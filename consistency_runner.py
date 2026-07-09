#!/usr/bin/env python3
"""Consistency test harness for the great-tables skill.

Measures *convergence*: for ONE prompt, run it once with no skill (the
baseline) and N times with the skill active, then check how often the N
with-skill runs land on the same design choices. That agreement fraction is
the consistency metric.

Runs through run.py's core `run()` with its new `skill_variant` parameter:
  - baseline    -> skill_variant="none"     (no skill loaded)
  - with_skill  -> skill_variant=<--variant> ("prose" or "scripted")

Output layout under test-runs/:
    test-runs/<ts>_<prompt-slug>/
      baseline/            table.py · table.png · transcript.json
      with_skill/repeat_1/  repeat_2/  repeat_3/   (each: table.py/.png/transcript)
      contact_sheet.png     baseline + repeats side-by-side (PIL)
      consistency_report.json

Usage examples:
    python consistency_runner.py "Make a clean table of this data" data/gtcars.csv
    python consistency_runner.py "..." data/towny.csv --variant scripted --repeat 5
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

import anyio
from dotenv import load_dotenv
from nokap import Chrome
from PIL import Image, ImageDraw, ImageFont

from run import run as run_agent

ROOT = Path(__file__).parent.resolve()

# Fields the convergence metric is computed over, in report order. Each maps a
# parsed design choice to a hashable value; palettes is list-valued and gets a
# signature in _field_convergence().
#
# R5 (PP-29) widens the metric beyond styling: the trailing six fields score the
# structural / data choices the palette-name-only metric was blind to —
# grouping, stub, the visible column set + labels, number formatting, the
# data_color domains, and a best-effort hash of the frame the table renders.
CONVERGENCE_FIELDS = [
    "heading_band_shade",
    "heading_band_hue",
    "palettes",
    "frame_present",
    "striping_present",
    "dividers_present",
    "caption_present",
    "source_present",
    "grouping_present",
    "stub_present",
    "columns_signature",
    "fmt_signature",
    "domain_signature",
    "data_hash",
]

# Palette hexes lifted from references/palettes.md (§1 solids + washed tints,
# §2 neutrals). Used to label a heading-band color with its Dark-Academia hue
# family via nearest-neighbour in RGB. Neutrals collapse to "grey".
_FAMILY_HEXES: dict[str, list[str]] = {
    "navy": ["#22384F", "#EAF0F6"],
    "forest": ["#2F4A38", "#EAF1EC"],
    "oxblood": ["#5C2E2E", "#F5EBEB"],
    "espresso": ["#4A3A2C", "#F1EADD"],
    "ochre": ["#9A7B33", "#F5EFDC"],
    "tan": ["#8A7452", "#EFE7D6"],
    "grey": [
        "#F0F0F0", "#F6F6F6", "#E8E8E8", "#CCCCCC",
        "#BDBDBD", "#D0D0D0", "#808080", "#FFFFFF", "#000000",
    ],
}


# --------------------------------------------------------------------------- #
# small pure helpers
# --------------------------------------------------------------------------- #
def slugify(text: str, max_len: int = 40) -> str:
    """A filesystem-safe, hyphenated slug of `text` (lowercased, trimmed)."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:max_len].strip("-") or "prompt"


def _hex_to_rgb(hexstr: str) -> tuple[int, int, int] | None:
    """Parse a #rgb / #rrggbb string to an (r, g, b) tuple, else None."""
    if not hexstr:
        return None
    h = hexstr.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        return None
    try:
        return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]
    except ValueError:
        return None


def _relative_luminance(rgb: tuple[int, int, int]) -> float:
    """Perceptual luminance on 0..1 (Rec. 709 coefficients)."""
    r, g, b = rgb
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0


def _band_shade(hexstr: str) -> str:
    """Classify a band hex as 'light' or 'dark' by luminance."""
    rgb = _hex_to_rgb(hexstr)
    if rgb is None:
        return "unknown"
    return "dark" if _relative_luminance(rgb) < 0.5 else "light"


def _classify_hue(hexstr: str) -> str:
    """Nearest Dark-Academia hue family for a hex ('grey' for neutrals)."""
    rgb = _hex_to_rgb(hexstr)
    if rgb is None:
        return "unknown"
    best_family, best_dist = "unknown", float("inf")
    for family, hexes in _FAMILY_HEXES.items():
        for ref in hexes:
            rr = _hex_to_rgb(ref)
            if rr is None:
                continue
            dist = sum((a - b) ** 2 for a, b in zip(rgb, rr))
            if dist < best_dist:
                best_dist, best_family = dist, family
    return best_family


def _call_arg_blocks(source: str, func: str) -> list[str]:
    """Return the argument text of every `.<func>(...)` call in `source`.

    A simple balanced-paren scan, so nested calls / lists inside the args
    (e.g. `domain=[df[...].min(), ...]`) are handled. Parens inside string
    literals are not specially handled, which is fine for these scripts.
    """
    blocks: list[str] = []
    for m in re.finditer(rf"\.{re.escape(func)}\s*\(", source):
        open_idx = m.end() - 1
        depth = 0
        for j in range(open_idx, len(source)):
            c = source[j]
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    blocks.append(source[open_idx + 1 : j])
                    break
    return blocks


def _gt_constructor_blocks(source: str) -> list[str]:
    """Return the argument text of every top-level `GT(...)` constructor call.

    Distinct from `_call_arg_blocks` (which needs a leading dot): the GT
    constructor is called bare, e.g. `GT(df, groupname_col='Country')`. The
    negative lookbehind avoids matching identifiers ending in `GT` or `.GT`.
    """
    blocks: list[str] = []
    for m in re.finditer(r"(?<![\w.])GT\s*\(", source):
        open_idx = m.end() - 1
        depth = 0
        for j in range(open_idx, len(source)):
            c = source[j]
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    blocks.append(source[open_idx + 1 : j])
                    break
    return blocks


def _find_band_color(source: str) -> str | None:
    """Extract the heading-band background hex, if the script sets one.

    Prefers the column-labels band (Step-4's "heading band"); falls back to
    the title/subtitle heading band. Only explicit `tab_options(...)` hexes are
    detected (the mechanism the skill prescribes)."""
    for key in ("column_labels_background_color", "heading_background_color"):
        m = re.search(rf"{key}\s*=\s*['\"]([^'\"]+)['\"]", source)
        if m:
            return m.group(1)
    return None


def _extract_palettes(source: str) -> list[str]:
    """Palette name of each `data_color(...)` call (one per colored measure).

    A quoted string -> its name; a list literal -> 'custom'; no palette arg ->
    'default'. Returned sorted so ordering never breaks the agreement check.
    """
    palettes: list[str] = []
    for block in _call_arg_blocks(source, "data_color"):
        m = re.search(r"palette\s*=\s*(\[[^\]]*\]|['\"]([^'\"]+)['\"])", block)
        if not m:
            palettes.append("default")
        elif m.group(2):
            palettes.append(m.group(2))
        else:
            palettes.append("custom")
    return sorted(palettes)


def _vlines_active(source: str) -> bool:
    """True if any column-divider (vlines) style/width/color is set to non-none."""
    for m in re.finditer(
        r"(?:table_body|column_labels)_vlines_(?:style|width|color)\s*=\s*['\"]([^'\"]+)['\"]",
        source,
    ):
        if m.group(1).strip().lower() not in ("none", "hidden", ""):
            return True
    return False


# --------------------------------------------------------------------------- #
# R5 — expanded convergence signals (structure / data, not just style)
# --------------------------------------------------------------------------- #
def _columns_signature(source: str) -> str:
    """Canonical signature of the visible column set + labels (PP-19..24).

    Built from the *displayed* labels in `cols_label(...)` and the hidden
    columns in `cols_hide(...)`, so two runs that show the same columns under
    the same labels produce the same string regardless of call ordering. Both
    keyword (`open="Opening Price"`) and dict-unpacked
    (`**{'Closing Price': 'Closing Price'}`) label forms are handled, plus an
    optional `md(...)`/`html(...)` wrapper on the label value. Returns
    "(unknown)" when neither call is parseable.
    """
    tokens: list[str] = []
    for block in _call_arg_blocks(source, "cols_label"):
        # keyword form:  ident = "Label"   (label optionally wrapped in md()/html())
        for m in re.finditer(
            r"\b[A-Za-z_]\w*\s*=\s*(?:md|html)?\s*\(?\s*['\"]([^'\"]+)['\"]", block
        ):
            tokens.append("label:" + m.group(1))
        # dict form:  "key": "Label"
        for m in re.finditer(
            r"['\"][^'\"]+['\"]\s*:\s*(?:md|html)?\s*\(?\s*['\"]([^'\"]+)['\"]", block
        ):
            tokens.append("label:" + m.group(1))
    for block in _call_arg_blocks(source, "cols_hide"):
        for m in re.finditer(r"['\"]([^'\"]+)['\"]", block):
            tokens.append("hide:" + m.group(1))
    if not tokens:
        return "(unknown)"
    return "|".join(sorted(set(tokens)))


def _fmt_signature(source: str) -> str:
    """Sorted multiset of the `fmt_*` formatters applied (PP-14/15/16).

    Function-name multiset only (duplicates kept, so two `fmt_currency` calls
    read as two): captures currency-vs-plain and percent divergence. Column
    targets are intentionally not parsed — they are unreliable across the
    keyword/list/positional forms these scripts use. "(none)" when no formatter
    is applied.
    """
    names = re.findall(r"\.(fmt_[a-z_]+)\s*\(", source)
    if not names:
        return "(none)"
    return "|".join(sorted(names))


def _round_sig(x: float, sig: int = 2) -> str:
    """Format a float to `sig` significant figures with a compact exponent.

    e.g. -20 -> "-20", 4786714716 -> "4.8e9", 100 -> "1e2", 0.045 -> "0.045".
    The exponent is normalized (strip the sign's leading zeros: e+09 -> e9) so
    the same magnitude always renders the same string across runs.
    """
    if x == 0:
        return "0"
    s = f"{x:.{sig}g}"
    s = re.sub(
        r"e([+-]?)0*(\d)",
        lambda mm: "e" + ("-" if mm.group(1) == "-" else "") + mm.group(2),
        s,
    )
    return s


def _split_top_level(text: str, sep: str = ",") -> list[str]:
    """Split `text` on `sep`, ignoring separators nested in (), [] or {}."""
    parts: list[str] = []
    depth = 0
    cur: list[str] = []
    for ch in text:
        if ch in "([{":
            depth += 1
            cur.append(ch)
        elif ch in ")]}":
            depth -= 1
            cur.append(ch)
        elif ch == sep and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    parts.append("".join(cur))
    return [p for p in (p.strip() for p in parts) if p != ""]


def _fmt_domain_elem(text: str) -> str:
    """Normalize one `domain=[...]` element to a stable token.

    Numeric literal -> rounded to 2 sig figs; a `.min()`/`.max()` expression ->
    "min"/"max" (so two data-driven runs converge); anything else -> its
    whitespace-stripped source text.
    """
    t = text.strip()
    try:
        return _round_sig(float(t))
    except ValueError:
        low = t.lower()
        if ".min(" in low:
            return "min"
        if ".max(" in low:
            return "max"
        return re.sub(r"\s+", "", t)


def _domain_signature(source: str) -> str:
    """Canonical signature of every `data_color(domain=[...])` (PP-6/PP-7).

    One `[a,b]` group per data_color call (a call with no domain -> "(none)"),
    sorted and joined with ";", e.g. "[-11,11];[0,4.8e9]". A balanced-bracket
    scan is used because the list can contain `df['col'].min()` indexing. "(none)"
    when there are no data_color calls at all (matches the palettes "no color"
    convention).
    """
    sigs: list[str] = []
    for block in _call_arg_blocks(source, "data_color"):
        m = re.search(r"domain\s*=\s*\[", block)
        if not m:
            sigs.append("(none)")
            continue
        start = m.end() - 1  # index of the opening '['
        depth = 0
        inner: str | None = None
        for j in range(start, len(block)):
            ch = block[j]
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    inner = block[start + 1 : j]
                    break
        if inner is None:
            sigs.append("(none)")
            continue
        elems = _split_top_level(inner)
        sigs.append("[" + ",".join(_fmt_domain_elem(e) for e in elems) + "]")
    if not sigs:
        return "(none)"
    return ";".join(sorted(sigs))


# Subprocess body for the best-effort data-frame hash (PP-18/PP-29). Kept as a
# `python -c` payload so it runs in a *fresh* interpreter we can hard-timeout and
# kill — it never touches the reporting process. Reads the table.py path from
# argv[1], stubs the harness Chrome shim + `gtsave`, execs the script with its
# stdout swallowed, then hashes the frame the table renders. Any failure prints
# an empty hash, which the parent maps to None.
_DATA_HASH_RUNNER = r'''
import sys, types, io, hashlib, contextlib


def _is_frame(obj):
    mod = type(obj).__module__ or ""
    return type(obj).__name__ == "DataFrame" and (
        mod.startswith("pandas") or mod.startswith("polars")
    )


def _size(df):
    try:
        s = getattr(df, "shape", None)
        if s and len(s) == 2:
            return int(s[0]) * int(s[1])
    except Exception:
        pass
    return -1


def _canon_and_hash(df):
    mod = type(df).__module__ or ""
    if mod.startswith("pandas"):
        d = df
        try:
            d = d.round(6)          # stabilize float noise
        except Exception:
            pass
        try:
            d = d.reindex(sorted(d.columns, key=str), axis=1)  # sort columns
        except Exception:
            pass
        try:
            payload = d.to_csv(index=False)
        except Exception:
            payload = repr(d)
    elif mod.startswith("polars"):
        try:
            payload = df.select(sorted(df.columns)).write_csv()
        except Exception:
            payload = repr(df)
    else:
        payload = repr(df)
    return hashlib.sha256(payload.encode("utf-8", "replace")).hexdigest()[:12]


def main():
    path = sys.argv[1]
    with open(path) as fh:
        src = fh.read()

    # Neutralize the harness Chrome shim / venv sidecar hook so importing them
    # never launches a browser.
    for name in ("gtskill_chrome", "_gtskill_sidecar"):
        sys.modules[name] = types.ModuleType(name)

    # Capture the frame(s) handed to GT(...) (the rendered data), and make
    # gtsave a no-op so nothing tries to render.
    captured = []
    try:
        import great_tables as _gt
        _orig_init = _gt.GT.__init__

        def _patched_init(self, data=None, *a, **k):
            try:
                if _is_frame(data):
                    captured.append(data)
            except Exception:
                pass
            return _orig_init(self, data, *a, **k)

        _gt.GT.__init__ = _patched_init
        _gt.GT.gtsave = lambda *a, **k: None
    except Exception:
        pass

    ns = {"__name__": "__main__", "__file__": path}
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(compile(src, path, "exec"), ns)

    # Prefer the frame actually rendered (handed to GT); fall back to the
    # largest DataFrame in the namespace. The raw input CSV is often the largest
    # object, so a pure "largest" heuristic would hash the unchanged input and
    # miss the divergent computations R5 is meant to catch (PP-18).
    candidates = list(captured)
    if not candidates:
        candidates = [v for v in ns.values() if _is_frame(v)]
    if not candidates:
        return None
    best = max(candidates, key=_size)
    return _canon_and_hash(best)


try:
    _h = main()
except Exception:
    _h = None
sys.stdout.write("DATAHASH:%s\n" % (_h if _h else ""))
'''


def _compute_data_hash(run_dir: Path, timeout: float = 30.0) -> str | None:
    """Best-effort short hex hash of the frame `run_dir/table.py` renders.

    Execs table.py in a hard-timed-out **subprocess** (fresh interpreter, cwd =
    run_dir so relative data paths resolve) with `gtsave` stubbed to a no-op and
    the Chrome shim neutralized, then hashes the canonicalized frame. Returns
    None on ANY failure/timeout — the field is then simply skipped in the
    convergence scoring, exactly like a missing choice. This never hangs (the
    subprocess is killed on timeout) and never raises to the caller.

    Limitation: scripts that import run-dir-local helper modules that are not
    present, do network I/O, or otherwise fail to exec cleanly will yield None.
    That is intentional — a None just means "not comparable for this run".
    """
    table_py = run_dir / "table.py"
    if not table_py.exists():
        return None
    try:
        proc = subprocess.run(
            [sys.executable, "-c", _DATA_HASH_RUNNER, str(table_py)],
            cwd=str(run_dir),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except Exception:  # TimeoutExpired (subprocess is killed) or spawn failure
        return None
    for line in proc.stdout.splitlines():
        if line.startswith("DATAHASH:"):
            val = line[len("DATAHASH:") :].strip()
            return val or None
    return None


def parse_design_choices(source: str, run_dir: Path | None = None) -> dict:
    """Parse a `table.py` source string into the design choices the rules pin down.

    Heuristic (regex) parsing — it reads the choices the skill's flowchart makes
    deterministic, not the full semantics of the script. The structural R5
    fields (grouping/stub/columns/fmt/domain) are pure source regex; `data_hash`
    needs `run_dir` (to exec the script against its data) and is None otherwise.
    """
    band_hex = _find_band_color(source)
    frame_present = bool(
        re.search(r"opt_table_outline\s*\(", source)
        or re.search(r"table_border_(?:left|right)_(?:style|width|color)\s*=", source)
        or re.search(r"\b(?:frame|finalize)\s*\(", source)
    )
    striping_present = bool(
        re.search(r"opt_row_striping\s*\(", source)
        or re.search(r"row_striping_background_color\s*=", source)
        or re.search(r"row_striping_include_table_body\s*=\s*True", source)
    )
    caption_present = any(
        re.search(r"subtitle\s*=", block) for block in _call_arg_blocks(source, "tab_header")
    )
    title_present = any(
        re.search(r"\btitle\s*=", block) for block in _call_arg_blocks(source, "tab_header")
    )
    source_present = bool(re.search(r"\.tab_source_note\s*\(", source))

    palettes = _extract_palettes(source)

    # R5: grouping / stub are GT(...) constructor kwargs (PP-1 / PP-13).
    gt_blocks = _gt_constructor_blocks(source)
    grouping_present = any(re.search(r"\bgroupname_col\s*=", b) for b in gt_blocks)
    stub_present = any(re.search(r"\browname_col\s*=", b) for b in gt_blocks)

    # R5: best-effort computed-data hash (PP-18/PP-29); None-safe, off the
    # critical path — a failure here must never break the report.
    data_hash: str | None = None
    if run_dir is not None:
        try:
            data_hash = _compute_data_hash(run_dir)
        except Exception:
            data_hash = None

    return {
        "heading_band_shade": _band_shade(band_hex) if band_hex else "none",
        "heading_band_hue": _classify_hue(band_hex) if band_hex else "none",
        "heading_band_hex": band_hex,
        "palettes": palettes,
        "n_color_measures": len(palettes),
        "frame_present": frame_present,
        "striping_present": striping_present,
        "dividers_present": _vlines_active(source),
        "caption_present": caption_present,
        "title_present": title_present,
        "source_present": source_present,
        # R5 additions (PP-29):
        "grouping_present": grouping_present,
        "stub_present": stub_present,
        "columns_signature": _columns_signature(source),
        "fmt_signature": _fmt_signature(source),
        "domain_signature": _domain_signature(source),
        "data_hash": data_hash,
    }


def parse_table_dir(run_dir: Path) -> dict:
    """Parse the table.py in a run dir into {status, choices, has_png}."""
    table_py = run_dir / "table.py"
    if not table_py.exists():
        return {"status": "missing", "choices": None, "has_png": (run_dir / "table.png").exists()}
    try:
        choices = parse_design_choices(table_py.read_text(), run_dir=run_dir)
    except Exception as e:  # never let a bad script kill the whole report
        return {"status": "error", "error": str(e), "choices": None,
                "has_png": (run_dir / "table.png").exists()}
    return {"status": "parsed", "choices": choices, "has_png": (run_dir / "table.png").exists()}


# --------------------------------------------------------------------------- #
# contact sheet
# --------------------------------------------------------------------------- #
def _label_font(size: int = 16):
    """A truetype label font if one is findable, else PIL's bitmap default."""
    for candidate in (
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _load_panel(png_path: Path, width: int) -> Image.Image:
    """Load table.png scaled to `width`, or a labelled placeholder if missing/bad."""
    try:
        img = Image.open(png_path).convert("RGB")
        scale = width / img.width
        return img.resize((width, max(1, round(img.height * scale))), Image.Resampling.LANCZOS)
    except Exception:
        ph = Image.new("RGB", (width, round(width * 0.6)), "#eeeeee")
        d = ImageDraw.Draw(ph)
        msg = "(no table.png)"
        font = _label_font(16)
        tb = d.textbbox((0, 0), msg, font=font)
        d.text(
            ((width - (tb[2] - tb[0])) / 2, (ph.height - (tb[3] - tb[1])) / 2),
            msg, fill="#999999", font=font,
        )
        return ph


def build_contact_sheet(
    panels: list[tuple[str, Path]],
    out_path: Path,
    *,
    panel_width: int = 380,
    pad: int = 12,
    label_h: int = 26,
    bg: str = "white",
) -> Path:
    """Compose labelled panels (label, png_path) side-by-side into one PNG.

    Missing or unreadable panels render as a grey "(no table.png)" placeholder,
    so the sheet is always produced.
    """
    if not panels:
        Image.new("RGB", (panel_width, panel_width), bg).save(out_path)
        return out_path

    loaded = [(label, _load_panel(p, panel_width)) for label, p in panels]
    max_h = max(im.height for _, im in loaded)
    total_w = pad + sum(im.width + pad for _, im in loaded)
    total_h = pad + label_h + max_h + pad

    sheet = Image.new("RGB", (total_w, total_h), bg)
    draw = ImageDraw.Draw(sheet)
    font = _label_font(16)

    x = pad
    for label, im in loaded:
        draw.text((x, pad), label, fill="black", font=font)
        top = pad + label_h
        sheet.paste(im, (x, top))
        draw.rectangle([x, top, x + im.width - 1, top + im.height - 1], outline="#cccccc")
        x += im.width + pad

    sheet.save(out_path)
    return out_path


# --------------------------------------------------------------------------- #
# convergence report
# --------------------------------------------------------------------------- #
def _value_signature(value):
    """Make a design-choice value hashable/JSON-key-safe for counting.

    Lists (e.g. palettes) collapse to a joined signature; str / bool / None
    (the R5 fields are str/bool, data_hash is str|None) pass through unchanged.
    """
    if isinstance(value, list):
        return "|".join(value) if value else "(none)"
    return value


def _field_convergence(field: str, baseline_choices: dict | None, repeat_choices: list[dict | None]) -> dict:
    """Agreement stats for one field across the parsed with-skill repeats.

    Repeats whose value for this field is None are skipped (not counted as an
    agreeing "None"): this matters for `data_hash`, which is None whenever the
    frame could not be computed — only runs where it *was* computable are scored.
    Existing fields never carry None values, so their behavior is unchanged.
    """
    vals = [
        _value_signature(c[field])
        for c in repeat_choices
        if c is not None and c.get(field) is not None
    ]
    baseline_val = (
        _value_signature(baseline_choices.get(field)) if baseline_choices is not None else None
    )
    n = len(vals)
    if n == 0:
        return {"consensus": None, "agreement": "0/0", "ratio": None,
                "unanimous": False, "distribution": {}, "baseline": baseline_val}
    counts = Counter(vals)
    top_val, top_n = counts.most_common(1)[0]
    return {
        "consensus": top_val,
        "agreement": f"{top_n}/{n}",
        "ratio": round(top_n / n, 3),
        "unanimous": top_n == n,
        "distribution": {str(k): v for k, v in counts.items()},
        "baseline": baseline_val,
    }


def build_report(
    meta: dict,
    baseline: dict,
    with_skill: list[dict],
) -> dict:
    """Assemble consistency_report.json from parsed baseline + repeat results.

    `baseline` and each `with_skill` entry are parse_table_dir() dicts extended
    with at least {"repeat"/"run_dir"}.
    """
    baseline_choices = baseline.get("choices")
    repeat_choices = [w.get("choices") for w in with_skill]

    convergence = {
        field: _field_convergence(field, baseline_choices, repeat_choices)
        for field in CONVERGENCE_FIELDS
    }
    ratios = [c["ratio"] for c in convergence.values() if c["ratio"] is not None]
    overall = round(sum(ratios) / len(ratios), 3) if ratios else None

    return {
        **meta,
        "overall_convergence": overall,
        "convergence": convergence,
        "baseline": baseline,
        "with_skill": with_skill,
    }


# --------------------------------------------------------------------------- #
# run orchestration
# --------------------------------------------------------------------------- #
async def run_consistency(
    prompt: str,
    data_path: Path,
    out_dir: Path,
    repeat: int,
    variant: str,
    chrome_ws: str,
) -> tuple[Path, list[Path]]:
    """Run 1x baseline (none) + N x with-skill (variant), sharing one Chrome.

    Returns (baseline_dir, [repeat_dir, ...]). Individual run failures are
    caught and logged so the contact sheet / report can still be built.
    """
    async def _one(run_dir: Path, skill_variant: str, label: str) -> None:
        run_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n{'=' * 60}\n{label}  (skill_variant={skill_variant})\n{'=' * 60}")
        print(f"  run_dir: {run_dir}\n")
        start = time.time()
        try:
            await run_agent(prompt, data_path, run_dir, chrome_ws, skill_variant=skill_variant)
            print(f"  done in {time.time() - start:.1f}s")
        except Exception as e:  # keep going; a failed run becomes a missing panel
            print(f"  FAILED after {time.time() - start:.1f}s: {e}", file=sys.stderr)

    baseline_dir = out_dir / "baseline"
    await _one(baseline_dir, "none", "baseline")

    repeat_dirs: list[Path] = []
    for r in range(1, repeat + 1):
        d = out_dir / "with_skill" / f"repeat_{r}"
        await _one(d, variant, f"with_skill / repeat {r}/{repeat}")
        repeat_dirs.append(d)

    return baseline_dir, repeat_dirs


def _finalize_outputs(
    out_dir: Path, baseline_dir: Path, repeat_dirs: list[Path], meta: dict
) -> dict:
    """Parse runs, write contact_sheet.png + consistency_report.json, return report."""
    panels: list[tuple[str, Path]] = [("baseline", baseline_dir / "table.png")]
    panels += [(f"repeat {i}", d / "table.png") for i, d in enumerate(repeat_dirs, 1)]
    build_contact_sheet(panels, out_dir / "contact_sheet.png")

    baseline = {"run_dir": str(baseline_dir), **parse_table_dir(baseline_dir)}
    with_skill = [
        {"repeat": i, "run_dir": str(d), **parse_table_dir(d)}
        for i, d in enumerate(repeat_dirs, 1)
    ]
    report = build_report(meta, baseline, with_skill)
    (out_dir / "consistency_report.json").write_text(json.dumps(report, indent=2, default=str))
    return report


def _print_summary(report: dict, out_dir: Path) -> None:
    print(f"\n{'=' * 60}\nCONSISTENCY SUMMARY\n{'=' * 60}")
    print(f"overall convergence: {report['overall_convergence']}")
    for field, c in report["convergence"].items():
        print(
            f"  {field:24s} agree={c['agreement']:>5s}  "
            f"consensus={str(c['consensus'])!s:14.14}  baseline={str(c['baseline'])!s:.20}"
        )
    print(f"\ncontact sheet:  {out_dir / 'contact_sheet.png'}")
    print(f"report:         {out_dir / 'consistency_report.json'}")


def main() -> int:
    load_dotenv(ROOT / ".env")

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("error: ANTHROPIC_API_KEY is not set (put it in .env)", file=sys.stderr)
        return 2

    parser = argparse.ArgumentParser(
        description="Measure design-choice convergence of the great-tables skill "
        "across repeated runs of one prompt.",
    )
    parser.add_argument("prompt", help="Describe the table you want.")
    parser.add_argument("data", help="Path to the data file (e.g. data/gtcars.csv).")
    parser.add_argument(
        "--variant",
        choices=["prose", "scripted"],
        default="prose",
        help="Which with-skill variant to repeat (default: prose).",
    )
    parser.add_argument(
        "--repeat",
        type=int,
        default=3,
        help="Number of with-skill repeats, N (default: 3). The baseline always runs once.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model override (sets GTSKILL_AGENT_MODEL env var).",
    )
    args = parser.parse_args()

    if args.repeat < 1:
        print("error: --repeat must be >= 1", file=sys.stderr)
        return 2

    data_path = Path(args.data).expanduser().resolve()
    if not data_path.is_file():
        print(f"error: data file not found: {data_path}", file=sys.stderr)
        return 2

    if args.model:
        os.environ["GTSKILL_AGENT_MODEL"] = args.model

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = ROOT / "test-runs" / f"{timestamp}_{slugify(args.prompt)}"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"out dir: {out_dir}")
    print(f"data:    {data_path}")
    print(f"variant: {args.variant}  (baseline=none + {args.repeat}x {args.variant})")
    print(f"prompt:  {args.prompt}\n")

    # One headless Chrome for the whole run; every baseline/repeat attaches to
    # it over CDP (same single-sidecar pattern as run.py / test_runner.py).
    chrome_profile = out_dir / ".chrome-profile"
    chrome_profile.mkdir(exist_ok=True)
    chrome = Chrome(extra_args=[f"--user-data-dir={chrome_profile}"])
    print(f"chrome:  {chrome.ws_url}\n")

    try:
        baseline_dir, repeat_dirs = anyio.run(
            run_consistency, args.prompt, data_path, out_dir, args.repeat, args.variant, chrome.ws_url
        )
    finally:
        chrome.close()
        shutil.rmtree(chrome_profile, ignore_errors=True)

    meta = {
        "timestamp": timestamp,
        "prompt": args.prompt,
        "data": str(data_path),
        "variant": args.variant,
        "repeat": args.repeat,
        "model": args.model,
    }
    report = _finalize_outputs(out_dir, baseline_dir, repeat_dirs, meta)
    _print_summary(report, out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
