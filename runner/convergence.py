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

import ast
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
# §2 neutrals) PLUS the great-tables-house skill's "accent"/"accent_tint"
# tiers (house_table.py's PALETTE) -- the brighter, more-saturated pairing
# that skill uses ONLY for the column-label band/stub/group headers. Used to
# label a heading-band color with its Dark-Academia hue family via
# nearest-neighbour in RGB. Neutrals collapse to "grey". Without the
# accent/accent_tint hexes here, a house-format-compliant band (which uses
# accent_tint, not the older washed tier) misclassifies as its nearest
# neutral instead of its actual hue family.
_FAMILY_HEXES: dict[str, list[str]] = {
    "navy": ["#22384F", "#EAF0F6", "#1B5A85", "#C9E0F0"],
    "forest": ["#2F4A38", "#EAF1EC", "#2E7350", "#CFEAD9"],
    "oxblood": ["#5C2E2E", "#F5EBEB", "#A23A3A", "#F4D6D6"],
    "espresso": ["#4A3A2C", "#F1EADD", "#8A6238", "#EEDFC7"],
    "ochre": ["#9A7B33", "#F5EFDC", "#B8912E", "#F6E8BE"],
    "tan": ["#8A7452", "#EFE7D6", "#9C8258", "#EFE3CE"],
    "grey": [
        "#F0F0F0", "#F6F6F6", "#E8E8E8", "#CCCCCC",
        "#BDBDBD", "#D0D0D0", "#808080", "#FFFFFF", "#000000",
    ],
}

# Flattened, for an EXACT-match membership check (not nearest-distance
# classification) -- used to reject a literal quiet-surface fill (stub
# tint, etc.) that isn't one of the recognized neutral/washed reference
# hexes at all, per palettes.md §2's "never a saturated color" rule.
_ALLOWED_TINT_HEXES = {h.upper() for hexes in _FAMILY_HEXES.values() for h in hexes}


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


def _is_effectively_transparent(color: str) -> bool:
    """True if a CSS color literal renders with effectively zero opacity.

    Beyond the literal keywords `transparent`/`none`/empty, also catches
    an `rgba(...)`/`rgb(...)` with a zero alpha channel and an 8-digit
    `#RRGGBBAA` / 4-digit `#RGBA` hex whose alpha byte/nibble is zero --
    all of these render NO visible fill, same as the literal keywords, so
    a candidate spelling transparency one of these other ways must not
    read as "a genuinely visible fill" just because it isn't the word
    "transparent".
    """
    c = color.strip()
    if c.lower() in ("transparent", "none", ""):
        return True
    m = re.fullmatch(r"rgba?\(\s*[^,]+,\s*[^,]+,\s*[^,]+,\s*([\d.]+)\s*\)", c, re.I)
    if m:
        try:
            return float(m.group(1)) == 0.0
        except ValueError:
            return False
    if re.fullmatch(r"#[0-9A-Fa-f]{8}", c):
        return c[-2:].lower() == "00"
    if re.fullmatch(r"#[0-9A-Fa-f]{4}", c):
        return c[-1].lower() == "0"
    return False


def _is_zero_length(v: str) -> bool:
    """True for a CSS-style zero length (`"0px"`, `"0"`, `"0.0em"`, ...).

    Shared by `_hlines_active`/`_vlines_active`: a zero-width/zero-weight
    border or rule renders no visible line no matter what its style/color
    say, so it must not count as "a divider/hairline is present."
    """
    return re.fullmatch(r"0+(\.0+)?(px|pt|em|rem|%)?", v.strip()) is not None


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


def _scan_balanced_paren(text: str, open_idx: int) -> int | None:
    """Index of the `)` matching the `(` at `open_idx` in `text`.

    Quote-aware: a `(`/`)` character INSIDE a string literal (e.g.
    `title="Sales (preliminary"`) does not affect depth — a naive
    char-by-char count would misread that unmatched `(` as opening a new
    nesting level, throw off the whole depth count, and never find the
    call's real closing paren (returning None / no block at all for
    perfectly valid, statically-static source). Handles TRIPLE-quoted
    strings (a run of three matching quote characters, Python's other
    string-literal form) as a single delimiter too — checking only one
    quote char at a time would treat a triple-quoted string containing a
    comma or paren as ending at the first of the three opening quote
    characters. Comment-aware too: a
    `#` outside any string starts a comment that runs to end-of-line, and
    a stray `(` inside an inline comment (`title="Sales",  # preliminary
    (`) must not affect depth either. Returns None if the parens never
    balance before the end of `text` (an actually-malformed/partial source
    snippet).
    """
    depth = 0
    quote: str | None = None  # the open delimiter: None, a 1-char, or 3-char string
    in_comment = False
    i, n = open_idx, len(text)
    while i < n:
        c = text[i]
        if in_comment:
            if c == "\n":
                in_comment = False
            i += 1
            continue
        if quote:
            if c == "\\" and i + 1 < n:
                i += 2
                continue
            if text[i : i + len(quote)] == quote:
                i += len(quote)
                quote = None
                continue
            i += 1
            continue
        if c in "'\"":
            quote = c * 3 if text[i : i + 3] == c * 3 else c
            i += len(quote)
            continue
        elif c == "#":
            in_comment = True
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return None


def _scan_balanced_bracket(text: str, open_idx: int) -> int | None:
    """Like `_scan_balanced_paren`, for `[`/`]` instead of `(`/`)`.

    Used by `_list_var_map`: a column name containing a literal `]`
    (`hero_cols = ["Profit ] share"]`) must not be misread as closing the
    list early. Triple-quote-aware too, for the same reason
    `_scan_balanced_paren` is — a triple-quoted element containing a `]`
    character must not close early either.
    """
    depth = 0
    quote: str | None = None
    i, n = open_idx, len(text)
    while i < n:
        c = text[i]
        if quote:
            if c == "\\" and i + 1 < n:
                i += 2
                continue
            if text[i : i + len(quote)] == quote:
                i += len(quote)
                quote = None
                continue
            i += 1
            continue
        if c in "'\"":
            quote = c * 3 if text[i : i + 3] == c * 3 else c
            i += len(quote)
            continue
        elif c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return None


def _call_arg_blocks(source: str, func: str) -> list[str]:
    """Return the argument text of every `.<func>(...)` call in `source`.

    A quote-aware balanced-paren scan (`_scan_balanced_paren`), so nested
    calls / lists inside the args (e.g. `domain=[df[...].min(), ...]`) are
    handled, AND an unmatched paren character inside a string argument
    (`title="Sales (preliminary"`) doesn't break the whole block extraction.
    """
    blocks: list[str] = []
    for m in re.finditer(rf"\.{re.escape(func)}\s*\(", source):
        open_idx = m.end() - 1
        close_idx = _scan_balanced_paren(source, open_idx)
        if close_idx is not None:
            blocks.append(source[open_idx + 1 : close_idx])
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
        close_idx = _scan_balanced_paren(source, open_idx)
        if close_idx is not None:
            blocks.append(source[open_idx + 1 : close_idx])
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
    chained `df.x.stripe(` is not caught. `(?<!def )` excludes a script's own
    `def heatmap(...):` declaration of the same name from being read as a call.
    """
    blocks: list[str] = []
    for m in re.finditer(rf"(?<!def )(?<![\w.])(?:[A-Za-z_]\w*\.)?{re.escape(func)}\s*\(", source):
        open_idx = m.end() - 1
        close_idx = _scan_balanced_paren(source, open_idx)
        if close_idx is not None:
            blocks.append(source[open_idx + 1 : close_idx])
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
    intact, AND so a quoted value containing its own comma —
    `columns="Sales, USD"` — isn't itself mistaken for a split point) and
    returns the value text of the first arg that *starts* with `name=`. None
    if the kwarg is absent. Whitespace/newlines inside the value are
    preserved for the caller to normalize.
    """
    for part in _split_top_level_quoted(block):
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
    'default'. Falls back to the positional slot (`data_color(columns, rows,
    palette, domain, ...)` -- palette is slot 2, verified against the
    installed great_tables==0.22.0 signature) when there's no `palette=`
    keyword, mirroring the same positional fallback `_color_mechanics`
    already applies to `columns`/`domain`. Shared by `_extract_palettes`
    and `_color_signature`.
    """
    m = re.search(r"palette\s*=\s*(\[[^\]]*\]|['\"]([^'\"]+)['\"])", block)
    if m:
        if m.group(2):
            return m.group(2)
        return "custom"
    positionals = [
        p for p in _split_top_level_quoted(block) if not re.match(r"[A-Za-z_]\w*\s*=", p)
    ]
    if len(positionals) > 2:
        pos_val = positionals[2].strip()
        if re.match(r"^\[[^\]]*\]$", pos_val):
            return "custom"
        qm = re.match(r"""^['"]([^'"]+)['"]$""", pos_val)
        if qm:
            return qm.group(1)
    return "default"


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


def _has_active_tab_style_border(source: str, side_pattern: str, *, require_loc_pattern: str | None = None) -> bool:
    """True if a `tab_style(style=style.borders(sides=...), ...)` call
    names a side matching `side_pattern` (a regex alternation like
    `left|right` or `top|bottom`) with a visible (non-`none`/non-zero)
    style and weight.

    Shared by `_vlines_active` (column-group dividers, `left`/`right`) and
    `_hlines_active` (row hairlines, `top`/`bottom`) — `tab_style` +
    `style.borders(...)` is one mechanism that can render either, keyed
    only by which `sides` value is named.

    `require_loc_pattern`, when given, additionally requires the SAME
    `tab_style(...)` call's `locations=` argument to match it (e.g.
    `loc\\.body\\(` for a body-row-scoped hairline) — a border drawn at
    `loc.column_labels()` (the heading rule) must not count as a body-row
    separator between ordinary rows. Left `None` (the default, used by
    `_vlines_active`) for callers where a column-group divider
    legitimately spans BOTH the body and the column-labels row.
    """
    for block in _call_arg_blocks(source, "tab_style"):
        if require_loc_pattern is not None:
            loc_val = _kwarg_value(block, "locations")
            if loc_val is None:
                positionals = [
                    p for p in _split_top_level(block) if not re.match(r"[A-Za-z_]\w*\s*=", p)
                ]
                loc_val = positionals[1] if len(positionals) >= 2 else None
            if loc_val is None or not re.search(require_loc_pattern, loc_val):
                continue
        style_val = _kwarg_value(block, "style")
        if style_val is None:
            positionals = [
                p for p in _split_top_level(block) if not re.match(r"[A-Za-z_]\w*\s*=", p)
            ]
            style_val = positionals[0] if positionals else None
        if style_val is None:
            continue
        # `style=` accepts a single style OR a list of them (the same
        # `Loc | list[Loc]`-shaped API `tab_style` uses for `locations=`),
        # e.g. `style=[style.borders(sides="top"), style.borders(sides=
        # "left")]` — inspect EVERY `style.borders(...)` occurrence, not
        # just the first, so a border named anywhere in the list counts.
        for bm in re.finditer(r"style\s*\.\s*borders\s*\(", style_val):
            open_idx = bm.end() - 1
            close_idx = _scan_balanced_paren(style_val, open_idx)
            if close_idx is None:
                continue
            borders_block = style_val[open_idx + 1 : close_idx]
            # A `style="none"`/`"hidden"` on the border itself disables it
            # regardless of which sides were named.
            border_style_val = _kwarg_value(borders_block, "style")
            if border_style_val is not None:
                unquoted = _unquote(border_style_val)
                if unquoted and unquoted.strip().lower() in ("none", "hidden", ""):
                    continue
            # A zero-weight border (`weight="0px"`) is equally invisible
            # regardless of style/sides.
            weight_val = _kwarg_value(borders_block, "weight")
            if weight_val is not None:
                unquoted_weight = _unquote(weight_val)
                if unquoted_weight and _is_zero_length(unquoted_weight):
                    continue
            sides_val = _kwarg_value(borders_block, "sides")
            if sides_val is None:
                positionals = [
                    p for p in _split_top_level(borders_block) if not re.match(r"[A-Za-z_]\w*\s*=", p)
                ]
                sides_val = positionals[0] if positionals else None
            if sides_val and re.search(rf"['\"](?:{side_pattern})['\"]", sides_val):
                return True
    return False


def _tab_options_frame_active(source: str) -> bool:
    """True if all FOUR border sides (top/bottom/left/right) are ACTIVELY
    set via manual `tab_options(...)` -- not merely mentioned.

    Uses the LAST occurrence of each attribute (chained-call last-wins,
    consistent with `_hlines_active`). A side counts only if at least one
    of its `style`/`width`/`color` is mentioned AT ALL, and if `style`/
    `width` IS given, it must not be a disabling value (`"none"`/
    `"hidden"`/zero-length) -- a candidate setting every side's style to
    `"none"` mentions all four sides without rendering a box at all.
    """
    def _last(attr: str) -> str | None:
        matches = re.findall(rf"table_border_{attr}\s*=\s*['\"]([^'\"]+)['\"]", source)
        return matches[-1] if matches else None

    for side in ("top", "bottom", "left", "right"):
        style_val = _last(f"{side}_style")
        width_val = _last(f"{side}_width")
        color_val = _last(f"{side}_color")
        if style_val is None and width_val is None and color_val is None:
            return False
        if style_val is not None and style_val.strip().lower() in ("none", "hidden", ""):
            return False
        if width_val is not None and _is_zero_length(width_val):
            return False
    return True


def _opt_row_striping_enabled(source: str) -> bool:
    """True if the LAST `.opt_row_striping(...)` call enables striping.

    `opt_row_striping(row_striping: bool = True)` -- a bare regex presence
    check would misread an explicit `.opt_row_striping(False)` (or
    `row_striping=False`) as striping being ON just because the call
    itself appears in the source. Uses the LAST call (chained-call
    last-wins, consistent with every other multi-call field in this
    module); omitted argument means the documented default (`True`).
    """
    blocks = _call_arg_blocks(source, "opt_row_striping")
    if not blocks:
        return False
    block = blocks[-1]
    val = _kwarg_value(block, "row_striping")
    if val is None:
        positionals = [p for p in _split_top_level(block) if not re.match(r"[A-Za-z_]\w*\s*=", p)]
        val = positionals[0] if positionals else None
    if val is None:
        return True
    unquoted = (_unquote(val) or val).strip().lower()
    return unquoted not in ("false", "0")


def _vlines_active(source: str) -> bool:
    """True if a column-group divider is present, by EITHER accepted mechanism.

    A table-wide `*_vlines_*` `tab_options` kwarg is one way; a per-boundary
    `tab_style(style=style.borders(sides="left"/"right", ...), ...)` call is
    the other (what `towny_growth_trends.py` actually uses for its spanner
    dividers) — both are equally valid per the outcome-only scoring rule, so
    either must count. Only an actual "left"/"right" token counts — a
    purely horizontal `sides=["top", "bottom"]` is a row rule (see
    `_hlines_active`), not a column divider.
    """
    for m in re.finditer(
        r"(?:table_body|column_labels)_vlines_(?:style|width|color)\s*=\s*['\"]([^'\"]+)['\"]",
        source,
    ):
        if m.group(1).strip().lower() not in ("none", "hidden", ""):
            return True
    return _has_active_tab_style_border(source, "left|right")


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
    """Every `.fmt_*(...)` call as (name, arg-block), via `_scan_balanced_paren`
    (quote-aware — an unmatched paren character inside a formatted column's
    string argument, e.g. `.fmt_number(columns="Sales (USD")`, must not
    break extraction, same as every other call-block scan in this module).
    """
    out: list[tuple[str, str]] = []
    for m in re.finditer(r"\.(fmt_[a-z_]+)\s*\(", source):
        name = m.group(1)
        open_idx = m.end() - 1
        close_idx = _scan_balanced_paren(source, open_idx)
        if close_idx is not None:
            out.append((name, source[open_idx + 1 : close_idx]))
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
        # Quote-aware: a column name can itself contain a comma (e.g.
        # "Sales, USD"), which the plain bracket-depth-only splitter would
        # misread as an argument separator.
        positionals = [
            p for p in _split_top_level_quoted(block) if not re.match(r"[A-Za-z_]\w*\s*=", p)
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


def _stub_tint_present(source: str) -> bool:
    """True if a VISIBLE stub tint is applied, by EITHER accepted mechanism.

    The `stub_tint(gt, *, hue)` runtime helper is one way; a literal
    `tab_style(style=style.fill(color=...), locations=loc.stub())` call is
    the other (what `towny_growth_trends.py` actually uses) — both are
    equally valid per the outcome-only scoring rule.

    A `style.fill(color=...)` call only counts if its color is genuinely
    visible -- `color="transparent"`/`"none"`/empty renders no tint at all,
    so a candidate spelling that out would otherwise satisfy this regex
    and receive full stub-tint credit for a fill nobody can actually see.
    """
    if _find_stub_tint_hue(source) is not None:
        return True
    for block in _call_arg_blocks(source, "tab_style"):
        loc_val = _kwarg_value(block, "locations")
        if loc_val is None:
            positionals = [
                p for p in _split_top_level(block) if not re.match(r"[A-Za-z_]\w*\s*=", p)
            ]
            loc_val = positionals[1] if len(positionals) >= 2 else None
        if loc_val is None or not re.search(r"loc\s*\.\s*stub\s*\(", loc_val):
            continue
        style_val = _kwarg_value(block, "style")
        if style_val is None:
            positionals = [
                p for p in _split_top_level(block) if not re.match(r"[A-Za-z_]\w*\s*=", p)
            ]
            style_val = positionals[0] if positionals else None
        if not style_val:
            continue
        fm = re.search(r"style\s*\.\s*fill\s*\(", style_val)
        if not fm:
            continue
        close_idx = _scan_balanced_paren(style_val, fm.end() - 1)
        fill_block = style_val[fm.end() : close_idx] if close_idx is not None else ""
        color_val = _kwarg_value(fill_block, "color")
        if color_val is None:
            fill_positionals = [
                p for p in _split_top_level(fill_block) if not re.match(r"[A-Za-z_]\w*\s*=", p)
            ]
            color_val = fill_positionals[0] if fill_positionals else None
        unquoted_color = _unquote(color_val) if color_val else None
        if unquoted_color is not None:
            stripped = unquoted_color.strip()
            if _is_effectively_transparent(stripped):
                continue
            # Per palettes.md §2, a quiet surface (stub tint included) is
            # ALWAYS a neutral grey or a washed tint of the table's
            # Big-Color hue -- NEVER an arbitrary saturated color. A
            # literal hex that isn't one of the recognized neutral/washed
            # reference values (e.g. `style.fill(color="#ff0000")`) is a
            # real grey-budget violation, not a merely-invisible fill --
            # reject it the same way. A non-hex value (a named CSS color,
            # a variable) can't be checked this precisely and keeps the
            # prior benefit-of-the-doubt.
            if stripped.startswith("#") and stripped.upper() not in _ALLOWED_TINT_HEXES:
                continue
        return True
    return False


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
# Triple-quoted literals, checked BEFORE the single-quote patterns above so
# a triple-double-quoted string containing an ordinary embedded double
# quote (`"""The "Best" Sales"""`) isn't misread as three single strings
# ending at the first embedded `"`. Non-greedy so it stops at the first
# genuine `"""`/`'''`, not the last one in the source.
_TQ_DQ_STRING = re.compile(r'"""((?:\\.|(?!""").)*?)"""', re.S)
_TQ_SQ_STRING = re.compile(r"'''((?:\\.|(?!''').)*?)'''", re.S)


def _find_quoted_strings(text: str) -> list[str]:
    """Every quoted string literal's content in `text`, matched by ITS OWN
    quote character — NOT `['"]` interchangeably. A quote-agnostic
    `re.findall(r"['\"]([^'\"]+)['\"]", ...)` misreads an apostrophe inside
    a double-quoted string (`columns="Owner's share"`) as the string's
    closing quote and returns the truncated `"Owner"`; matching each
    literal by its own opening delimiter (like `_extract_text_literal`
    already does for header/caption text) reads the whole `"Owner's
    share"` correctly.

    Each match is decoded via `ast.literal_eval` (real Python string-
    literal semantics — `\\'`/`\\u0020`/etc. resolve to the actual
    characters, not the literal escape sequence), falling back to the raw
    matched text only if `literal_eval` itself fails.

    An f-string with an unresolved `{...}` interpolation
    (`f"{metric}_rate"`) contributes NOTHING for that match — the runtime
    column name is whatever `metric` evaluates to, not the literal
    template text — matching `_extract_text_literal`'s identical guard for
    header/caption text.
    """
    out: list[str] = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c in "'\"":
            # Try the TRIPLE-quote pattern first (see
            # _extract_text_literal's identical ordering rationale): the
            # single-quote pattern would otherwise match just the opening
            # `"` of `"""..."""` and misread an embedded ordinary quote as
            # the string's end.
            triple = c * 3
            pat = (_TQ_DQ_STRING if c == '"' else _TQ_SQ_STRING) if text[i : i + 3] == triple else (
                _DQ_STRING if c == '"' else _SQ_STRING
            )
            m = pat.match(text, i)
            if m:
                j = i - 1
                while j >= 0 and text[j].isalpha():
                    j -= 1
                prefix = text[j + 1 : i].lower()
                if "f" in prefix and "{" in m.group(1):
                    i = m.end()
                    continue
                try:
                    out.append(ast.literal_eval(text[j + 1 : m.end()]))
                except Exception:
                    out.append(m.group(1))
                i = m.end()
                continue
        i += 1
    return out


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

    Likewise, anything OTHER than plain adjacent-literal concatenation
    (Python only allows whitespace/comments between two adjacent string
    literals) also returns None — a `+ str(year)` operator, a method chain,
    an f-string prefix, etc. left over once every matched literal span is
    removed means the value is a dynamic expression, not static text.

    Each segment is decoded via `ast.literal_eval` (real Python string-
    literal semantics: `\\n`/`\\t`/`\\uXXXX`/etc. all resolve to the actual
    characters that render, not the literal two-character escape sequence)
    rather than hand-rolled unescaping, falling back to the raw matched text
    only if `literal_eval` itself fails for some unforeseen reason.
    """
    v = value_text.strip()
    m = re.match(r"^(?:html|md)\s*\(\s*(.*)\)\s*$", v, re.S)
    if m:
        v = m.group(1).strip()
    # Peel a balanced OUTER `(...)` grouping -- e.g. `title=("Sales " "FY
    # 2025")`, a common style for wrapping a long adjacent-literal
    # concatenation across lines. Meaningless to Python (pure grouping, not
    # a tuple -- no top-level comma), so it must not count as "leftover"
    # dynamic content. Only strips a pair that spans the ENTIRE remaining
    # text and is genuinely balanced (its own depth never returns to 0
    # before the final char), so `("a") + ("b")` is correctly left alone.
    while v.startswith("(") and v.endswith(")") and len(v) >= 2:
        # Quote-aware (_scan_balanced_paren): a '(' inside a string literal
        # (`title=("Sales (preliminary")`) must not affect depth, or a
        # perfectly valid grouped literal gets misread as unbalanced.
        close_idx = _scan_balanced_paren(v, 0)
        if close_idx != len(v) - 1:
            break
        v = v[1:-1].strip()
    parts: list[str] = []
    spans: list[tuple[int, int]] = []
    i, n = 0, len(v)
    while i < n:
        c = v[i]
        if c in "'\"":
            # Try the TRIPLE-quote pattern first — checking the single-quote
            # one first would match just the opening `"` of `"""..."""` as
            # an empty string and misread an embedded ordinary quote
            # (`"""The "Best" Sales"""`) as the literal's end.
            triple = c * 3
            if v[i : i + 3] == triple:
                tpat = _TQ_DQ_STRING if c == '"' else _TQ_SQ_STRING
                tm = tpat.match(v, i)
                if tm:
                    j = i - 1
                    while j >= 0 and v[j].isalpha():
                        j -= 1
                    prefix = v[j + 1 : i].lower()
                    if "f" in prefix and "{" in tm.group(1):
                        return None
                    try:
                        decoded = ast.literal_eval(v[j + 1 : tm.end()])
                    except Exception:
                        decoded = tm.group(1)
                    parts.append(decoded)
                    spans.append((j + 1, tm.end()))
                    i = tm.end()
                    continue
            pat = _DQ_STRING if c == '"' else _SQ_STRING
            mm = pat.match(v, i)
            if mm:
                j = i - 1
                while j >= 0 and v[j].isalpha():
                    j -= 1
                prefix = v[j + 1 : i].lower()
                if "f" in prefix and "{" in mm.group(1):
                    return None
                try:
                    decoded = ast.literal_eval(v[j + 1 : mm.end()])
                except Exception:
                    decoded = mm.group(1)
                parts.append(decoded)
                spans.append((j + 1, mm.end()))
                i = mm.end()
                continue
        i += 1
    if not parts:
        return None
    covered = bytearray(n)
    for s, e in spans:
        for k in range(s, e):
            covered[k] = 1
    leftover = "".join(ch for idx, ch in enumerate(v) if not covered[idx])
    # A `#` in `leftover` is never inside a matched string (those spans are
    # already excluded above), so it's always the start of a genuine Python
    # comment — strip `#`-to-end-of-line before deciding whether anything
    # dynamic is left. A comment alongside otherwise-static text
    # (`("Sales FY 2025"  # concise heading\n)`) must not make static text
    # look unresolvable.
    leftover = re.sub(r"#[^\n]*", "", leftover)
    if leftover.strip():
        return None
    return "".join(parts)


def _split_top_level_quoted(text: str) -> list[str]:
    """Like `_split_top_level`, but a comma inside a string literal is NOT a
    split point. Free-text call args (title/subtitle/source_note) routinely
    contain commas in prose; the plain bracket-depth-only splitter would
    truncate the value at the first in-string comma. Triple-quoted
    delimiters (three matching quote characters) are tracked as a single
    unit too, the same as `_scan_balanced_paren` — otherwise a
    triple-quoted string containing an embedded ordinary quote followed by
    a comma would close early and treat the comma as a real split point.
    """
    parts: list[str] = []
    depth = 0
    quote: str | None = None
    cur: list[str] = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if quote:
            if c == "\\" and i + 1 < n:
                cur.append(text[i : i + 2])
                i += 2
                continue
            if text[i : i + len(quote)] == quote:
                cur.append(quote)
                i += len(quote)
                quote = None
                continue
            cur.append(c)
            i += 1
            continue
        if c in "'\"":
            quote = c * 3 if text[i : i + 3] == c * 3 else c
            cur.append(quote)
            i += len(quote)
            continue
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


# `_kwarg_value` is now quote-aware itself (it used to differ from this
# alias); kept as a name so existing call sites don't need to change.
_kwarg_value_quoted_aware = _kwarg_value


_TAB_HEADER_POSITIONAL_INDEX = {"title": 0, "subtitle": 1}

_STRING_LITERAL_RE = re.compile(r'^[bBrRuUfF]{0,2}(\'\'\'|"""|\'|")(.*)\1$', re.S)


def _is_absent_header_value(val: str) -> bool:
    """True when `val`'s raw source text is unmistakably empty: the literal
    `None` keyword, or a string literal containing only whitespace.

    A dynamic expression (a variable, an f-string built from other parts)
    gets the benefit of the doubt and is NOT treated as absent, since its
    actual rendered content can't be known from source text alone.
    """
    val = val.strip()
    if val == "None":
        return True
    m = _STRING_LITERAL_RE.match(val)
    return bool(m and m.group(2).strip() == "")


def _tab_header_arg_present(source: str, kwarg: str) -> bool:
    """True if `tab_header(...)`'s LAST call supplies `kwarg` with a value
    that isn't unmistakably empty — by keyword OR by position
    (`tab_header("Sales", "FY 2026")`).

    Mirrors `_tab_header_text`'s own keyword-then-positional resolution,
    but stops once a value is confirmed supplied rather than extracting its
    literal text. Explicit `None`/empty-string literals (`title=None`,
    `subtitle=""`) don't earn presence credit — see
    `_is_absent_header_value` — while a dynamic/variable value
    (`title=TITLE`, an f-string subtitle) still reads as present, since it
    can't be proven empty from source text.
    """
    blocks = _call_arg_blocks(source, "tab_header")
    if not blocks:
        return False
    block = blocks[-1]
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
    return val is not None and not _is_absent_header_value(val)


def _tab_header_text(source: str, kwarg: str) -> str | None:
    """Literal text of `tab_header(<kwarg>=...)` (title/subtitle), if set.

    Falls back to the positional form (`tab_header("Sales", "FY 2025")` —
    `title` is positional arg 0, `subtitle` is arg 1) when the keyword isn't
    present, so a validly-documented positional call isn't read as absent.

    Uses ONLY the LAST `tab_header(...)` call in the source — a script that
    calls it more than once (`.tab_header("Old").tab_header("New")`)
    renders the LATER one, in full: if that later call omits a field
    (`.tab_header(title="Old", subtitle="Stale").tab_header(title="New")`),
    the rendered header has NO subtitle at all, not the earlier call's
    stale one — great_tables replaces the whole header per call, it
    doesn't merge fields across calls. So only the last call's block is
    ever consulted; an earlier call's value never leaks through.
    """
    blocks = _call_arg_blocks(source, "tab_header")
    if not blocks:
        return None
    block = blocks[-1]
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
    return _extract_text_literal(val) if val is not None else None


def _source_note_texts(source: str) -> list[str | None]:
    """Literal text of every `.tab_source_note(...)` call, in source order.

    Step 6's convention (CONSISTENCY_DEV.md) is caption first, source second —
    each `tab_source_note` renders on its own stacked footer line in call
    order — so index 0 is the caption candidate and index 1 the source
    candidate when both are present. This function only extracts the raw
    ordered text; interpreting which slot is which is the comparator's job,
    not the parser's.

    ONE entry per call, always — a call whose text can't be resolved
    statically (a dynamic expression, an f-string with an interpolation)
    contributes `None` rather than being dropped. Dropping it would shift
    every later call's text one slot earlier, so a table with an unresolved
    caption followed by a resolvable source note would misreport the source
    text as though it were the caption.
    """
    texts: list[str | None] = []
    for block in _call_arg_blocks(source, "tab_source_note"):
        val = _kwarg_value_quoted_aware(block, "source_note")
        if val is None:
            positionals = [
                p for p in _split_top_level_quoted(block) if not re.match(r"[A-Za-z_]\w*\s*=", p)
            ]
            val = positionals[0] if positionals else None
        texts.append(_extract_text_literal(val) if val is not None else None)
    return texts


def _strip_line_comments(text: str) -> str:
    """Remove `#`-to-end-of-line comments from `text`, quote-aware (a
    literal `#` inside a string, e.g. a column named "Item #1", is not a
    comment and is left alone).
    """
    out: list[str] = []
    quote: str | None = None
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if quote:
            if c == "\\" and i + 1 < n:
                out.append(text[i : i + 2])
                i += 2
                continue
            if text[i : i + len(quote)] == quote:
                out.append(quote)
                i += len(quote)
                quote = None
                continue
            out.append(c)
            i += 1
            continue
        if c in "'\"":
            quote = c * 3 if text[i : i + 3] == c * 3 else c
            out.append(quote)
            i += len(quote)
            continue
        if c == "#":
            j = text.find("\n", i)
            i = j if j != -1 else n
            continue
        out.append(c)
        i += 1
    return "".join(out)


def _list_var_map(source: str) -> dict[str, list[str]]:
    """Best-effort ``{variable name -> [quoted strings]}`` for simple
    list-literal assignments (e.g. ``density_cols = ["density_1996", ...]``).

    Lets the per-column Tier-1 fields below (``fmt_column_map``,
    ``color_mechanics``) resolve a ``columns=density_cols``-style reference
    back to real column names — the idiomatic style this repo's own
    ground-truth scripts use for facet columns — without touching
    `_columns_token`/`_color_signature` (the convergence report's existing,
    unrelated repeat-vs-repeat contract, left unchanged on purpose).

    Matches the assignment regardless of leading indentation (a script
    that wraps its table-building code in a function, e.g.
    ``def build():\n    hero_cols = [...]``) and an optional type
    annotation (``hero_cols: list[str] = [...]``) — both are just as valid
    a column-list assignment as an unindented, unannotated one.
    """
    out: dict[str, list[str]] = {}
    for m in re.finditer(r"^[ \t]*([A-Za-z_]\w*)\s*(?::[^=\n]+)?=\s*\[", source, re.M):
        name = m.group(1)
        open_idx = m.end() - 1
        close_idx = _scan_balanced_bracket(source, open_idx)
        body = source[open_idx + 1 : close_idx] if close_idx is not None else None
        if body is None:
            continue
        # The bracketed literal must be the COMPLETE assignment value — a
        # compound expression (`hero_cols = ["sales"] + ["profit"]`) means
        # the real runtime value has more columns than just this one
        # literal, so treating it as the whole answer would silently drop
        # the rest. Only whitespace/a comment/end-of-statement may follow
        # the closing bracket.
        after = source[close_idx + 1 :]
        after_line = after.split("\n", 1)[0]
        if after_line.strip() and not after_line.strip().startswith("#"):
            continue
        # Every top-level element must be a bare quoted string literal — a
        # comprehension (`[c for c in df.columns if c.startswith("pct_")]`)
        # or any other non-literal expression must NOT resolve, or a single
        # quoted substring inside it (e.g. "pct_") would be misread as the
        # variable's one-and-only column name. Validated by ITS OWN quote
        # character (single- or triple- quote fullmatch), not a "no quotes
        # at all inside" check — the latter would reject (and so silently
        # drop the whole assignment for) a perfectly valid element
        # containing an apostrophe, e.g. `hero_cols = ["Owner's share"]`,
        # or a valid triple-quoted element like
        # `hero_cols = ["""The "Best" Sales"""]`. An explanatory comment
        # between elements (`["sales", # primary\n "profit"]`) is stripped
        # first — `_split_top_level_quoted` isn't comment-aware, so it
        # would otherwise glue the comment onto the following element's
        # text and fail the fullmatch, discarding the whole (fully static)
        # binding over what's really just a comment.
        elems = [
            e for e in (_strip_line_comments(p).strip() for p in _split_top_level_quoted(body))
            if e
        ]
        if elems and all(
            _DQ_STRING.fullmatch(e) or _SQ_STRING.fullmatch(e)
            or _TQ_DQ_STRING.fullmatch(e) or _TQ_SQ_STRING.fullmatch(e)
            for e in elems
        ):
            out[name] = [_find_quoted_strings(e)[0] for e in elems]
    return out


# Sentinel `_resolve_columns_token`/`_fmt_column_map` use for an explicit
# `columns=None` — the documented great_tables meaning is "every column",
# not a column literally named "None"; callers that attribute per-column
# data (e.g. `_fmt_column_map`) must treat this as unresolvable-per-column
# rather than fabricating a fake `"None"` column entry.
_ALL_COLUMNS = "(all)"


def _resolve_columns_token(value_text: str | None, var_map: dict[str, list[str]]) -> str:
    """Like `_columns_token`, but a bare identifier resolves through
    `var_map` first (e.g. `density_cols` -> its list's real column names)
    before falling back to the identifier text itself. A literal `None`
    (great_tables' "apply to every column" default) resolves to the
    `_ALL_COLUMNS` sentinel rather than the fake column name `"None"`.
    """
    if value_text is not None:
        ident = value_text.strip()
        if ident == "None":
            return _ALL_COLUMNS
        if ident in var_map and re.fullmatch(r"[A-Za-z_]\w*", ident):
            return ",".join(sorted(var_map[ident]))
    return _columns_token(value_text)


def _resolve_columns_list(value_text: str | None, var_map: dict[str, list[str]]) -> list[str]:
    """Like `_resolve_columns_token`, but returns the actual list of column
    names instead of a comma-joined string.

    Exists because `token.split(",")` on `_resolve_columns_token`'s joined
    string is ambiguous when a column name itself contains a comma
    (`"Sales, USD"` joined with a second column becomes indistinguishable
    from two columns "Sales" and "USD"). Callers that need to iterate
    individual column names (`_fmt_column_map`, `_color_mechanics`,
    `_bold_columns`) use this instead; callers that only ever treat the
    result as an opaque signature string (`_color_signature`,
    `_columns_signature`) keep using `_resolve_columns_token`/
    `_columns_token`, where the ambiguity doesn't matter (the string is
    never re-split, only compared for equality across runs).
    """
    if value_text is None:
        return []
    ident = value_text.strip()
    if ident == "None":
        return []
    if ident in var_map and re.fullmatch(r"[A-Za-z_]\w*", ident):
        return sorted(var_map[ident])
    # A column-selector expression (great_tables/polars `cs.starts_with(...)`
    # and friends) is not a literal column reference — its quoted operand
    # ("rate_") is a PATTERN, not itself a column name, and the columns it
    # actually selects (rate_q1, rate_q2, ...) can't be known without the
    # real schema. Extracting that operand as though it were one concrete
    # column is worse than admitting it's unresolvable.
    if re.match(r"^cs\s*\.\s*\w+\s*\(", ident):
        return []
    return _find_quoted_strings(value_text)


def _call_arg_blocks_pos(source: str, func: str) -> list[tuple[int, str]]:
    """Like `_call_arg_blocks`, paired with each match's source offset.

    Needed to interleave-sort calls of two different function names
    (`data_color` / `heatmap`) by true source order — see `_color_mechanics`.
    """
    out: list[tuple[int, str]] = []
    for m in re.finditer(rf"\.{re.escape(func)}\s*\(", source):
        open_idx = m.end() - 1
        close_idx = _scan_balanced_paren(source, open_idx)
        if close_idx is not None:
            out.append((m.start(), source[open_idx + 1 : close_idx]))
    return out


def _bare_call_blocks_pos(source: str, func: str) -> list[tuple[int, str]]:
    """Position-paired variant of `_bare_call_blocks` (see `_call_arg_blocks_pos`)."""
    out: list[tuple[int, str]] = []
    for m in re.finditer(rf"(?<!def )(?<![\w.])(?:[A-Za-z_]\w*\.)?{re.escape(func)}\s*\(", source):
        open_idx = m.end() - 1
        close_idx = _scan_balanced_paren(source, open_idx)
        if close_idx is not None:
            out.append((m.start(), source[open_idx + 1 : close_idx]))
    return out


# `great_tables.GT.data_color`'s OWN defaults when a kwarg is omitted
# (verified against the installed `great_tables==0.22.0`: the constructor
# kwarg defaults to `None`, but `_data_color/base.py` substitutes this
# literal hex whenever `na_color is None`) — a LITERAL `.data_color(...)`
# call that omits these renders IDENTICALLY to one that states them, and to
# an equivalent `heatmap(...)` helper call, so all three must report the
# same mechanics rather than two `None`s and one explicit value.
_DATA_COLOR_DEFAULTS = {"na_color": "#808080", "truncate": "False", "autocolor_text": "True", "reverse": "False"}


def _kwarg_or_default(
    block: str, name: str, positionals: list[str] | None = None, index: int | None = None,
) -> str | None:
    """`_unquote(_kwarg_value(block, name))`, defaulting when omitted OR
    explicitly `None` (`na_color=None` is documented as "use the default,"
    identical to not passing it at all — a bare unquoted `"None"` must not
    be treated as a real, different value from the default it explicitly
    requests).

    Falls back to `positionals[index]` (same shared, quote-aware split the
    caller already uses for `columns`/`rows`/`domain`) when the keyword
    isn't found and a position was given — `.data_color("sales", None,
    "Blues", [0, 10], "red", None, False, False, True)` sets `na_color`,
    `autocolor_text`, and `truncate` purely positionally; a keyword-only
    lookup would silently substitute the "safe" default for a rendered
    value that's actually wrong.

    Returns `None` (unresolved, NOT the default) when `block` contains a
    `**overrides`/`**{...}` expansion — it could set this exact kwarg to
    something this parser can't see, so asserting the safe default could
    mask a genuinely different rendered value (same reasoning as
    `_render_params`'s `**`-expansion guard).
    """
    if any(p.strip().startswith("**") for p in _split_top_level_quoted(block)):
        return None
    val = _kwarg_value(block, name)
    if val is None and positionals is not None and index is not None and len(positionals) > index:
        val = positionals[index]
    v = _unquote(val)
    if v is None or v == "None":
        return _DATA_COLOR_DEFAULTS[name]
    return v


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
    finding) kwargs that can't be there. A literal `.data_color(...)` call
    that omits any of the three gets the SAME materialized defaults
    (`_DATA_COLOR_DEFAULTS`), since that's what actually renders.

    A `.data_color(..., rows=[...])` call restricted to a subset of rows is
    EXCLUDED entirely (like the analogous `_fmt_column_map` row-scope
    exclusion) — it colors only part of the column, so it must not be
    reported identically to a call that colors the whole measure.
    `heatmap(...)` has no `rows=` parameter at all, so this only applies to
    the literal branch.

    `columns` is an actual `list[str]` (via `_resolve_columns_list`), not a
    comma-joined string — a column name can itself contain a comma, which a
    joined-then-split representation can't distinguish from two columns.
    `None` (not `[]`) for a literal `.data_color(...)` call whose `columns`
    is omitted or explicitly `None` — see the "all columns" note below.

    `palette` is the palette/hue name (`_palette_of_block` for a literal
    `data_color`, the `hue=` kwarg for `heatmap`) — needed by the
    comparator to classify each colored measure as sequential vs.
    diverging and to check for a same-family hue collision between two
    measures, neither of which `_extract_palettes`/`_color_signature`
    (which report palettes independent of which measure they belong to)
    can answer on their own.

    `domain` is the raw `domain=` kwarg text (None if omitted) — kept
    per-entry rather than relying on `_domain_signature`'s OWN list, which
    is SORTED (for stable repeat-vs-repeat comparison) and so cannot be
    zipped positionally against this list, which is TRUE SOURCE ORDER.

    `via_helper` is True for a `heatmap(...)` entry, False for a literal
    `.data_color(...)` entry — needed by the comparator's domain check: an
    OMITTED domain is guaranteed shape-correct (symmetric-for-diverging /
    full-range-for-sequential) only for `heatmap(...)`, which always
    computes one internally. A literal `.data_color(...)` that omits
    `domain` instead falls back to `great_tables`' own auto-inferred range,
    which is NOT guaranteed symmetric around zero for diverging data, so
    the two cases must not get the same benefit-of-the-doubt treatment.

    `source` is comment-stripped FIRST (quote-aware, so a genuinely live
    call is untouched) -- otherwise a commented-out `# gt.data_color(...)`
    line is scanned exactly like a live one, and if it names a canonical
    measure, the candidate can receive colored-measure, palette-shape,
    domain, and mechanics credit for a table that renders completely
    uncolored. Does NOT catch the same dead text inside a triple-quoted
    docstring (a string literal is legitimate content everywhere else in
    this module; distinguishing "this triple-quoted string IS a docstring"
    from "IS an argument value" isn't attempted here) -- a narrower,
    known-remaining gap.
    """
    source = _strip_line_comments(source)
    var_map = _list_var_map(source)
    entries: list[tuple[int, dict]] = []
    for pos, block in _call_arg_blocks_pos(source, "data_color"):
        # `data_color(columns, rows, palette, domain, ...)` -- shared once
        # so `rows`/`columns`/`domain` positional fallbacks (slots 1/0/3)
        # all line up against the SAME split, quote-aware (see
        # _heatmap_columns_raw: a column name can itself contain a comma).
        positionals = [
            p for p in _split_top_level_quoted(block) if not re.match(r"[A-Za-z_]\w*\s*=", p)
        ]
        rows_val = _kwarg_value(block, "rows")
        if rows_val is None and len(positionals) > 1:
            rows_val = positionals[1]
        if rows_val is not None and rows_val.strip() != "None":
            continue
        cols_val = _kwarg_value(block, "columns")
        if cols_val is None:
            cols_val = positionals[0] if positionals else None
        if cols_val is None or cols_val.strip() == "None":
            # `columns` omitted entirely, or explicit `columns=None` --
            # great_tables applies data_color to EVERY column in that case.
            # Tier 1 has no access to the real rendered schema to enumerate
            # that here (this function only sees static source text), so a
            # bare `[]` would wrongly look identical to "unresolvable" --
            # `None` is an explicit sentinel the comparator expands against
            # the candidate's actual Tier-2 visible columns at scoring time.
            resolved_columns = None
        else:
            resolved_columns = _resolve_columns_list(cols_val, var_map)
        domain_val = _kwarg_value(block, "domain")
        if domain_val is None and len(positionals) > 3:
            # A positional `domain` can ONLY occur if columns/rows/palette
            # were ALSO all positional (you can't skip earlier positions),
            # so the shared `positionals` list above already lines up
            # domain at index 3 when it's long enough.
            domain_val = positionals[3]
        entries.append((pos, {
            "columns": resolved_columns,
            "palette": _palette_of_block(block),
            "domain": domain_val,
            # data_color(columns, rows, palette, domain, na_color, alpha,
            # reverse, autocolor_text, truncate) -- positional slots 4/6/7/8.
            "na_color": _kwarg_or_default(block, "na_color", positionals, 4),
            "reverse": _kwarg_or_default(block, "reverse", positionals, 6),
            "truncate": _kwarg_or_default(block, "truncate", positionals, 8),
            "autocolor_text": _kwarg_or_default(block, "autocolor_text", positionals, 7),
            "via_helper": False,
        }))
    for pos, block in _bare_call_blocks_pos(source, "heatmap"):
        entries.append((pos, {
            "columns": _resolve_columns_list(_heatmap_columns_raw(block), var_map),
            "palette": _unquote(_kwarg_value(block, "hue")) or "default",
            "domain": _kwarg_value(block, "domain"),
            # `heatmap(gt, columns, *, kind, hue, domain=None)`'s own
            # `kind=` IS the declared encoding decision -- more
            # authoritative than reverse-engineering it from `palette`
            # above, which for a helper call is the raw semantic `hue=`
            # key (e.g. "neutral"), not a real palette name
            # `_palette_kind` can classify. `None` when `kind` is itself a
            # dynamic expression -- unresolvable, not a wrong answer.
            "kind": _unquote(_kwarg_value(block, "kind")),
            "na_color": "#808080",
            "truncate": "False",
            "autocolor_text": "True",
            # heatmap() doesn't expose a `reverse` param at all -- it
            # always calls the underlying data_color(...) without one, so
            # it always renders with GT's own reverse=False default.
            "reverse": "False",
            "via_helper": True,
        }))
    entries.sort(key=lambda e: e[0])
    return [d for _, d in entries]


def _targets_table_png(value_text: str) -> bool:
    """True if a `gtsave`/`finalize` path argument's value is EXACTLY
    `table.png` (optionally `./table.png`) — the harness's mandated output
    location, not merely a path whose BASENAME happens to be `table.png`.
    A plain `"table.png" in value_text` substring check would also match
    `"backup/table.png"`, a genuinely different file in a subdirectory
    that the harness never reads — matching by basename alone would make
    the exact same mistake (its basename is ALSO `table.png`).
    """
    unquoted = (_unquote(value_text) or value_text).strip()
    if unquoted.startswith("./"):
        unquoted = unquoted[2:]
    return unquoted == "table.png"


def _blocks_target_table_png(blocks: list[str], path_kwarg: str, path_index: int) -> bool:
    """True if any call block's path argument plausibly targets `table.png`.

    A literal path (`"preview.png"`) only counts when `_targets_table_png`
    confirms it; a non-literal path (a variable, an f-string) can't be
    proven wrong from source text alone and gets the benefit of the
    doubt, same as `_render_params`'s own `**overrides` handling.
    """
    for b in blocks:
        path_val = _kwarg_value(b, path_kwarg)
        if path_val is None:
            positionals = [
                p for p in _split_top_level_quoted(b) if not re.match(r"[A-Za-z_]\w*\s*=", p)
            ]
            path_val = positionals[path_index] if len(positionals) > path_index else None
        if path_val is None:
            continue
        if not _STRING_LITERAL_RE.match(path_val.strip()):
            return True  # non-literal -- can't prove it's the wrong target
        if _targets_table_png(path_val):
            return True
    return False


def _render_call_targets_table_png(source: str) -> bool:
    """True if some `gtsave`/`finalize` call plausibly produced the
    harness's mandated `table.png` artifact.

    Any `gtsave()`/`finalize()` call exists != that call wrote the file
    the harness actually reads: a candidate that only ever writes
    `preview.png` (or some other literal path) never produced `table.png`,
    no matter how many render calls it made. Non-literal paths keep the
    prior benefit-of-the-doubt behavior (see `_blocks_target_table_png`).
    """
    if _blocks_target_table_png(_call_arg_blocks(source, "gtsave"), "file", 0):
        return True
    return _blocks_target_table_png(_bare_call_blocks(source, "finalize"), "path", 1)


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
    value (e.g. `zoom=ZOOM_DEFAULT`). A literal `.gtsave(...)` call that
    omits `zoom`/`expand` renders with `great_tables.GT.gtsave`'s own
    defaults (`zoom=2.0`, `expand=5` — verified against the installed
    `great_tables==0.22.0` signature), so those are materialized too, the
    same way the `finalize(...)` branch already materializes its defaults.

    When there are MULTIPLE `.gtsave(...)` calls (e.g. an earlier debug/
    preview render before the final one), prefers whichever call's target
    path contains `table.png` — the harness's mandated output filename —
    over just taking the first. When SEVERAL calls target `table.png`
    (writing it more than once), the LAST one is the one whose parameters
    actually produced the final artifact (it overwrote every earlier
    write), so the loop keeps scanning rather than stopping at the first
    match. Falls back to the LAST call overall (last-wins, consistent with
    the other multi-call fields above) when none of them mentions
    `table.png` explicitly (e.g. a variable path).
    """
    blocks = _call_arg_blocks(source, "gtsave")
    if blocks:
        block = blocks[-1]  # last-wins default when no call targets table.png
        for b in blocks:
            file_val = _kwarg_value(b, "file")
            if file_val is None:
                positionals = [
                    p for p in _split_top_level_quoted(b) if not re.match(r"[A-Za-z_]\w*\s*=", p)
                ]
                file_val = positionals[0] if positionals else None
            if file_val and _targets_table_png(file_val):
                block = b  # keep scanning -- a LATER table.png write wins
        # Same **overrides/**{...} guard as the finalize(...) branch below:
        # an expansion can override the materialized defaults with values
        # this parser can't see.
        if any(p.strip().startswith("**") for p in _split_top_level(block)):
            return {}
        out: dict[str, str] = {"zoom": "2.0", "expand": "5"}
        for kw in ("zoom", "expand", "vwidth", "vheight"):
            v = _kwarg_value(block, kw)
            if v is not None:
                out[kw] = v.strip()
        return out

    finalize_blocks = _bare_call_blocks(source, "finalize")
    if finalize_blocks:
        # Same target-aware, last-write-wins selection as the .gtsave(...)
        # branch above: finalize(gt, path=..., **overrides)'s `path` is the
        # 2nd positional/kwarg.
        block = finalize_blocks[-1]
        for b in finalize_blocks:
            path_val = _kwarg_value(b, "path")
            if path_val is None:
                positionals = [
                    p for p in _split_top_level_quoted(b) if not re.match(r"[A-Za-z_]\w*\s*=", p)
                ]
                path_val = positionals[1] if len(positionals) >= 2 else None  # positionals[0] is `gt`
            if path_val and _targets_table_png(path_val):
                block = b
        # A `**overrides`/`**{...}` expansion can override the defaults with
        # values this parser can't see (it isn't a literal `kwarg=value`) --
        # reporting the defaults anyway could mask a below-minimum override
        # (e.g. `finalize(gt, **{"zoom": 1.0})`), so leave this unresolved
        # rather than assert a default that might not be what actually
        # rendered.
        if any(p.strip().startswith("**") for p in _split_top_level(block)):
            return {}
        out = {"expand": "15", "zoom": "2.0"}
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
    var_map = _list_var_map(source)
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
        # `locations=` accepts a single Loc OR a list of them
        # (`[loc.body(columns="sales"), loc.body(columns="profit")]` —
        # `tab_style`'s documented `Loc | list[Loc]` signature) — iterate
        # every `loc.body(...)` occurrence, not just the first.
        for body_m in re.finditer(r"loc\s*\.\s*body\s*\(", loc_val):
            open_idx = body_m.end() - 1
            close_idx = _scan_balanced_paren(loc_val, open_idx)
            if close_idx is None:
                continue
            body_args = loc_val[open_idx + 1 : close_idx]
            # A `rows=[...]`-restricted location bolds only a subset of
            # cells, not the whole column — must not count as the required
            # whole-column hero emphasis (same row-scope exclusion already
            # applied to fmt_column_map/color_mechanics). A `**{...}`
            # expansion could supply `rows=` invisibly to the keyword
            # lookup, so it's treated the same as an explicit row
            # restriction — it MIGHT be row-scoped and this parser can't
            # tell, so it's not credited as whole-column emphasis either.
            rows_val = _kwarg_value(body_args, "rows")
            has_expansion = any(
                p.strip().startswith("**") for p in _split_top_level_quoted(body_args)
            )
            if has_expansion or (rows_val is not None and rows_val.strip() != "None"):
                continue
            cols_val = _kwarg_value(body_args, "columns")
            if cols_val is None:
                # Quote-aware (see _heatmap_columns_raw): a column name can
                # itself contain a comma.
                positionals = [
                    p for p in _split_top_level_quoted(body_args)
                    if not re.match(r"[A-Za-z_]\w*\s*=", p)
                ]
                cols_val = positionals[0] if positionals else None
            if cols_val:
                # Resolve a list-variable reference (e.g. `loc.body(columns=
                # hero_cols)`) through var_map, the same as the other
                # per-column fields, before falling back to plain quoted
                # names. _resolve_columns_list (not _resolve_columns_token)
                # avoids the join-then-split ambiguity for a column name
                # containing a comma.
                out.extend(_resolve_columns_list(cols_val, var_map))
    return out


def _hlines_active(source: str) -> bool:
    """True if body-row hairlines (`table_body_hlines_*`) are set to non-none.

    Uses the LAST occurrence of each of `style`/`width`/`color` independently
    — a script commonly chains multiple `.tab_options(...)` calls, and a
    later call's kwarg overrides an earlier one for that same attribute
    (`.tab_options(table_body_hlines_style="none").tab_options(
    table_body_hlines_style="solid")` renders WITH hairlines; reading only
    the first match would get this backwards). An explicit LAST
    `table_body_hlines_style="none"` is authoritative and disables the line
    regardless of any `_width`/`_color` also being set (those are
    meaningless once style disables rendering). Likewise a zero-length
    `_width` (`"0px"`, `"0"`, ...) renders no visible line no matter what
    `style`/`color` say, so it is equally authoritative.

    A per-boundary `tab_style(style=style.borders(sides="top"/"bottom",
    ...), locations=loc.body())` call is an EQUALLY valid alternate
    mechanism for rendering row hairlines (the outcome-only scoring rule
    applies here the same way it does for `_vlines_active`'s
    `left`/`right` equivalent) — checked whenever the table-wide
    `table_body_hlines_*` options don't themselves establish an active
    line, INCLUDING when they explicitly disable it
    (`.tab_options(table_body_hlines_style="none")` followed by a
    separate `tab_style(...)` border is a real, if unusual, way to turn
    off the default line and draw a custom one instead — the disabled
    table-wide option must not short-circuit past checking for that).
    """
    def _last(attr: str) -> str | None:
        matches = re.findall(rf"table_body_hlines_{attr}\s*=\s*['\"]([^'\"]+)['\"]", source)
        return matches[-1] if matches else None

    style = _last("style")
    width = _last("width")
    disabled = (style is not None and style.strip().lower() in ("none", "hidden", "")) or (
        width is not None and _is_zero_length(width)
    )
    if not disabled:
        for v in (style, width, _last("color")):
            if v is not None and v.strip().lower() not in ("none", "hidden", ""):
                return True
    return _has_active_tab_style_border(source, "top|bottom", require_loc_pattern=r"loc\s*\.\s*body\s*\(")


def _fmt_column_map(source: str) -> dict[str, str | bool]:
    """Best-effort `{source column -> the EFFECTIVE fmt_* name}`.

    A value of `False` (never a real formatter name) means "explicitly
    NOT covered" -- overrides the `_ALL_COLUMNS` fallback for that one
    column without discarding the sentinel's credit for every other
    column it still validly covers. See the row-scoped-invalidation note
    below.

    Feeds the per-column semantic `fmt_*` check (against `SEMANTIC_TYPES`).
    Reads the `columns=` kwarg (or first positional) of each `.fmt_*(...)`
    call via the same `_columns_token` used by the color-signature helpers;
    a call with no parseable column target, or an explicit `columns=None`
    (`_ALL_COLUMNS` — "every column", not a column literally named "None"),
    contributes nothing rather than being guessed or fabricated. A call
    restricted to a subset of rows (`rows=...`, and not the literal `None`
    "every row" default) is EXCLUDED entirely — it doesn't format the whole
    column, so it must not satisfy a whole-column semantic-type check the
    same way a full-column call does.

    When the SAME column is formatted more than once
    (`.fmt_percent(columns="rate").fmt_number(columns="rate")`), only the
    LAST call actually renders — `fmt_*` calls don't stack, each later one
    replaces the formatting of every column it targets. `_fmt_calls`
    yields calls in source order, so simply overwriting on each occurrence
    naturally keeps only the effective (last) one per column, rather than
    accumulating every formatter ever applied.

    A LATER call that targets EVERY column (`columns=None`, or `columns`
    omitted entirely — both mean "every column" per the documented
    default) invalidates every per-column entry tracked so far (they're
    now stale, overwritten by this call) but is itself recorded under the
    `_ALL_COLUMNS` sentinel key rather than discarded outright — an
    all-percent table using only `.fmt_percent()` must still get semantic-
    format credit for every visible column, not lose it just because this
    parser can't enumerate the real schema itself. Callers that key by
    column name (`check_fmt_semantic_type`, `check_summary_row_formatting`)
    fall back to `map.get(_ALL_COLUMNS)` for any column with no more
    specific entry.

    A row-scoped LATER call for a column that ALREADY has a whole-column
    entry also invalidates that entry (rather than merely being skipped)
    UNLESS it's the SAME formatter name — it overwrites the formatting for
    the rows it targets, so a column that's "mostly fmt_percent, one row
    overridden to fmt_number" must not read as "fully fmt_percent"; but a
    row-scoped re-application of the identical formatter
    (`.fmt_percent(columns="rate").fmt_percent(columns="rate",
    rows=[0])`) leaves the column uniformly the same format it already
    was, so that entry survives.

    A `**overrides`/`**{...}` expansion supplying `rows=` isn't visible to
    the plain keyword lookup, so a row-scoped call written that way would
    otherwise be read as unrestricted (no `rows=` found) and wrongly
    establish/keep a whole-column entry — treated the same as an explicit
    `rows=[...]` (invalidate, don't establish) since it MIGHT be
    row-restricted and this parser can't tell.
    """
    var_map = _list_var_map(source)
    out: dict[str, str | bool] = {}
    for name, block in _fmt_calls(source):
        # Quote-aware (see _heatmap_columns_raw): a column name can itself
        # contain a comma. Every `fmt_*` function shares the same
        # `(columns, rows, ...)` positional order (verified against the
        # installed great_tables==0.22.0 signatures), so this one
        # `positionals` list backs both the columns AND rows fallback below.
        positionals = [
            p for p in _split_top_level_quoted(block) if not re.match(r"[A-Za-z_]\w*\s*=", p)
        ]
        val = _kwarg_value(block, "columns")
        if val is None:
            val = positionals[0] if positionals else None
        rows_val = _kwarg_value(block, "rows")
        if rows_val is None and len(positionals) > 1:
            rows_val = positionals[1]
        has_expansion = any(p.strip().startswith("**") for p in _split_top_level_quoted(block))
        row_restricted = has_expansion or (rows_val is not None and rows_val.strip() != "None")
        if row_restricted:
            if val is None or val.strip() == "None":
                out.clear()
            else:
                for col in _resolve_columns_list(val, var_map):
                    if out.get(col, out.get(_ALL_COLUMNS)) != name:
                        # This row-scoped call disagrees with the earlier
                        # effective formatter for `col` specifically --
                        # `False` explicitly excludes JUST this column from
                        # any `_ALL_COLUMNS` fallback, rather than dropping
                        # the sentinel entirely and losing formatting
                        # credit for every OTHER, unaffected column too.
                        out[col] = False
            continue
        if val is None or val.strip() == "None":
            out.clear()
            out[_ALL_COLUMNS] = name
            continue
        for col in _resolve_columns_list(val, var_map):
            out[col] = name
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
        # NOT `finalize(...)` -- the scripted skill's own `finalize()`
        # helper only calls `gtsave(...)` with render params; it adds no
        # border of any kind, so a candidate using it alone (without a
        # separate `frame(gt)` call or explicit border options) renders
        # genuinely frameless.
        or re.search(r"\bframe\s*\(", source)
        # A genuine box needs all FOUR sides ACTIVELY set (not just
        # mentioned, and not just left/right) -- a candidate that only
        # sets e.g. table_border_left_style="solid" has one ruled edge,
        # not an enclosing frame, and one that sets all four to
        # style="none" (or a zero-width) mentions every side without
        # rendering any of them.
        or _tab_options_frame_active(source)
    )
    striping_present = bool(
        _opt_row_striping_enabled(source)
        # NOT `row_striping_background_color=` alone -- per GT's own docs,
        # `opt_row_striping()`/this flag is what actually turns body
        # striping on; the background color kwarg only configures WHICH
        # color a stripe would use if enabled, with no visual effect by
        # itself (striping defaults to off).
        or re.search(r"row_striping_include_table_body\s*=\s*True", source)
        or _bare_call_blocks(source, "stripe")  # runtime stripe(gt) helper
    )
    # NOTE: keyword-OR-positional presence (a valid `.tab_header("Sales",
    # "FY 2026")` supplies both fields positionally, with no `title=`/
    # `subtitle=` keyword text anywhere in the block).
    caption_present = _tab_header_arg_present(source, "subtitle")
    title_present = _tab_header_arg_present(source, "title")
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
        "stub_tint_present": _stub_tint_present(source),
        "columns_signature": _columns_signature(source),
        "fmt_signature": _fmt_signature(source),
        "domain_signature": _domain_signature(source),
        "color_signature": _color_signature(source),
        "data_hash": data_hash,
        # Comparator Tier-1 additions (09-ground-truth-comparator.md §6):
        # tab_spanner_delim(...) also renders column-group spanners (from a
        # delimiter in column names), not just an explicit tab_spanner(...)
        # call -- both count as "a spanner is present."
        "spanner_present": bool(
            _call_arg_blocks(source, "tab_spanner")
            or _call_arg_blocks(source, "tab_spanner_delim")
        ),
        "color_mechanics": _color_mechanics(source),
        "render_params": _render_params(source),
        # Distinguishes "no render call that plausibly wrote table.png" (a
        # hard failure -- see `_render_call_targets_table_png`) from "a
        # render call exists but its params are unresolved" (e.g. a
        # **kwargs expansion -- genuinely unverifiable, benefit of the
        # doubt). `_render_params` returns `{}` for both that case AND the
        # hard-failure case, so this is checked independently.
        "render_call_present": _render_call_targets_table_png(source),
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
