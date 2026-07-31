#!/usr/bin/env python3
"""Convergence scoring + contact sheet — the metric core of the old runner.

Every design-choice parser, the convergence scorer, and the contact-sheet
compositor were moved here verbatim from ``consistency_runner.py`` (only the
orchestration — the Chrome/SDK-driving ``run_consistency`` / ``main`` — was left
behind; the new ``runner.orchestrate`` drives runs and calls these primitives).
The parsing heuristics ARE the contract the convergence report depends on, so
nothing about their behavior changed in the move.

For ONE prompt, the metric measures *convergence*: run it N times with the skill
active and check how often the N runs land on the same design choices. That
agreement fraction (averaged over the fields in ``CONVERGENCE_FIELDS``) is the
consistency metric. A baseline (no-skill) run is parsed too, for contrast.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

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
    "color_signature",
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


def _bare_call_blocks(source: str, func: str) -> list[str]:
    """Return the argument text of every bare `func(...)` call in `source`.

    Like `_gt_constructor_blocks` but for an arbitrary top-level function name —
    used to recognize the runtime helper calls the scripted skill PREFERS
    (`heatmap(...)`, `band(...)`, `stripe(...)`, `stub_tint(...)`) rather than
    the literal `.data_color(...)` / `tab_options(...)` equivalents. An optional
    single module qualifier is allowed so both the documented bare import
    (`heatmap(`) and an attribute call (`gtc.heatmap(` / `gt_consistency.heatmap(`)
    are caught — matching `gt_check.py`'s leniency so the two enforcement layers
    agree. The leading `(?<![\\w.])` still means `heatmap` never matches inside
    `add_heatmap` (a longer identifier), and the qualifier is a single level so a
    chained `df.x.stripe(` is not caught.
    """
    blocks: list[str] = []
    for m in re.finditer(rf"(?<![\w.])(?:[A-Za-z_]\w*\.)?{re.escape(func)}\s*\(", source):
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


def _unquote(text: str | None) -> str | None:
    """Strip one layer of surrounding quotes from a token, else return as-is."""
    if text is None:
        return None
    t = text.strip()
    if len(t) >= 2 and t[0] in "'\"" and t[-1] == t[0]:
        return t[1:-1]
    return t


def _kwarg_value(block: str, name: str) -> str | None:
    """Raw source text of the top-level `name=<value>` kwarg in a call's args.

    Splits on top-level commas (so `columns=['a','b']` / `domain=[x, y]` stay
    intact) and returns the value text of the first arg that *starts* with
    `name=`. None if the kwarg is absent. Whitespace/newlines inside the value
    are preserved for the caller to normalize.
    """
    for part in _split_top_level(block):
        m = re.match(rf"{re.escape(name)}\s*=\s*(.+)", part, re.S)
        if m:
            return m.group(1).strip()
    return None


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


def _palette_of_block(block: str) -> str:
    """Palette name for one `data_color(...)` arg block.

    A quoted string -> its name; a list literal -> 'custom'; no palette arg ->
    'default'. Shared by `_extract_palettes` and `_color_signature`.
    """
    m = re.search(r"palette\s*=\s*(\[[^\]]*\]|['\"]([^'\"]+)['\"])", block)
    if not m:
        return "default"
    if m.group(2):
        return m.group(2)
    return "custom"


def _extract_palettes(source: str) -> list[str]:
    """Palette name of each colored measure (one per `data_color`/`heatmap`).

    Literal `.data_color(...)`: a quoted `palette=` -> its name, a list literal
    -> 'custom', no palette -> 'default' (unchanged behavior). The runtime
    helper `heatmap(gt, columns, *, kind, hue, ...)` the scripted skill prefers
    contributes its `hue=` family as the palette (else 'default'), so a
    helper-based run scores palettes the SAME as its literal equivalent instead
    of reading as no-color. Returned sorted so ordering never breaks agreement.
    """
    palettes: list[str] = []
    for block in _call_arg_blocks(source, "data_color"):
        palettes.append(_palette_of_block(block))
    for block in _bare_call_blocks(source, "heatmap"):
        hue = _unquote(_kwarg_value(block, "hue"))
        palettes.append(hue or "default")
    return sorted(palettes)


def _vlines_active(source: str) -> bool:
    """True if a column-group divider is present, by EITHER accepted mechanism.

    A table-wide `*_vlines_*` `tab_options` kwarg is one way; a per-boundary
    `tab_style(style=style.borders(sides="left"/"right", ...), ...)` call is
    the other (what `towny_growth_trends.py` actually uses for its spanner
    dividers) — both are equally valid per the outcome-only scoring rule, so
    either must count.
    """
    for m in re.finditer(
        r"(?:table_body|column_labels)_vlines_(?:style|width|color)\s*=\s*['\"]([^'\"]+)['\"]",
        source,
    ):
        if m.group(1).strip().lower() not in ("none", "hidden", ""):
            return True
    for block in _call_arg_blocks(source, "tab_style"):
        style_val = _kwarg_value(block, "style")
        if style_val is None:
            positionals = [
                p for p in _split_top_level(block) if not re.match(r"[A-Za-z_]\w*\s*=", p)
            ]
            style_val = positionals[0] if positionals else None
        if style_val is None:
            continue
        bm = re.search(r"style\s*\.\s*borders\s*\(", style_val)
        if not bm:
            continue
        open_idx = bm.end() - 1
        depth = 0
        borders_block = None
        for j in range(open_idx, len(style_val)):
            c = style_val[j]
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    borders_block = style_val[open_idx + 1 : j]
                    break
        if borders_block is None:
            continue
        sides_val = _kwarg_value(borders_block, "sides")
        if sides_val is None:
            positionals = [
                p for p in _split_top_level(borders_block) if not re.match(r"[A-Za-z_]\w*\s*=", p)
            ]
            sides_val = positionals[0] if positionals else None
        # Only an actual "left"/"right" token counts — a purely horizontal
        # `sides=["top", "bottom"]` is a row rule, not a column divider, and
        # must not be misread as one just because it's a bracketed list.
        if sides_val and re.search(r"['\"](?:left|right)['\"]", sides_val):
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
        # The SOURCE key is retained alongside the display label so that
        # `revenue="Value"` and `profit="Value"` no longer collide as a bare
        # `label:Value` and falsely converge (they differ on the source column).
        for m in re.finditer(
            r"\b([A-Za-z_]\w*)\s*=\s*(?:md|html)?\s*\(?\s*['\"]([^'\"]+)['\"]", block
        ):
            tokens.append(f"label:{m.group(1)}={m.group(2)}")
        # dict form:  "key": "Label"
        for m in re.finditer(
            r"['\"]([^'\"]+)['\"]\s*:\s*(?:md|html)?\s*\(?\s*['\"]([^'\"]+)['\"]", block
        ):
            tokens.append(f"label:{m.group(1)}={m.group(2)}")
    for block in _call_arg_blocks(source, "cols_hide"):
        for m in re.finditer(r"['\"]([^'\"]+)['\"]", block):
            tokens.append("hide:" + m.group(1))
    if not tokens:
        return "(unknown)"
    return "|".join(sorted(set(tokens)))


# Formatter kwargs that change the RENDERED value (so they belong in the
# signature). Column targets are deliberately excluded — they are unreliable
# across the keyword/list/positional forms these scripts use.
_FMT_KWARGS = (
    "accounting",
    "compact",
    "currency",
    "decimals",
    "force_sign",
    "n_sigfig",
    "pattern",
    "scale_by",
    "scale_values",
    "suffixing",
)


def _fmt_calls(source: str) -> list[tuple[str, str]]:
    """Every `.fmt_*(...)` call as (name, arg-block), via a balanced-paren scan."""
    out: list[tuple[str, str]] = []
    for m in re.finditer(r"\.(fmt_[a-z_]+)\s*\(", source):
        name = m.group(1)
        open_idx = m.end() - 1
        depth = 0
        for j in range(open_idx, len(source)):
            c = source[j]
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    out.append((name, source[open_idx + 1 : j]))
                    break
    return out


def _fmt_signature(source: str) -> str:
    """Sorted multiset of the `fmt_*` formatters applied, WITH their kwargs.

    Each call becomes `fmt_number(decimals=0)` / `fmt_percent(scale_values=False)`
    — the value-affecting kwargs in `_FMT_KWARGS` are captured and sorted so that
    `fmt_number(decimals=0)` != `decimals=2` and a non-default `scale_values` no
    longer collapses onto the default. Duplicates kept (two `fmt_currency` read
    as two). "(none)" when no formatter is applied.
    """
    tokens: list[str] = []
    for name, block in _fmt_calls(source):
        kvs: list[str] = []
        for kw in _FMT_KWARGS:
            v = _kwarg_value(block, kw)
            if v is not None:
                kvs.append(f"{kw}=" + re.sub(r"\s+", "", v))
        tokens.append(name + ("(" + ",".join(sorted(kvs)) + ")" if kvs else ""))
    if not tokens:
        return "(none)"
    return "|".join(sorted(tokens))


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


def _parse_domain_value(val: str | None, default: str) -> str:
    """Normalize a `domain=` value to a stable token.

    An inline list `[a, b]` -> the canonical `[a,b]` group (each element via
    `_fmt_domain_elem`). A NON-list expression (a variable, e.g.
    `domain=domain`) -> `var:<expr>` so a variable domain is no longer
    indistinguishable from "no explicit domain". `val is None` (no `domain=` at
    all) -> the caller's `default` ("(none)" for data_color, "computed" for
    heatmap, which auto-derives its domain from the data).
    """
    if val is None:
        return default
    v = val.strip()
    if v.startswith("["):
        depth = 0
        inner: str | None = None
        for j, ch in enumerate(v):
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    inner = v[1:j]
                    break
        if inner is None:
            return default
        elems = _split_top_level(inner)
        return "[" + ",".join(_fmt_domain_elem(e) for e in elems) + "]"
    return "var:" + re.sub(r"\s+", "", v)


def _domain_signature(source: str) -> str:
    """Canonical signature of every color domain (PP-6/PP-7).

    One token per colored measure — from a literal `data_color(domain=...)` OR a
    runtime `heatmap(..., domain=...)` — sorted and joined with ";", e.g.
    "[-11,11];[0,4.8e9]". An inline list yields its `[a,b]` group; a variable
    domain yields `var:<expr>` (fix 3); a `data_color` with no domain yields
    "(none)" and a `heatmap` with no domain yields "computed" (it derives the
    domain from the data). "(none)" when there is no coloring at all (matches
    the palettes "no color" convention).
    """
    sigs: list[str] = []
    for block in _call_arg_blocks(source, "data_color"):
        sigs.append(_parse_domain_value(_kwarg_value(block, "domain"), "(none)"))
    for block in _bare_call_blocks(source, "heatmap"):
        sigs.append(_parse_domain_value(_kwarg_value(block, "domain"), "computed"))
    if not sigs:
        return "(none)"
    return ";".join(sorted(sigs))


def _columns_token(value_text: str | None) -> str:
    """Normalize a `columns=` value (or positional) to a stable token.

    Any quoted column names are collected and sorted (`['b','a']` -> "a,b"); a
    bare expression (e.g. a `cs.*` selector) collapses to its whitespace-free
    text. "(cols?)" when nothing is parseable.
    """
    if value_text is None:
        return "(cols?)"
    quoted = re.findall(r"['\"]([^'\"]+)['\"]", value_text)
    if quoted:
        return ",".join(sorted(quoted))
    stripped = re.sub(r"\s+", "", value_text)
    return stripped or "(cols?)"


def _heatmap_columns_raw(block: str) -> str | None:
    """Raw (untokenized) `columns` value text for a `heatmap(gt, columns, ...)`
    call — the 2nd positional arg or a `columns=` kwarg. Shared by
    `_heatmap_columns` (tokenized, for `_color_signature`) and
    `_color_mechanics` (var-map-resolved, so `heatmap(gt, change_cols, ...)`
    resolves to real column names instead of the literal identifier).
    """
    val = _kwarg_value(block, "columns")
    if val is None:
        positionals = [
            p for p in _split_top_level(block) if not re.match(r"[A-Za-z_]\w*\s*=", p)
        ]
        if len(positionals) >= 2:  # positionals[0] is the gt object
            val = positionals[1]
    return val


def _heatmap_columns(block: str) -> str:
    """Colored-column token for a `heatmap(gt, columns, ...)` call."""
    return _columns_token(_heatmap_columns_raw(block))


def _color_signature(source: str) -> str:
    """Canonical signature pairing each colored measure's TARGET columns with its
    palette/hue (PP-6..8).

    Coloring `sales` vs `profit` with the same palette + domain otherwise
    converges (palettes/domain are column-blind). Each `data_color(...)` becomes
    `<cols>::<palette>` and each runtime `heatmap(gt, cols, hue=...)` becomes
    `<cols>::<hue>`, so a different colored target no longer reads as agreement.
    "(none)" when there is no coloring at all.
    """
    tokens: list[str] = []
    for block in _call_arg_blocks(source, "data_color"):
        cols = _columns_token(_kwarg_value(block, "columns"))
        tokens.append(f"{cols}::{_palette_of_block(block)}")
    for block in _bare_call_blocks(source, "heatmap"):
        hue = _unquote(_kwarg_value(block, "hue")) or "default"
        tokens.append(f"{_heatmap_columns(block)}::{hue}")
    if not tokens:
        return "(none)"
    return ";".join(sorted(tokens))


def _find_band_helper(source: str) -> tuple[str, str] | None:
    """(shade, hue) of a runtime `band(gt, *, shade, hue)` heading-band call.

    None when there is no `band(...)` call. Lets a helper-based run score the
    heading band the SAME as the literal `column_labels_background_color=`.
    """
    blocks = _bare_call_blocks(source, "band")
    if not blocks:
        return None
    b = blocks[0]
    shade = _unquote(_kwarg_value(b, "shade")) or "unknown"
    hue = _unquote(_kwarg_value(b, "hue")) or "unknown"
    return shade, hue


def _find_stub_tint_hue(source: str) -> str | None:
    """`hue` of a runtime `stub_tint(gt, *, hue)` call, else None."""
    blocks = _bare_call_blocks(source, "stub_tint")
    if not blocks:
        return None
    return _unquote(_kwarg_value(blocks[0], "hue")) or "unknown"


def _constructor_col_present(gt_blocks: list[str], kw: str) -> bool:
    """True if any GT(...) block sets `kw=<an actual column>` (not None).

    `groupname_col=None` / `rowname_col=None` — the explicit default — must count
    as ABSENT: a stub/group is only present when a real column value is given
    (a quoted name or a variable holding one).
    """
    for b in gt_blocks:
        m = re.search(rf"\b{re.escape(kw)}\s*=\s*([^\s,)]+)", b)
        if m:
            val = m.group(1).strip()
            if val and val != "None":
                return True
    return False


# Subprocess body for the best-effort data-frame hash (PP-18/PP-29). Kept as a
# `python -c` payload so it runs in a *fresh* interpreter we can hard-timeout and
# kill — it never touches the reporting process. Reads the table.py path from
# argv[1], stubs the harness Chrome shim + `gtsave`, execs the script with its
# stdout swallowed, then hashes the frame the table renders. Any failure prints
# an empty hash, which the parent maps to None.
_DATA_HASH_RUNNER = r'''
import sys, types, io, hashlib, contextlib

# Columns hidden via a parsed cols_hide(...) in the source (argv[2:]). Dropped
# before hashing so "full frame then hide" and "preselect only the visible
# columns" hash identically — the hash reflects the VISIBLE table.
HIDDEN = list(sys.argv[2:])


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
        try:                        # exclude cols_hide(...) columns
            drop = [c for c in HIDDEN if c in d.columns]
            if drop:
                d = d.drop(columns=drop)
        except Exception:
            pass
        # NB: columns are intentionally NOT sorted — the rendered column order is
        # preserved so column-order drift shows up as a differing hash instead of
        # being normalized away into false convergence.
        try:
            payload = d.to_csv(index=False)
        except Exception:
            payload = repr(d)
    elif mod.startswith("polars"):
        try:
            keep = [c for c in df.columns if c not in HIDDEN]  # preserve order
            payload = df.select(keep).write_csv()
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


def _compute_data_hash(
    run_dir: Path, hidden_cols: list[str] | None = None, timeout: float = 30.0
) -> str | None:
    """Best-effort short hex hash of the frame `run_dir/table.py` renders.

    Execs table.py in a hard-timed-out **subprocess** (fresh interpreter, cwd =
    run_dir so relative data paths resolve) with `gtsave` stubbed to a no-op and
    the Chrome shim neutralized, then hashes the canonicalized frame. Columns
    named in `hidden_cols` (parsed from `cols_hide(...)`) are passed to the
    subprocess and dropped before hashing so the hash reflects the VISIBLE table.
    Returns None on ANY failure/timeout — the field is then simply skipped in the
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
            [sys.executable, "-c", _DATA_HASH_RUNNER, str(table_py), *(hidden_cols or [])],
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


# --------------------------------------------------------------------------- #
# Comparator Tier-1 additions (09-ground-truth-comparator.md §6) — new
# source-parsed fields the convergence report never needed but the ground-
# truth comparator's check functions do: spanner presence, data_color
# mechanics beyond the palette name, render params, the actual text of
# title/subtitle/caption/source (not just presence booleans), bold/hero
# detection, summary-row presence, body hairlines, and a per-column fmt map.
# --------------------------------------------------------------------------- #
_DQ_STRING = re.compile(r'"((?:[^"\\]|\\.)*)"', re.S)
_SQ_STRING = re.compile(r"'((?:[^'\\]|\\.)*)'", re.S)


def _extract_text_literal(value_text: str) -> str | None:
    """Best-effort literal text of a kwarg value: unwrap one `html(...)`/`md(...)`
    call, then concatenate every quoted string segment found inside (Python's
    implicit adjacent-string-literal concatenation, e.g. a subtitle split
    across two lines). None when no quoted string is present (e.g. a bare
    variable reference) — text is never fabricated from something that isn't
    a string literal in the source.

    Each segment is matched by ITS OWN quote character (`"..."` or `'...'`),
    not `['"]` interchangeably — free-text titles routinely contain an
    apostrophe (`"Ontario's Fastest-Growing Towns"`), and a quote-agnostic
    match would misread that apostrophe as the string's closing quote.

    An f-string segment with an unresolved `{...}` interpolation (e.g.
    `f"Sales for {year}"`) makes the WHOLE value return None rather than the
    literal template text — `{year}` is never what actually renders, and
    fabricating "Sales for {year}" as though it were the real title would be
    worse than admitting the text isn't known statically.
    """
    v = value_text.strip()
    m = re.match(r"^(?:html|md)\s*\(\s*(.*)\)\s*$", v, re.S)
    if m:
        v = m.group(1).strip()
    parts: list[str] = []
    i, n = 0, len(v)
    while i < n:
        c = v[i]
        if c in "'\"":
            pat = _DQ_STRING if c == '"' else _SQ_STRING
            mm = pat.match(v, i)
            if mm:
                j = i - 1
                while j >= 0 and v[j].isalpha():
                    j -= 1
                prefix = v[j + 1 : i].lower()
                if "f" in prefix and "{" in mm.group(1):
                    return None
                parts.append(mm.group(1))
                i = mm.end()
                continue
        i += 1
    if not parts:
        return None
    return "".join(parts).replace('\\"', '"').replace("\\'", "'")


def _split_top_level_quoted(text: str) -> list[str]:
    """Like `_split_top_level`, but a comma inside a string literal is NOT a
    split point. Free-text call args (title/subtitle/source_note) routinely
    contain commas in prose; the plain bracket-depth-only splitter would
    truncate the value at the first in-string comma.
    """
    parts: list[str] = []
    depth = 0
    quote: str | None = None
    cur: list[str] = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if quote:
            cur.append(c)
            if c == "\\" and i + 1 < n:
                cur.append(text[i + 1])
                i += 2
                continue
            if c == quote:
                quote = None
            i += 1
            continue
        if c in "'\"":
            quote = c
            cur.append(c)
        elif c in "([{":
            depth += 1
            cur.append(c)
        elif c in ")]}":
            depth -= 1
            cur.append(c)
        elif c == "," and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(c)
        i += 1
    parts.append("".join(cur))
    return [p for p in (p.strip() for p in parts) if p != ""]


def _kwarg_value_quoted_aware(block: str, name: str) -> str | None:
    """Like `_kwarg_value`, split via `_split_top_level_quoted` instead."""
    for part in _split_top_level_quoted(block):
        m = re.match(rf"{re.escape(name)}\s*=\s*(.+)", part, re.S)
        if m:
            return m.group(1).strip()
    return None


_TAB_HEADER_POSITIONAL_INDEX = {"title": 0, "subtitle": 1}


def _tab_header_text(source: str, kwarg: str) -> str | None:
    """Literal text of `tab_header(<kwarg>=...)` (title/subtitle), if set.

    Falls back to the positional form (`tab_header("Sales", "FY 2025")` —
    `title` is positional arg 0, `subtitle` is arg 1) when the keyword isn't
    present, so a validly-documented positional call isn't read as absent.
    """
    for block in _call_arg_blocks(source, "tab_header"):
        val = _kwarg_value_quoted_aware(block, kwarg)
        if val is None:
            idx = _TAB_HEADER_POSITIONAL_INDEX.get(kwarg)
            if idx is not None:
                positionals = [
                    p for p in _split_top_level_quoted(block)
                    if not re.match(r"[A-Za-z_]\w*\s*=", p)
                ]
                if idx < len(positionals):
                    val = positionals[idx]
        if val is not None:
            return _extract_text_literal(val)
    return None


def _source_note_texts(source: str) -> list[str]:
    """Literal text of every `.tab_source_note(...)` call, in source order.

    Step 6's convention (CONSISTENCY_DEV.md) is caption first, source second —
    each `tab_source_note` renders on its own stacked footer line in call
    order — so index 0 is the caption candidate and index 1 the source
    candidate when both are present. This function only extracts the raw
    ordered text; interpreting which slot is which is the comparator's job,
    not the parser's.
    """
    texts: list[str] = []
    for block in _call_arg_blocks(source, "tab_source_note"):
        val = _kwarg_value_quoted_aware(block, "source_note")
        if val is None:
            positionals = [
                p for p in _split_top_level_quoted(block) if not re.match(r"[A-Za-z_]\w*\s*=", p)
            ]
            val = positionals[0] if positionals else None
        if val is None:
            continue
        text = _extract_text_literal(val)
        if text is not None:
            texts.append(text)
    return texts


def _list_var_map(source: str) -> dict[str, list[str]]:
    """Best-effort ``{variable name -> [quoted strings]}`` for simple
    list-literal assignments (e.g. ``density_cols = ["density_1996", ...]``).

    Lets the per-column Tier-1 fields below (``fmt_column_map``,
    ``color_mechanics``) resolve a ``columns=density_cols``-style reference
    back to real column names — the idiomatic style this repo's own
    ground-truth scripts use for facet columns — without touching
    `_columns_token`/`_color_signature` (the convergence report's existing,
    unrelated repeat-vs-repeat contract, left unchanged on purpose).
    """
    out: dict[str, list[str]] = {}
    for m in re.finditer(r"^([A-Za-z_]\w*)\s*=\s*\[", source, re.M):
        name = m.group(1)
        open_idx = m.end() - 1
        depth = 0
        body = None
        for j in range(open_idx, len(source)):
            c = source[j]
            if c == "[":
                depth += 1
            elif c == "]":
                depth -= 1
                if depth == 0:
                    body = source[open_idx + 1 : j]
                    break
        if body is None:
            continue
        # Every top-level element must be a bare quoted string literal — a
        # comprehension (`[c for c in df.columns if c.startswith("pct_")]`)
        # or any other non-literal expression must NOT resolve, or a single
        # quoted substring inside it (e.g. "pct_") would be misread as the
        # variable's one-and-only column name.
        elems = _split_top_level_quoted(body)
        if elems and all(re.fullmatch(r"""['"][^'"]*['"]""", e) for e in elems):
            out[name] = [e[1:-1] for e in elems]
    return out


def _resolve_columns_token(value_text: str | None, var_map: dict[str, list[str]]) -> str:
    """Like `_columns_token`, but a bare identifier resolves through
    `var_map` first (e.g. `density_cols` -> its list's real column names)
    before falling back to the identifier text itself.
    """
    if value_text is not None:
        ident = value_text.strip()
        if ident in var_map and re.fullmatch(r"[A-Za-z_]\w*", ident):
            return ",".join(sorted(var_map[ident]))
    return _columns_token(value_text)


def _call_arg_blocks_pos(source: str, func: str) -> list[tuple[int, str]]:
    """Like `_call_arg_blocks`, paired with each match's source offset.

    Needed to interleave-sort calls of two different function names
    (`data_color` / `heatmap`) by true source order — see `_color_mechanics`.
    """
    out: list[tuple[int, str]] = []
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
                    out.append((m.start(), source[open_idx + 1 : j]))
                    break
    return out


def _bare_call_blocks_pos(source: str, func: str) -> list[tuple[int, str]]:
    """Position-paired variant of `_bare_call_blocks` (see `_call_arg_blocks_pos`)."""
    out: list[tuple[int, str]] = []
    for m in re.finditer(rf"(?<![\w.])(?:[A-Za-z_]\w*\.)?{re.escape(func)}\s*\(", source):
        open_idx = m.end() - 1
        depth = 0
        for j in range(open_idx, len(source)):
            c = source[j]
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    out.append((m.start(), source[open_idx + 1 : j]))
                    break
    return out


def _color_mechanics(source: str) -> list[dict]:
    """One dict per colored-measure call (`data_color`/`heatmap`), in TRUE
    source order (both call kinds interleave-sorted by match offset, so a
    script mixing `heatmap(...)` and `.data_color(...)` calls doesn't get
    all of one kind before the other): `columns`, `na_color`, `truncate`,
    `autocolor_text` — the Big-Color mechanics beyond the palette name
    already covered by `_extract_palettes`/`_color_signature`.

    `heatmap(gt, columns, *, kind, hue, domain=None)` (the scripted skill's
    helper, `gt_consistency.py`) does not accept `na_color`/`truncate`/
    `autocolor_text` as call-site kwargs at all — it always applies its own
    pinned values (`PALETTE["neutral"]["na_cell"]` = `#808080`,
    `truncate=False`, `autocolor_text=True`) internally, so a `heatmap(...)`
    call reports those FIXED values rather than looking for (and never
    finding) kwargs that can't be there.
    """
    var_map = _list_var_map(source)
    entries: list[tuple[int, dict]] = []
    for pos, block in _call_arg_blocks_pos(source, "data_color"):
        entries.append((pos, {
            "columns": _resolve_columns_token(_kwarg_value(block, "columns"), var_map),
            "na_color": _unquote(_kwarg_value(block, "na_color")),
            "truncate": _unquote(_kwarg_value(block, "truncate")),
            "autocolor_text": _unquote(_kwarg_value(block, "autocolor_text")),
        }))
    for pos, block in _bare_call_blocks_pos(source, "heatmap"):
        entries.append((pos, {
            "columns": _resolve_columns_token(_heatmap_columns_raw(block), var_map),
            "na_color": "#808080",
            "truncate": "False",
            "autocolor_text": "True",
        }))
    entries.sort(key=lambda e: e[0])
    return [d for _, d in entries]


def _render_params(source: str) -> dict:
    """`zoom`/`expand`/`vwidth`/`vheight` off the render call.

    Prefers a literal `.gtsave(...)` call. Falls back to a bare
    `finalize(gt, path=..., **overrides)` call (the scripted skill's
    helper, `gt_consistency.py`) when no literal `gtsave` is present:
    `finalize` always calls `gtsave` with `{"expand": 15, "zoom": 2.0}` as
    defaults, letting any of its own kwargs override them — so those two
    defaults are reported unless an explicit override is parseable in the
    `finalize(...)` call, mirroring what actually renders.

    Raw source text per kwarg (not coerced to float) — the comparator's fit-
    order check compares against the documented default and can parse these
    itself; keeping them as text avoids silently swallowing a non-literal
    value (e.g. `zoom=ZOOM_DEFAULT`).
    """
    blocks = _call_arg_blocks(source, "gtsave")
    if blocks:
        block = blocks[0]
        out: dict[str, str] = {}
        for kw in ("zoom", "expand", "vwidth", "vheight"):
            v = _kwarg_value(block, kw)
            if v is not None:
                out[kw] = v.strip()
        return out

    finalize_blocks = _bare_call_blocks(source, "finalize")
    if finalize_blocks:
        out = {"expand": "15", "zoom": "2.0"}
        block = finalize_blocks[0]
        for kw in ("zoom", "expand", "vwidth", "vheight"):
            v = _kwarg_value(block, kw)
            if v is not None:
                out[kw] = v.strip()
        return out

    return {}


def _bold_columns(source: str) -> list[str]:
    """Columns targeted by a bold `tab_style(style=style.text(weight="bold"),
    locations=loc.body(columns=...))` call — the hero-emphasis mechanism used
    when the hero column isn't a colored measure. Best-effort: only counts
    `tab_style` blocks whose `style=` value literally sets a bold weight AND
    whose `locations=` is a `loc.body(...)` call — a bold COLUMN LABEL
    (`loc.column_labels(...)`) is a different thing (header emphasis, not a
    hero-value emphasis) and must not be counted here. Both `style=`/
    `locations=` keywords and the equivalent positional form
    (`tab_style(style.text(...), loc.body(...))`) are recognized.
    """
    out: list[str] = []
    for block in _call_arg_blocks(source, "tab_style"):
        style_val = _kwarg_value(block, "style")
        loc_val = _kwarg_value(block, "locations")
        if style_val is None or loc_val is None:
            positionals = [
                p for p in _split_top_level(block) if not re.match(r"[A-Za-z_]\w*\s*=", p)
            ]
            if style_val is None and len(positionals) >= 1:
                style_val = positionals[0]
            if loc_val is None and len(positionals) >= 2:
                loc_val = positionals[1]
        style_val = style_val or ""
        loc_val = loc_val or ""
        if not re.search(r"weight\s*=\s*['\"]bold['\"]", style_val):
            continue
        if not re.search(r"loc\s*\.\s*body\s*\(", loc_val):
            continue
        m = re.search(r"columns\s*=\s*(\[[^\]]*\]|['\"][^'\"]+['\"])", loc_val)
        if m:
            out.extend(re.findall(r"['\"]([^'\"]+)['\"]", m.group(1)))
    return out


def _hlines_active(source: str) -> bool:
    """True if body-row hairlines (`table_body_hlines_*`) are set to non-none.

    An explicit `table_body_hlines_style="none"` is authoritative and
    disables the line regardless of any `_width`/`_color` also being set
    (those are meaningless once style disables rendering) — checked first
    so it can't be overridden by the generic per-kwarg scan below.
    """
    style_m = re.search(r"table_body_hlines_style\s*=\s*['\"]([^'\"]+)['\"]", source)
    if style_m and style_m.group(1).strip().lower() in ("none", "hidden", ""):
        return False
    for m in re.finditer(
        r"table_body_hlines_(?:style|width|color)\s*=\s*['\"]([^'\"]+)['\"]",
        source,
    ):
        if m.group(1).strip().lower() not in ("none", "hidden", ""):
            return True
    return False


def _fmt_column_map(source: str) -> dict[str, list[str]]:
    """Best-effort `{source column -> [fmt_* names applied]}`.

    Feeds the per-column semantic `fmt_*` check (against `SEMANTIC_TYPES`).
    Reads the `columns=` kwarg (or first positional) of each `.fmt_*(...)`
    call via the same `_columns_token` used by the color-signature helpers;
    a call with no parseable column target contributes nothing rather than
    being guessed.
    """
    var_map = _list_var_map(source)
    out: dict[str, list[str]] = {}
    for name, block in _fmt_calls(source):
        val = _kwarg_value(block, "columns")
        if val is None:
            positionals = [
                p for p in _split_top_level(block) if not re.match(r"[A-Za-z_]\w*\s*=", p)
            ]
            val = positionals[0] if positionals else None
        token = _resolve_columns_token(val, var_map)
        if token == "(cols?)":
            continue
        for col in token.split(","):
            out.setdefault(col, []).append(name)
    return out


def parse_design_choices(source: str, run_dir: Path | None = None) -> dict:
    """Parse a `table.py` source string into the design choices the rules pin down.

    Heuristic (regex) parsing — it reads the choices the skill's flowchart makes
    deterministic, not the full semantics of the script. The structural R5
    fields (grouping/stub/columns/fmt/domain) are pure source regex; `data_hash`
    needs `run_dir` (to exec the script against its data) and is None otherwise.
    """
    # Heading band: prefer the literal tab_options hex (unchanged behavior); only
    # fall back to a runtime band(gt, *, shade, hue) helper when no literal hex is
    # set, so a helper-based run scores the band the SAME as the literal path.
    band_hex = _find_band_color(source)
    band_helper = _find_band_helper(source) if band_hex is None else None
    if band_hex:
        heading_band_shade, heading_band_hue = _band_shade(band_hex), _classify_hue(band_hex)
    elif band_helper:
        heading_band_shade, heading_band_hue = band_helper
    else:
        heading_band_shade = heading_band_hue = "none"

    frame_present = bool(
        re.search(r"opt_table_outline\s*\(", source)
        or re.search(r"table_border_(?:left|right)_(?:style|width|color)\s*=", source)
        or re.search(r"\b(?:frame|finalize)\s*\(", source)
    )
    striping_present = bool(
        re.search(r"opt_row_striping\s*\(", source)
        or re.search(r"row_striping_background_color\s*=", source)
        or re.search(r"row_striping_include_table_body\s*=\s*True", source)
        or _bare_call_blocks(source, "stripe")  # runtime stripe(gt) helper
    )
    caption_present = any(
        re.search(r"subtitle\s*=", block) for block in _call_arg_blocks(source, "tab_header")
    )
    title_present = any(
        re.search(r"\btitle\s*=", block) for block in _call_arg_blocks(source, "tab_header")
    )
    source_present = bool(re.search(r"\.tab_source_note\s*\(", source))

    palettes = _extract_palettes(source)

    # R5: grouping / stub are GT(...) constructor kwargs (PP-1 / PP-13). An
    # explicit `groupname_col=None` / `rowname_col=None` counts as ABSENT — a
    # stub/group is present only when a real column value is supplied.
    gt_blocks = _gt_constructor_blocks(source)
    grouping_present = _constructor_col_present(gt_blocks, "groupname_col")
    stub_present = _constructor_col_present(gt_blocks, "rowname_col")

    # Columns hidden via cols_hide(...) — dropped from the data_hash so the hash
    # reflects the VISIBLE table.
    hidden_cols: list[str] = []
    for block in _call_arg_blocks(source, "cols_hide"):
        hidden_cols += re.findall(r"['\"]([^'\"]+)['\"]", block)

    # R5: best-effort computed-data hash (PP-18/PP-29); None-safe, off the
    # critical path — a failure here must never break the report.
    data_hash: str | None = None
    if run_dir is not None:
        try:
            data_hash = _compute_data_hash(run_dir, hidden_cols=hidden_cols)
        except Exception:
            data_hash = None

    return {
        "heading_band_shade": heading_band_shade,
        "heading_band_hue": heading_band_hue,
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
        "stub_tint_hue": _find_stub_tint_hue(source),
        "columns_signature": _columns_signature(source),
        "fmt_signature": _fmt_signature(source),
        "domain_signature": _domain_signature(source),
        "color_signature": _color_signature(source),
        "data_hash": data_hash,
        # Comparator Tier-1 additions (09-ground-truth-comparator.md §6):
        "spanner_present": bool(_call_arg_blocks(source, "tab_spanner")),
        "color_mechanics": _color_mechanics(source),
        "render_params": _render_params(source),
        "title_text": _tab_header_text(source, "title"),
        "subtitle_text": _tab_header_text(source, "subtitle"),
        "source_note_texts": _source_note_texts(source),
        "bold_columns": _bold_columns(source),
        "summary_row_present": bool(
            _call_arg_blocks(source, "grand_summary_rows")
            or _call_arg_blocks(source, "summary_rows")
        ),
        "hairlines_present": _hlines_active(source),
        "fmt_column_map": _fmt_column_map(source),
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

    A value of "(unknown)" is likewise skipped: it marks a signature that could
    not be MEASURED (e.g. no cols_label/cols_hide call), so identical "(unknown)"
    across runs must NOT be credited as unanimous agreement for a choice that was
    never observed. A real "no choice" sentinel like "(none)" still counts.
    """
    vals = [
        sig
        for c in repeat_choices
        if c is not None and c.get(field) is not None
        for sig in (_value_signature(c[field]),)
        if sig != "(unknown)"
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
    """Assemble the convergence report from parsed baseline + repeat results.

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
