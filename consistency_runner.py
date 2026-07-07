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
CONVERGENCE_FIELDS = [
    "heading_band_shade",
    "heading_band_hue",
    "palettes",
    "frame_present",
    "striping_present",
    "dividers_present",
    "caption_present",
    "source_present",
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


def parse_design_choices(source: str) -> dict:
    """Parse a `table.py` source string into the design choices the rules pin down.

    Heuristic (regex) parsing — it reads the choices the skill's flowchart makes
    deterministic, not the full semantics of the script.
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
    }


def parse_table_dir(run_dir: Path) -> dict:
    """Parse the table.py in a run dir into {status, choices, has_png}."""
    table_py = run_dir / "table.py"
    if not table_py.exists():
        return {"status": "missing", "choices": None, "has_png": (run_dir / "table.png").exists()}
    try:
        choices = parse_design_choices(table_py.read_text())
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
    """Make a design-choice value hashable/JSON-key-safe for counting."""
    if isinstance(value, list):
        return "|".join(value) if value else "(none)"
    return value


def _field_convergence(field: str, baseline_choices: dict | None, repeat_choices: list[dict | None]) -> dict:
    """Agreement stats for one field across the parsed with-skill repeats."""
    vals = [_value_signature(c[field]) for c in repeat_choices if c is not None]
    baseline_val = (
        _value_signature(baseline_choices[field]) if baseline_choices is not None else None
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
            f"  {field:22s} agree={c['agreement']:>5s}  "
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
