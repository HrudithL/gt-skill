#!/usr/bin/env python3
"""The ground-truth comparator — scores a candidate `table.py` against its
prompt's ground truth, via a HYBRID of deterministic checks and one grounded
LLM judge call.

Per ``.planning/10-hybrid-comparator.md`` (supersedes ``09``'s "no LLM
anywhere" lock): most checks are still regex/AST parsing (Tier 1,
``runner.convergence``), execution + value comparison (Tier 2,
``runner.execution_tier``), or a lookup against the ground truth's own
authored metadata (§5) — these have exactly one provably-correct answer and
stay fully deterministic. A handful of checks are instead about wording or
an open-ended space of valid choices (column-label clarity, caption/title/
subtitle quality, column order, palette taste) — those are computed by one
batched call to ``runner.judge.judge()`` (a vision-capable LLM call, see
that module) and read out of the single combined result ``compare()``
stashes in ``meta["_judge_result"]`` before running the check functions.
Every check function still has the exact same signature and every
judge-backed check degrades to the existing ``_na()`` pattern (0/0,
excluded from the denominator) if the judge is unavailable or the
dimension doesn't apply to this comparison — nothing ever silently passes
or fails. ``CheckResult.tier`` ("mechanical" or "judge") makes the
distinction visible in the printed report, not just in code comments.

Report shape: a 0–114 total = Data-compliance (0–53) + Formatting-compliance
(0–61), plus one line per check naming its tier, what passed/failed, its
point value, and why (§7).
"""

from __future__ import annotations

import ast
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from runner import convergence, execution_tier
from runner import judge as judge_module

# ----------------------------------------------------------------------- #
# fingerprint + metadata loading
# ----------------------------------------------------------------------- #

# Default metadata values for a ground truth that leaves one of the §5
# blocks out entirely (e.g. a table with no explicit prompt instructions to
# check) -- absence must read as "nothing to check", never as an error.
_METADATA_DEFAULTS = {
    "LABEL_SYNONYMS": {},
    "REQUIRED_INSTRUCTIONS": {},
    "CAPTION_KEYWORDS": {},
    "CANONICAL_MEASURES": {"colored": [], "hero_uncolored": []},
    "SEMANTIC_TYPES": {},
}


# ----------------------------------------------------------------------- #
# Tier-1 compatibility shim -- see the long comment on `build_fingerprint`
# below for why this exists. Every function here is a straight, unmodified
# port of the closed `gtc/comparator` branch's OWN `runner/convergence.py`
# logic (verified against `git show gtc/comparator:runner/convergence.py`),
# relocated into comparator.py rather than into convergence.py itself
# (a hard non-goal for this slice) -- it reuses only low-level parsing
# primitives convergence.py already exposes and comparator.py already
# reaches into directly elsewhere in this file (e.g. `convergence.
# _split_top_level`/`_kwarg_value`/`_scan_balanced_paren` in
# `_summary_row_style_is_distinctive` below).
# ----------------------------------------------------------------------- #

# The closed `gtc/comparator` branch's OWN `_FAMILY_HEXES` added a second
# "accent"/"accent_tint" hex pair per family (the great-tables-house skill's
# brighter, more-saturated heading-band tier, e.g. navy's `#1B5A85`/
# `#C9E0F0` -- `gtcars_hp_price.py`'s own heading band uses `#C9E0F0`
# exactly) ON TOP OF convergence.py's base washed-tier pair, discovered as a
# real classification bug during that branch's own review ("without the
# accent/accent_tint hexes here, a house-format-compliant band misclassifies
# as its nearest neutral instead of its actual hue family"). The version of
# `_FAMILY_HEXES` merged to `gtc/root` today only has the base pair -- this
# extends it locally (layered on top of convergence.py's own table, not a
# replacement) so `_classify_hue_extended` below classifies an accent-tier
# band hex correctly without touching convergence.py itself.
_ACCENT_TIER_HEXES: dict[str, list[str]] = {
    "navy": ["#1B5A85", "#C9E0F0"],
    "forest": ["#2E7350", "#CFEAD9"],
    "oxblood": ["#A23A3A", "#F4D6D6"],
    "espresso": ["#8A6238", "#EEDFC7"],
    "ochre": ["#B8912E", "#F6E8BE"],
    "tan": ["#9C8258", "#EFE3CE"],
}
_EXTENDED_FAMILY_HEXES: dict[str, list[str]] = {
    family: [*hexes, *_ACCENT_TIER_HEXES.get(family, [])]
    for family, hexes in convergence._FAMILY_HEXES.items()
}


def _classify_hue_extended(hexstr: str | None) -> str:
    """Like `convergence._classify_hue`, but against `_EXTENDED_FAMILY_HEXES`
    (base + accent tier) instead of convergence.py's base-only table --
    nearest-neighbour in RGB, ported from the closed branch's fixed
    `_classify_hue`. `build_fingerprint()` below recomputes
    `tier1["heading_band_hue"]` with this, from `tier1["heading_band_hex"]`
    (still present, unchanged), rather than trusting convergence.py's own
    `heading_band_hue` value (computed against the narrower base-only
    table).
    """
    if not hexstr:
        return "unknown"
    rgb = convergence._hex_to_rgb(hexstr)
    if rgb is None:
        return "unknown"
    best_family, best_dist = "unknown", float("inf")
    for family, hexes in _EXTENDED_FAMILY_HEXES.items():
        for ref in hexes:
            rr = convergence._hex_to_rgb(ref)
            if rr is None:
                continue
            dist = sum((a - b) ** 2 for a, b in zip(rgb, rr))
            if dist < best_dist:
                best_dist, best_family = dist, family
    return best_family


# Flattened, upper-cased hex membership set for "is this quiet-surface fill
# one of the recognized neutral/washed reference colors" -- derived from the
# EXTENDED table above (base + accent tier), same reasoning as
# `_classify_hue_extended`: a literal accent-tier hex used as a stub tint
# must be recognized too, not just the base washed tier.
_ALLOWED_TINT_HEXES = {h.upper() for hexes in _EXTENDED_FAMILY_HEXES.values() for h in hexes}

# A whole-string literal (optionally string-prefixed, `b`/`r`/`u`/`f` in any
# combination/case) -- single or triple quoted. Ported from the closed
# branch, with an added capturing group around the prefix (see
# `_is_static_string_literal` just below) so an `f`-prefixed string can be
# told apart from a plain one; used only to tell "a literal path string"
# from "a variable/expression" when checking a render call's target path.
_STRING_LITERAL_RE = re.compile(r"^([bBrRuUfF]{0,2})('''|\"\"\"|'|\")(.*)\2$", re.S)


def _is_static_string_literal(value_text: str) -> bool:
    """True if `value_text` is a plain string literal whose rendered text is
    STATICALLY known -- i.e. NOT an f-string with a real `{...}` placeholder.

    Codex round-1 finding: `_STRING_LITERAL_RE` alone accepts an f-string
    like `f"{stem}.png"` as "a string literal" (the `f` prefix is in its
    allowed prefix set), so `_blocks_target_table_png` below classified a
    genuinely dynamic, interpolated path as a resolved literal and then
    correctly rejected it as not equal to `"table.png"` -- denying the
    benefit of the doubt this function's OWN docstring says a non-literal
    path should get. A bare `f"table.png"` with no `{}` at all (a harmless,
    no-op `f`-prefix) is still statically resolvable and stays literal.
    """
    m = _STRING_LITERAL_RE.match(value_text.strip())
    if not m:
        return False
    prefix, _quote, body = m.group(1), m.group(2), m.group(3)
    if "f" in prefix.lower() and re.search(r"(?<!\{)\{(?!\{)", body):
        return False
    return True


def _is_effectively_transparent(color: str) -> bool:
    """True if a CSS color literal renders with effectively zero opacity.

    Beyond the literal keywords `transparent`/`none`/empty, also catches an
    `rgba(...)`/`rgb(...)` with a zero alpha channel and an 8-digit
    `#RRGGBBAA` / 4-digit `#RGBA` hex whose alpha byte/nibble is zero -- all
    of these render NO visible fill, same as the literal keywords. Ported
    verbatim from the closed `gtc/comparator` branch's `convergence.py`
    (that name doesn't exist in the version of `convergence.py` actually
    merged to `gtc/root` today -- see the shim-section comment above).
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


def _stub_tint_present(source: str) -> bool:
    """True if a VISIBLE stub tint is applied, by EITHER accepted mechanism.

    The `stub_tint(gt, *, hue)` runtime helper is one way (detected via
    convergence.py's own still-present `_find_stub_tint_hue`); a literal
    `tab_style(style=style.fill(color=...), locations=loc.stub())` call is
    the other (what `towny_growth_trends.py` actually uses) -- both are
    equally valid per the outcome-only scoring rule. A `style.fill(color=...)`
    call only counts if its color is genuinely visible and is one of the
    recognized neutral/washed reference hexes (`_ALLOWED_TINT_HEXES`) when
    it's a literal hex -- ported verbatim from the closed branch (the
    combined `stub_tint_present` field itself doesn't exist in the version
    of `convergence.py` merged to `gtc/root` today; only the narrower
    `stub_tint_hue` does).
    """
    if convergence._find_stub_tint_hue(source) is not None:
        return True
    for block in convergence._call_arg_blocks(source, "tab_style"):
        loc_val = convergence._kwarg_value(block, "locations")
        if loc_val is None:
            positionals = [
                p for p in convergence._split_top_level(block) if not re.match(r"[A-Za-z_]\w*\s*=", p)
            ]
            loc_val = positionals[1] if len(positionals) >= 2 else None
        if loc_val is None or not re.search(r"loc\s*\.\s*stub\s*\(", loc_val):
            continue
        style_val = convergence._kwarg_value(block, "style")
        if style_val is None:
            positionals = [
                p for p in convergence._split_top_level(block) if not re.match(r"[A-Za-z_]\w*\s*=", p)
            ]
            style_val = positionals[0] if positionals else None
        if not style_val:
            continue
        fm = re.search(r"style\s*\.\s*fill\s*\(", style_val)
        if not fm:
            continue
        close_idx = convergence._scan_balanced_paren(style_val, fm.end() - 1)
        fill_block = style_val[fm.end():close_idx] if close_idx is not None else ""
        color_val = convergence._kwarg_value(fill_block, "color")
        if color_val is None:
            fill_positionals = [
                p for p in convergence._split_top_level(fill_block) if not re.match(r"[A-Za-z_]\w*\s*=", p)
            ]
            color_val = fill_positionals[0] if fill_positionals else None
        unquoted_color = convergence._unquote(color_val) if color_val else None
        if unquoted_color is not None:
            stripped = unquoted_color.strip()
            if _is_effectively_transparent(stripped):
                continue
            if stripped.startswith("#") and stripped.upper() not in _ALLOWED_TINT_HEXES:
                continue
        return True
    return False


def _blocks_target_table_png(blocks: list[str], path_kwarg: str, path_index: int) -> bool:
    """True if any call block's path argument plausibly targets `table.png`.

    A literal path only counts when `convergence._targets_table_png`
    confirms it; a non-literal path (a variable, an f-string) can't be
    proven wrong from source text alone and gets the benefit of the doubt.
    Ported verbatim from the closed branch.
    """
    for b in blocks:
        path_val = convergence._kwarg_value(b, path_kwarg)
        if path_val is None:
            positionals = [
                p for p in convergence._split_top_level_quoted(b) if not re.match(r"[A-Za-z_]\w*\s*=", p)
            ]
            path_val = positionals[path_index] if len(positionals) > path_index else None
        if path_val is None:
            continue
        if not _is_static_string_literal(path_val.strip()):
            return True  # non-literal -- can't prove it's the wrong target
        if convergence._targets_table_png(path_val):
            return True
    return False


def _render_call_present(source: str) -> bool:
    """True if some `gtsave`/`finalize` call plausibly produced the
    harness's mandated `table.png` artifact. Ported verbatim from the
    closed branch (`render_call_present` itself doesn't exist in the
    version of `convergence.py` merged to `gtc/root` today).
    """
    if _blocks_target_table_png(convergence._call_arg_blocks(source, "gtsave"), "file", 0):
        return True
    return _blocks_target_table_png(convergence._bare_call_blocks(source, "finalize"), "path", 1)


def _tab_header_kwarg_present(source: str, kwarg: str) -> bool:
    """True if the LAST `tab_header(...)` call in `source` sets `kwarg`
    (`"title"` or `"subtitle"`) -- via either the keyword form or the
    documented positional form (`tab_header("Title", "Subtitle")`, where
    title is positional arg 0 and subtitle is arg 1).

    Codex round-1 finding: `convergence.parse_design_choices`'s own
    `title_present`/`caption_present` fields (the latter is convergence.py's
    name for "subtitle is present") have two bugs: (a) they only ever
    recognize the `title=`/`subtitle=` keyword form via a bare regex search,
    so a positional `tab_header("Title", "Subtitle")` call reads as
    completely absent; and (b) they `any()` across EVERY `tab_header(...)`
    call in the source, rather than using only the LAST one -- but
    great_tables REPLACES the whole header per call rather than merging
    fields across calls, so an earlier call's subtitle can wrongly "count"
    even after a later call replaces the header without one (or vice
    versa). `convergence._tab_header_text` (used elsewhere in this file for
    `title_text`/`subtitle_text`) already gets both of these right for TEXT
    EXTRACTION, but returns `None` for a genuinely present-but-DYNAMIC value
    (a variable, an unresolved f-string) -- which must still count as
    "present" for THIS existence check, so this checks for the argument's
    presence (keyword or positional slot occupied), not its resolved text,
    reusing `convergence._TAB_HEADER_POSITIONAL_INDEX` (still present) for
    the positional-slot mapping.
    """
    blocks = convergence._call_arg_blocks(source, "tab_header")
    if not blocks:
        return False
    block = blocks[-1]
    if convergence._kwarg_value(block, kwarg) is not None:
        return True
    idx = convergence._TAB_HEADER_POSITIONAL_INDEX.get(kwarg)
    if idx is None:
        return False
    positionals = [
        p for p in convergence._split_top_level_quoted(block) if not re.match(r"[A-Za-z_]\w*\s*=", p)
    ]
    return idx < len(positionals)


# convergence.py's own `_DATA_COLOR_DEFAULTS` covers na_color/truncate/
# autocolor_text only (current convergence.py never checks `reverse`, so it
# never needed a default for it). `reverse` DOES have a universal
# great_tables default when omitted (`False`) even though it has no
# universal CORRECT value (see check_color_mechanics' own docstring) --
# layered on top locally rather than added to convergence.py's constant.
_DATA_COLOR_DEFAULTS_EXT = {**convergence._DATA_COLOR_DEFAULTS, "reverse": "False"}


def _kwarg_or_default_positional(block: str, name: str, positionals: list[str], index: int) -> str | None:
    """Like `convergence._kwarg_or_default(block, name)`, but ALSO falls
    back to `positionals[index]` when the keyword isn't found -- the
    version of `_kwarg_or_default` merged to `gtc/root` today only supports
    the keyword form, not this positional fallback the closed branch's
    `_color_mechanics` needs (a `.data_color("sales", None, "Blues", [0,
    10], "red", None, False, False, True)` call sets `na_color`/
    `autocolor_text`/`truncate` purely positionally).
    """
    if any(p.strip().startswith("**") for p in convergence._split_top_level_quoted(block)):
        return None
    val = convergence._kwarg_value(block, name)
    if val is None and len(positionals) > index:
        val = positionals[index]
    v = convergence._unquote(val)
    if v is None or v == "None":
        return _DATA_COLOR_DEFAULTS_EXT[name]
    return v


def _strip_docstrings(source: str) -> str:
    """Blank out every module/class/function DOCSTRING's text in `source`
    (replacing every non-newline character in its span with a space, so
    every other character's line/column position is preserved exactly --
    nothing downstream that relies on relative source order shifts).

    Codex round-1 finding: `convergence._strip_line_comments` (already
    applied below) only strips `#`-comments, not string content -- a
    docstring that mentions a literal `.data_color(...)`/`heatmap(...)`
    example (e.g. explaining a pattern, or what NOT to do) was scanned as a
    REAL call by the regex-based extraction below, corrupting the colored-
    measure count and every check that depends on it (palette, domain,
    striping, hue-collision, band-harmonization). This repo's own checked-in
    `sp500_monthly_performance.py` ground truth avoids literally spelling
    `.data_color(` in its docstring specifically to dodge this bug -- a
    workaround for it, not a fix.

    Uses the AST (not a regex) to find genuine docstring nodes precisely:
    only the first statement of a module/class/function body, when it's a
    bare string-literal expression -- Python's own definition of a
    docstring. An ordinary string ARGUMENT (e.g. a triple-quoted title=
    value) is never in that position, so it's never touched, only real
    docstrings are. Falls back to returning `source` unchanged if it isn't
    parseable (e.g. a broken candidate) -- the regex-based extraction below
    already tolerates that source verbatim, same as before this fix.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return source
    doc_nodes: list[ast.Constant] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(node, "body", None) or []
            if body and isinstance(body[0], ast.Expr):
                val = body[0].value
                if isinstance(val, ast.Constant) and isinstance(val.value, str):
                    doc_nodes.append(val)
    if not doc_nodes:
        return source
    line_starts = [0]
    for line in source.splitlines(keepends=True):
        line_starts.append(line_starts[-1] + len(line))

    def _offset(lineno: int, col: int) -> int:
        return line_starts[lineno - 1] + col

    chars = list(source)
    for node in doc_nodes:
        if node.end_lineno is None or node.end_col_offset is None:
            continue
        start = _offset(node.lineno, node.col_offset)
        end = _offset(node.end_lineno, node.end_col_offset)
        for i in range(start, min(end, len(chars))):
            if chars[i] != "\n":
                chars[i] = " "
    return "".join(chars)


def _palette_of_block_positional(block: str, positionals: list[str]) -> str:
    """Like `convergence._palette_of_block(block)`, but ALSO falls back to
    positional slot 2 (`data_color(columns, rows, palette, domain, ...)`)
    when no `palette=` keyword is present.

    Codex round-1 finding: `convergence._palette_of_block` only recognizes
    the keyword form, so a valid positional call like `data_color(cols,
    None, "RdYlGn", domain)` reads as `"default"` -- which can make the
    sequential/diverging shape check treat a genuinely diverging palette as
    unknown (benefit-of-the-doubt, silently passing a real mismatch), and
    can collapse two DIFFERENT positionally-specified palettes sharing a
    domain into what looks like the same `(palette, domain)` measure for
    the ≤2-ceiling count. Mirrors the positional handling every other
    argument in `_enrich_color_mechanics` already gets.
    """
    literal = convergence._palette_of_block(block)
    if literal != "default":
        return literal
    if convergence._kwarg_value(block, "palette") is not None:
        # An explicit `palette=<list literal>` -- convergence.py's own
        # "custom" classification for a list, not a missing arg -- must
        # not be overridden by falling through to the positional slot.
        return literal
    if len(positionals) > 2:
        pos_val = positionals[2].strip()
        if pos_val and pos_val != "None":
            m = re.match(r"^\[[^\]]*\]$", pos_val)
            if m:
                return "custom"
            unquoted = convergence._unquote(pos_val)
            if unquoted and unquoted != pos_val:  # was actually quoted
                return unquoted
    return literal


def _enrich_color_mechanics(source: str) -> list[dict]:
    """One dict per colored-measure call (`data_color`/`heatmap`), in TRUE
    source order, carrying `columns`/`na_color`/`truncate`/`autocolor_text`
    PLUS `palette`/`domain`/`via_helper`/`kind`/`reverse` -- the per-entry
    fields `check_colored_measure_selection`, `check_sequential_vs_
    diverging`, `check_domain_computation`, `check_hue_collision`,
    `check_band_hue_harmonization`, and `check_color_mechanics` below all
    depend on and were 14-round Codex-reviewed against.

    This is a straight port of the closed `gtc/comparator` branch's OWN
    `convergence._color_mechanics()` (verified via `git show gtc/comparator:
    runner/convergence.py`), relocated here rather than into
    `runner/convergence.py` itself (a hard non-goal for this slice): the
    version of `_color_mechanics()` actually merged to `gtc/root` (developed
    on an independent, differently-scoped branch) only materializes
    `columns`/`na_color`/`truncate`/`autocolor_text` per entry -- it never
    picked up `palette`/`domain`/`via_helper`/`kind`/`reverse`, so every
    colored-measure check below would otherwise silently degrade (e.g. every
    entry's `(palette, domain)` collapsing to the same `(None, None)` pair,
    making a candidate with 5 differently-colored measures misreport as "1
    measure" for the ≤2 ceiling check). `build_fingerprint()` below replaces
    `tier1["color_mechanics"]` with this function's output entirely, using
    only convergence.py's still-present, already-exposed low-level parsing
    primitives -- no change to convergence.py itself.
    """
    source = _strip_docstrings(source)
    source = convergence._strip_line_comments(source)
    var_map = convergence._list_var_map(source)
    entries: list[tuple[int, dict]] = []
    for pos, block in convergence._call_arg_blocks_pos(source, "data_color"):
        # `data_color(columns, rows, palette, domain, ...)` -- shared once so
        # `rows`/`columns`/`domain` positional fallbacks (slots 1/0/3) all
        # line up against the SAME split.
        positionals = [
            p for p in convergence._split_top_level_quoted(block) if not re.match(r"[A-Za-z_]\w*\s*=", p)
        ]
        rows_val = convergence._kwarg_value(block, "rows")
        if rows_val is None and len(positionals) > 1:
            rows_val = positionals[1]
        if rows_val is not None and rows_val.strip() != "None":
            continue
        cols_val = convergence._kwarg_value(block, "columns")
        if cols_val is None:
            cols_val = positionals[0] if positionals else None
        if cols_val is None or cols_val.strip() == "None":
            resolved_columns = None
        else:
            resolved_columns = convergence._resolve_columns_list(cols_val, var_map)
        domain_val = convergence._kwarg_value(block, "domain")
        if domain_val is None and len(positionals) > 3:
            domain_val = positionals[3]
        entries.append((pos, {
            "columns": resolved_columns,
            "palette": _palette_of_block_positional(block, positionals),
            "domain": domain_val,
            # data_color(columns, rows, palette, domain, na_color, alpha,
            # reverse, autocolor_text, truncate) -- positional slots 4/6/7/8.
            "na_color": _kwarg_or_default_positional(block, "na_color", positionals, 4),
            "reverse": _kwarg_or_default_positional(block, "reverse", positionals, 6),
            "truncate": _kwarg_or_default_positional(block, "truncate", positionals, 8),
            "autocolor_text": _kwarg_or_default_positional(block, "autocolor_text", positionals, 7),
            "via_helper": False,
        }))
    for pos, block in convergence._bare_call_blocks_pos(source, "heatmap"):
        entries.append((pos, {
            "columns": convergence._resolve_columns_list(convergence._heatmap_columns_raw(block), var_map),
            "palette": convergence._unquote(convergence._kwarg_value(block, "hue")) or "default",
            "domain": convergence._kwarg_value(block, "domain"),
            "kind": convergence._unquote(convergence._kwarg_value(block, "kind")),
            "na_color": "#808080",
            "truncate": "False",
            "autocolor_text": "True",
            "reverse": "False",
            "via_helper": True,
        }))
    entries.sort(key=lambda e: e[0])
    return [d for _, d in entries]


def build_fingerprint(py_path: Path) -> dict:
    """Tier 1 + Tier 2 fingerprint for one `table.py` (candidate OR ground
    truth — both are built identically, per the spec's "computed the same
    way" instruction).

    Overrides/adds Tier-1 fields (`color_mechanics`, `stub_tint_present`,
    `render_call_present`, `heading_band_hue` when a hex exists,
    `title_present`, `caption_present`) via the compatibility shim just
    above, immediately after `convergence.parse_design_choices()` runs.
    Why: the 23 unchanged checks vendored from the closed `gtc/comparator`
    branch (see this module's docstring) were written and 14-round
    Codex-reviewed against THAT branch's own `runner/convergence.py`, which
    added richer per-entry color-mechanics fields, two extra boolean fields,
    and an extended hue-family hex table as part of the SAME PR. `gtc/root`'s
    actual `convergence.py` was developed independently (a different,
    differently-scoped branch) and doesn't carry those additions --
    discovered by running this comparator against the real corpus (self-
    comparison silently mis-scored `check_colored_measure_selection`/
    `check_hue_collision`/`check_domain_computation`/`check_stub_tint`/
    `check_render_mechanics`/`check_band_hue_harmonization` without this
    shim). `title_present`/`caption_present` were separately found (Codex
    round-1) to have their own, unrelated bugs (keyword-only, all-calls-not-
    last-call) even though they aren't part of the vendoring-skew story --
    fixed here for the same "keep the compatibility shim" reason: `runner/
    convergence.py` is a hard non-goal for this slice either way, so the
    fix lives here instead, built only from primitives convergence.py
    already exposes.
    """
    source = py_path.read_text()
    tier1 = convergence.parse_design_choices(source)
    tier1["color_mechanics"] = _enrich_color_mechanics(source)
    tier1["stub_tint_present"] = _stub_tint_present(source)
    tier1["render_call_present"] = _render_call_present(source)
    # Codex round-1 finding: convergence.py's own `title_present`/
    # `caption_present` (subtitle) only recognize the keyword form and
    # `any()` across every `tab_header(...)` call instead of just the last
    # one -- see `_tab_header_kwarg_present`'s docstring.
    tier1["title_present"] = _tab_header_kwarg_present(source, "title")
    tier1["caption_present"] = _tab_header_kwarg_present(source, "subtitle")
    # Codex round-1 finding: only reclassify when an explicit band HEX
    # exists. `convergence.parse_design_choices` also derives
    # `heading_band_hue` from the runtime `band(gt, shade=..., hue=...)`
    # HELPER when no literal hex is present (`heading_band_hex` is `None`
    # in that case) -- that helper-derived hue is already correct (parsed
    # directly from the helper's own `hue=` argument, not classified from a
    # color), and unconditionally re-deriving it from a `None` hex here
    # collapsed it to `"unknown"`, wrongly costing a helper-based candidate
    # its hue-harmonization points. Only override when there's an actual
    # hex to reclassify against the extended table.
    if tier1.get("heading_band_hex"):
        tier1["heading_band_hue"] = _classify_hue_extended(tier1["heading_band_hex"])
    tier2 = execution_tier.exec_table(py_path)
    return {"tier1": tier1, "tier2": tier2, "source": source, "path": py_path}


def load_ground_truth_metadata(gt_path: Path) -> dict:
    """Read a ground truth's §5 metadata literals via AST parsing -- no
    execution of the module at all.

    The §5 design constraint is that this metadata is ALWAYS a plain
    dict/list literal assignment (no computation) specifically so it's both
    a human-reviewable answer key and mechanically loadable without exec
    risk -- `ast.literal_eval` on each matching top-level assignment's value
    node honors that constraint directly, rather than actually importing
    and running the ground-truth script (which previously executed the
    WHOLE module, including its trailing `gt.gtsave(...)`/`finalize(...)`
    call -- silently re-rendering and overwriting the checked-in PNG on
    every single comparison, and requiring a full rendering toolchain just
    to read 5 dicts, which could crash comparison entirely in a headless
    evaluator without one).

    Missing names default per `_METADATA_DEFAULTS` — a ground truth that
    doesn't need `REQUIRED_INSTRUCTIONS` (say) simply omits it, and that
    must read as "no instructions to check," not as a loader error. A
    matching name whose value ISN'T a plain literal (violates the §5
    constraint) is likewise treated as absent rather than raising.
    """
    tree = ast.parse(gt_path.read_text(), filename=str(gt_path))
    found: dict[str, object] = {}
    for node in tree.body:
        # A type-annotated assignment (`SEMANTIC_TYPES: dict[str, str] =
        # {...}`) is `ast.AnnAssign`, not `ast.Assign` -- its target is a
        # single `Name` (not a `targets` list), and its value can be
        # `None` for a bare annotation with no assignment at all
        # (`SEMANTIC_TYPES: dict`), which isn't literal-evaluable.
        if isinstance(node, ast.AnnAssign):
            if node.value is None or not isinstance(node.target, ast.Name):
                continue
            targets = [node.target]
            value = node.value
        elif isinstance(node, ast.Assign):
            targets = node.targets
            value = node.value
        else:
            continue
        for target in targets:
            if isinstance(target, ast.Name) and target.id in _METADATA_DEFAULTS:
                try:
                    found[target.id] = ast.literal_eval(value)
                except (ValueError, SyntaxError):
                    pass
    return {name: found.get(name, default) for name, default in _METADATA_DEFAULTS.items()}


# ----------------------------------------------------------------------- #
# small shared helpers
# ----------------------------------------------------------------------- #

def _visible_columns(fp: dict) -> set[str]:
    """Source columns actually present in the rendered `_tbl_data`, minus
    ones hidden via `cols_hide(...)` — the stub/group columns ARE included
    (they render, just not as ordinary body columns).
    """
    tier2 = fp["tier2"]
    if not tier2.get("ok"):
        return set()
    return set(tier2.get("columns", {}).keys()) - set(tier2.get("hidden_columns") or [])


def _mechanics_columns(entry: dict, fp: dict) -> list[str]:
    """The columns a `color_mechanics` entry actually targets.

    `entry["columns"] is None` is Tier 1's explicit sentinel for a literal
    `.data_color(...)` call whose `columns` was omitted or `None` (great_
    tables applies it to EVERY column in that case) -- Tier 1 can't
    enumerate the real schema itself (it only sees static source text), so
    this expands the sentinel against `fp`'s own Tier-2 VISIBLE columns
    (excluding the stub/group, which data_color never targets) at scoring
    time, when both tiers are available together. Without this, an
    all-columns `data_color(...)` call reported an empty column list,
    making the candidate look like it colored nothing at all.
    """
    cols = entry.get("columns")
    if cols is not None:
        return cols
    tier2 = fp["tier2"]
    visible = _visible_columns(fp) - {tier2.get("stub_column"), tier2.get("group_column")}
    return sorted(visible)


def _n_rows(fp: dict) -> int | None:
    tier2 = fp["tier2"]
    return tier2.get("n_rows") if tier2.get("ok") else None


def _measure_signedness(fp: dict, columns: list[str]) -> str | None:
    """"diverging" (mixed sign), "sequential" (all one sign), or None (no
    usable values) for the given columns' ACTUAL values in `fp`.
    """
    tier2 = fp["tier2"]
    if not tier2.get("ok"):
        return None
    vals: list[float] = []
    for col in columns:
        for v in tier2.get("columns", {}).get(col, []):
            if v is None:
                continue
            # Attempt numeric coercion even for a string value -- the Tier-2
            # JSON serializer falls back to `str(v)` for a type it doesn't
            # recognize (e.g. `decimal.Decimal`), so a genuinely numeric
            # colored column can arrive here as numeric-looking strings. A
            # real categorical string ("On Track") still raises ValueError
            # and is skipped exactly as before -- this only WIDENS what
            # counts as numeric, never narrows it.
            try:
                vals.append(float(v))
            except (TypeError, ValueError):
                continue
    if not vals:
        return None
    has_pos = any(v > 0 for v in vals)
    has_neg = any(v < 0 for v in vals)
    return "diverging" if has_pos and has_neg else "sequential"


def _actual_value_range(fp: dict, columns: list[str]) -> tuple[float, float] | None:
    """(min, max) of the given columns' actual numeric Tier-2 values, or
    `None` if there are no usable values -- used to verify a literal
    sequential domain actually COVERS the real data instead of just being
    well-formed.
    """
    tier2 = fp["tier2"]
    if not tier2.get("ok"):
        return None
    vals: list[float] = []
    for col in columns:
        for v in tier2.get("columns", {}).get(col, []):
            if v is None:
                continue
            try:
                vals.append(float(v))
            except (TypeError, ValueError):
                continue
    if not vals:
        return None
    return min(vals), max(vals)


# The full standard ColorBrewer diverging/sequential name sets (not just
# the house skill's own narrower prescribed subset -- RdYlGn/RdBu/PuOr
# diverging, Blues/Greens/Reds/Oranges sequential) -- a candidate using
# any OTHER standard name (e.g. `Spectral`, a diverging palette, on
# all-positive data) previously fell through to "unknown" and got the
# same benefit-of-the-doubt as a genuinely unclassifiable custom hex-list,
# silently passing a real sequential/diverging mismatch.
_DIVERGING_PALETTES = {
    "brbg", "piyg", "prgn", "puor", "rdbu", "rdgy", "rdylbu", "rdylgn", "spectral",
}
_SEQUENTIAL_PALETTES = {
    "blues", "bugn", "bupu", "gnbu", "greens", "greys", "oranges", "orrd",
    "pubu", "pubugn", "purd", "purples", "rdpu", "reds", "ylgn", "ylgnbu",
    "ylorbr", "ylorrd",
}


def _palette_kind(palette: str | None) -> str:
    """"diverging"/"sequential" for a RECOGNIZED palette name, else
    "unknown" -- never assumed sequential by default.

    A custom diverging palette expressed as a literal hex-list (e.g. the
    repo's own `corpus/heatmap/good_table.py` red-white-green gradient) is
    not a bare palette NAME at all, so it can't match either known set --
    treating that as "unknown" (which `check_sequential_vs_diverging`
    already gives the benefit of the doubt) rather than defaulting it to
    "sequential" avoids penalizing a genuinely diverging custom palette for
    not being one of the standard ColorBrewer names this function
    recognizes.
    """
    if not palette:
        return "unknown"
    p = palette.strip().lower()
    if p in _DIVERGING_PALETTES:
        return "diverging"
    if p in _SEQUENTIAL_PALETTES:
        return "sequential"
    return "unknown"


def _parse_columns_signature_labels(columns_signature: str) -> dict[str, str]:
    """`{source column -> rendered label}` from Tier 1's `columns_signature`
    string (format `label:<col>=<label>|hide:<col>|...`, `|`-joined,
    produced by `convergence._columns_signature`).
    """
    out: dict[str, str] = {}
    if not columns_signature or columns_signature == "(unknown)":
        return out
    for token in columns_signature.split("|"):
        if token.startswith("label:"):
            body = token[len("label:"):]
            if "=" in body:
                col, label = body.split("=", 1)
                out[col] = label
    return out


def _round_points(fraction: float, possible: int) -> int:
    """`fraction` (0..1) of `possible` points, rounded to the nearest int,
    clamped to `[0, possible]` (guards float noise like 1.0000000002).
    """
    return max(0, min(possible, round(fraction * possible)))


# ----------------------------------------------------------------------- #
# check result + registry
# ----------------------------------------------------------------------- #

@dataclass
class CheckResult:
    name: str
    points_possible: int
    points_earned: int
    passed: bool
    detail: str
    # "mechanical" (regex/AST/execution -- provably correct) or "judge" (the
    # LLM call scored this dimension). Defaults to "mechanical" so every
    # pre-existing positional `CheckResult(...)` call site in this file
    # (there are dozens) needs no change -- only the 2 moved checks and 5
    # new judge-backed checks pass `tier="judge"` explicitly.
    tier: str = "mechanical"


CheckFn = Callable[[dict, dict, dict], CheckResult]


def _na(name: str, detail: str, tier: str = "mechanical") -> CheckResult:
    """A check with nothing to grade this run (e.g. an optional
    REQUIRED_INSTRUCTIONS key the prompt never asked for) — contributes 0 to
    BOTH earned and possible, so the report's denominator shrinks instead of
    silently awarding or docking points for something that was never asked.
    """
    return CheckResult(name, 0, 0, True, detail, tier=tier)


def _judge_dimension_check(meta: dict, dimension_key: str, name: str, points: int) -> CheckResult:
    """Shared body for every judge-backed check (the 2 moved checks + 5 new
    ones): look up ``dimension_key`` in the single combined judge result
    ``compare()`` stashes in ``meta["_judge_result"]`` (a
    ``dict[str, judge_module.JudgeDimension]``, see that function), convert
    ``.score`` (1-5) to ``points`` via the same ``_round_points`` helper
    every mechanical check already uses, and degrade to the existing
    ``_na()`` pattern when the dimension isn't applicable -- whether because
    the judge itself is unavailable (``JudgeDimension.rationale`` then
    starts with the ``"judge unavailable: "`` prefix -- see
    ``runner.judge.judge()``'s docstring) or because this specific
    comparison genuinely has nothing to judge (e.g. no grouping to assess
    quality of). Either way this reads as N/A (0/0), never a silent
    pass/fail -- ``dim.rationale`` (surfaced verbatim in the detail) is how
    a report reader tells those two cases apart.
    """
    judge_result = meta.get("_judge_result") or {}
    dim = judge_result.get(dimension_key)
    if dim is None or not dim.applicable:
        reason = dim.rationale if dim is not None else "judge result missing for this dimension"
        return _na(name, reason, tier="judge")
    pts = _round_points(dim.score / 5, points)
    return CheckResult(name, points, pts, pts == points, f"judge score {dim.score}/5 -- {dim.rationale}", tier="judge")


# ----------------------------------------------------------------------- #
# Data-compliance checks (§8, 50 pts)
# ----------------------------------------------------------------------- #

def check_row_selection_identity(cand: dict, truth: dict, meta: dict) -> CheckResult:
    name = "Row/entity selection identity"
    truth_ids = truth["tier2"].get("row_ids") if truth["tier2"].get("ok") else None
    cand_ids = cand["tier2"].get("row_ids") if cand["tier2"].get("ok") else None
    if truth_ids is None:
        return _na(name, "ground truth has no stub column; row identity not verifiable")
    if cand_ids is None:
        return CheckResult(name, 10, 0, False, "candidate has no stub column; row selection unverifiable")
    result = execution_tier.row_set_identity(
        cand_ids, truth_ids,
        candidate_group_ids=cand["tier2"].get("row_group_ids"),
        truth_group_ids=truth["tier2"].get("row_group_ids"),
    )
    if result["exact"]:
        return CheckResult(name, 10, 10, True, "candidate's row set exactly matches the ground truth's")
    p, r = result["precision"] or 0.0, result["recall"] or 0.0
    f1 = (2 * p * r / (p + r)) if (p + r) > 0 else 0.0
    pts = _round_points(f1, 10)
    return CheckResult(
        name, 10, pts, False,
        f"row set mismatch (precision={p:.2f}, recall={r:.2f}); "
        f"missing={result['truth_only'][:5]}, extra={result['candidate_only'][:5]}",
    )


def check_computed_value_correctness(cand: dict, truth: dict, meta: dict) -> CheckResult:
    name = "Computed/derived value correctness"
    measures = list(dict.fromkeys(
        meta["CANONICAL_MEASURES"].get("colored", []) + meta["CANONICAL_MEASURES"].get("hero_uncolored", [])
    ))
    if not measures:
        return _na(name, "ground truth declares no CANONICAL_MEASURES to verify")
    if not cand["tier2"].get("ok"):
        return CheckResult(name, 10, 0, False, f"candidate failed to execute: {cand['tier2'].get('error')}")
    matched, missing = [], []
    for m in measures:
        found = execution_tier.match_measure_by_value(cand["tier2"], truth["tier2"], m)
        (matched if found else missing).append(m)
    pts = _round_points(len(matched) / len(measures), 10)
    detail = f"{len(matched)}/{len(measures)} canonical measures have a value-matching candidate column"
    if missing:
        detail += f"; unmatched: {missing}"
    return CheckResult(name, 10, pts, len(missing) == 0, detail)


def _any_colored_column_matches(cand_tier2: dict, truth_tier2: dict, colored_cols: set[str], truth_col: str) -> bool:
    """True if ANY column in `colored_cols` value-matches `truth_col`
    against the ground truth, at or above the standard match threshold.

    Deliberately does NOT use `match_measure_by_value` here: that function
    picks the SINGLE highest-scoring (leftmost-tied) column across ALL
    visible candidate columns. When two columns tie on a perfect value
    match and only the LATER one is actually colored, its leftmost tie-
    break would return the EARLIER, uncolored column -- silently missing
    the colored, equally-matching target and reporting the measure as
    uncolored despite a real colored match existing. Checking every
    colored column independently answers "is this measure covered by SOME
    colored column", not "does the single tie-broken winner happen to be
    colored".
    """
    for col in colored_cols:
        frac = execution_tier.column_match_fraction(cand_tier2, truth_tier2, col, truth_col)
        if frac is not None and frac >= execution_tier._MATCH_THRESHOLD:
            return True
    return False


def _truth_requires_color(meta: dict) -> bool:
    """True if the ground truth's own §5 metadata declares at least one
    canonical colored measure -- the authoritative "was coloring actually
    required here" signal, same source `check_colored_measure_selection`
    already uses for its own identity check.
    """
    return bool(meta["CANONICAL_MEASURES"].get("colored"))


def check_colored_measure_selection(cand: dict, truth: dict, meta: dict) -> CheckResult:
    name = "Colored-measure selection (≤2 ceiling + right measure(s))"
    cand_mechanics = cand["tier1"].get("color_mechanics", [])
    # Count DISTINCT (palette, domain) pairs as "measures", not raw
    # .data_color()/heatmap() CALLS -- the same conceptual measure applied
    # via multiple calls that share a palette+domain (e.g. one call per
    # facet of the same shared scale) is one measure, not N, and must not
    # be rejected as exceeding the ≤2 ceiling.
    n_measures = len({(m.get("palette"), m.get("domain")) for m in cand_mechanics})
    ceiling_ok = n_measures <= 2
    ceiling_pts = 2 if ceiling_ok else 0
    canonical_colored = meta["CANONICAL_MEASURES"].get("colored", [])
    if not canonical_colored:
        identity_pts = 4
        identity_detail = "ground truth declares no canonical colored measures"
    elif not cand["tier2"].get("ok"):
        identity_pts = 0
        identity_detail = f"candidate failed to execute: {cand['tier2'].get('error')}"
    else:
        # A value-matching column only counts if it's actually TARGETED by
        # one of the candidate's own color calls -- otherwise a candidate
        # that merely displays the canonical values uncolored (no
        # data_color/heatmap at all) would be credited with "covering" the
        # colored measure just for showing the right numbers.
        colored_cols = {c for m in cand_mechanics for c in _mechanics_columns(m, cand)}
        covered = 0
        for m in canonical_colored:
            if _any_colored_column_matches(cand["tier2"], truth["tier2"], colored_cols, m):
                covered += 1
        identity_pts = _round_points(covered / len(canonical_colored), 4)
        identity_detail = f"{covered}/{len(canonical_colored)} canonical colored measures covered by a candidate color call"
    pts = ceiling_pts + identity_pts
    detail = f"{'≤2 measures OK' if ceiling_ok else f'{n_measures} colored measures exceeds the ceiling of 2'}; {identity_detail}"
    return CheckResult(name, 6, pts, ceiling_ok and identity_pts == 4, detail)


def check_sequential_vs_diverging(cand: dict, truth: dict, meta: dict) -> CheckResult:
    name = "Sequential-vs-diverging matches data shape"
    mechanics = cand["tier1"].get("color_mechanics", [])
    if not mechanics:
        if _truth_requires_color(meta):
            return CheckResult(name, 5, 0, False, "ground truth requires colored measure(s) but candidate has none")
        return _na(name, "candidate has no colored measures")
    if not cand["tier2"].get("ok"):
        return CheckResult(name, 5, 0, False, f"candidate failed to execute: {cand['tier2'].get('error')}")
    correct, total, notes = 0, 0, []
    for entry in mechanics:
        shape = _measure_signedness(cand, _mechanics_columns(entry, cand))
        if shape is None:
            continue
        total += 1
        if entry.get("via_helper") and entry.get("kind") in ("sequential", "diverging"):
            # heatmap()'s own `kind=` is the declared encoding decision --
            # more authoritative than reverse-engineering it from
            # `palette`, which for a helper entry is the raw semantic
            # `hue=` key (e.g. "neutral"), not a real palette name
            # `_palette_kind` can classify (it would otherwise always read
            # as "unknown" and get benefit-of-the-doubt, even for a
            # `kind="sequential"` call made on genuinely diverging data).
            kind = entry["kind"]
        else:
            kind = _palette_kind(entry.get("palette"))
        if kind == "unknown" or kind == shape:
            correct += 1
        else:
            notes.append(f"{entry.get('columns')}: data is {shape} but palette '{entry.get('palette')}' is {kind}")
    if total == 0:
        return _na(name, "no colored measure had usable numeric values to classify")
    pts = _round_points(correct / total, 5)
    detail = f"{correct}/{total} colored measures use an encoding matching their data shape"
    if notes:
        detail += "; " + "; ".join(notes)
    return CheckResult(name, 5, pts, correct == total, detail)


# `_MATCH_THRESHOLD` still exists on `execution_tier` (reused directly
# below); `_MIN_COVERAGE` does not -- it's local to the closed branch's own
# `group_partition_match`, ported here alongside it.
_MIN_COVERAGE = 0.5


def _group_row_multisets(row_ids: list, group_ids: list) -> dict[Any, Counter]:
    """``{group_id -> Counter[normalized_row_id]}`` -- each group's row-id
    CONTENT, as a multiset (a repeated row id, e.g. "January" appearing
    once per year in a year-grouped table, counts each occurrence rather
    than collapsing to one). Ported verbatim from the closed
    `gtc/comparator` branch's `runner/execution_tier.py` (see
    `_group_partition_match`'s docstring for why this lives here).
    """
    out: dict[Any, Counter] = {}
    for rid, gid in zip(row_ids, group_ids):
        out.setdefault(gid, Counter())[execution_tier.normalize_id(rid)] += 1
    return out


def _group_overlap(a: Counter, b: Counter) -> int:
    """Multiset-intersection size between two row-id counters. Ported
    verbatim from the closed branch."""
    return sum(min(n, b.get(rid, 0)) for rid, n in a.items())


def _group_partition_match(
    candidate_row_ids: list | None,
    candidate_group_ids: list | None,
    truth_row_ids: list | None,
    truth_group_ids: list | None,
) -> dict:
    """Whether the candidate groups rows into the SAME partition as the
    ground truth, by VALUE (row co-membership) -- not by group label text.

    Returns ``{"comparable": bool, "match": bool, "shared_rows": int}``.
    ``comparable=False`` when either side has no grouping at all, or there
    are zero rows shared by identity between the two sides.

    Codex round-1 finding: `check_explicit_instructions`'s `"grouping"`
    branch below calls `execution_tier.group_partition_match(...)`, which
    does not exist in the version of `runner/execution_tier.py` merged to
    `gtc/root` (only in the closed branch's own, differently-scoped
    version) -- so any ground truth that ever sets
    `REQUIRED_INSTRUCTIONS["grouping"]` to a truthy value raised
    `AttributeError` and crashed `compare()` entirely instead of degrading.
    `runner/execution_tier.py` is a hard non-goal for this slice (same as
    `runner/convergence.py`), so this is a straight, self-contained port of
    the closed branch's own `group_partition_match` -- verified via `git
    show gtc/comparator:runner/execution_tier.py` -- built only from
    `execution_tier.normalize_id`/`execution_tier._MATCH_THRESHOLD` (both
    still present) plus the two small helpers just above.

    This is how an explicit "grouped by <concept>" prompt instruction is
    verified: not by checking the candidate's group column LABEL (a
    candidate could call it anything), but by checking that whichever rows
    the ground truth places together in one group, the candidate ALSO
    places together in one group (and vice versa) -- matching by VALUE,
    the same principle used everywhere else in this module. Tolerates
    disagreement on a handful of rows (`execution_tier._MATCH_THRESHOLD`)
    rather than requiring every shared row to agree perfectly.
    """
    if not candidate_group_ids or not truth_group_ids:
        return {"comparable": False, "match": False, "shared_rows": 0}
    cand_groups = _group_row_multisets(candidate_row_ids or [], candidate_group_ids)
    truth_groups = _group_row_multisets(truth_row_ids or [], truth_group_ids)
    if not cand_groups or not truth_groups:
        return {"comparable": False, "match": False, "shared_rows": 0}
    all_cand: Counter = Counter()
    for c in cand_groups.values():
        all_cand.update(c)
    all_truth: Counter = Counter()
    for c in truth_groups.values():
        all_truth.update(c)
    shared_rows = _group_overlap(all_cand, all_truth)
    if not shared_rows:
        return {"comparable": False, "match": False, "shared_rows": 0}
    # A coverage floor: without it, a candidate retaining just ONE row per
    # truth group (each assigned its own distinct, arbitrary label) makes
    # every designation trivially one-to-one, reporting a "match" despite
    # providing no real evidence of correct WITHIN-group co-membership.
    total_truth_rows = len(truth_row_ids or [])
    if total_truth_rows and shared_rows / total_truth_rows < _MIN_COVERAGE:
        return {"comparable": False, "match": False, "shared_rows": shared_rows}
    # For each TRUTH group, whichever candidate group its row CONTENT
    # overlaps with most decides that truth group's designated counterpart.
    # An exact-text id match (e.g. both sides literally use "2015" as the
    # group label) is used directly rather than voting by content, which
    # can be genuinely ambiguous (e.g. every year-group shares the same 12
    # month labels). Sorted iteration on both axes keeps a tied maximum
    # deterministic.
    cand_by_normalized_id = {execution_tier.normalize_id(cg): cg for cg in cand_groups}
    designated: dict[Any, tuple[Any, int]] = {}
    for tg in sorted(truth_groups, key=str):
        truth_rows = truth_groups[tg]
        exact_cg = cand_by_normalized_id.get(execution_tier.normalize_id(tg))
        if exact_cg is not None:
            designated[tg] = (exact_cg, _group_overlap(truth_rows, cand_groups[exact_cg]))
            continue
        best_cg, best_overlap = None, 0
        for cg in sorted(cand_groups, key=str):
            overlap = _group_overlap(truth_rows, cand_groups[cg])
            if overlap > best_overlap:
                best_cg, best_overlap = cg, overlap
        if best_cg is not None:
            designated[tg] = (best_cg, best_overlap)
    # A valid partition match additionally requires the mapping to be
    # one-to-one -- two DIFFERENT truth groups must not designate the SAME
    # candidate group (that would mean the candidate merged two real groups
    # into one).
    one_to_one = len({cg for cg, _ in designated.values()}) == len(designated)
    agree = sum(overlap for _cg, overlap in designated.values())
    match = one_to_one and agree / shared_rows >= execution_tier._MATCH_THRESHOLD
    return {"comparable": True, "match": match, "shared_rows": shared_rows}


def check_explicit_instructions(cand: dict, truth: dict, meta: dict) -> CheckResult:
    name = "Explicit prompt-instruction compliance"
    required = meta["REQUIRED_INSTRUCTIONS"]
    if not required:
        return _na(name, "prompt made no explicit structural demands (REQUIRED_INSTRUCTIONS empty)")
    total = len(required)
    satisfied = 0
    notes = []
    for key, expected in required.items():
        if key == "grouping":
            if not expected:
                # An explicit "must NOT group" instruction -- presence
                # alone is the whole question.
                ok = not bool(cand["tier1"].get("grouping_present"))
            elif not bool(cand["tier1"].get("grouping_present")):
                ok = False
            elif not cand["tier2"].get("ok") or not truth["tier2"].get("ok"):
                ok = False
            else:
                # A required grouping is verified by VALUE -- does the
                # candidate's grouping induce the SAME partition of rows as
                # the ground truth's own (e.g. actually grouped by country,
                # not merely grouped by something) -- not by comparing
                # group-label text, which a candidate could phrase however
                # it likes or apply to an unrelated column.
                result = _group_partition_match(
                    cand["tier2"].get("row_ids"), cand["tier2"].get("row_group_ids"),
                    truth["tier2"].get("row_ids"), truth["tier2"].get("row_group_ids"),
                )
                ok = result["comparable"] and result["match"]
        elif key == "row_count":
            n = _n_rows(cand)
            ok = n == expected
        elif key == "sort":
            # expected is (column, direction) or (column, direction, scope);
            # scope defaults to "global". "within_group" verifies each
            # candidate row-group's OWN segment is independently ordered --
            # for a table required to sort AND group, a single global
            # monotonicity check is either too strict (grouped display
            # legitimately breaks strict cross-group ordering) or, if
            # dropped entirely, too lax (a candidate could shuffle rows
            # WITHIN a group with no penalty at all). Checking order
            # per-group threads both: it doesn't require cross-group
            # monotonicity, but a shuffled group still fails.
            col, direction = expected[0], expected[1]
            scope = expected[2] if len(expected) > 2 else "global"
            if not cand["tier2"].get("ok") or not truth["tier2"].get("ok"):
                ok = False
            else:
                vals = cand["tier2"].get("columns", {}).get(col)
                if not vals:
                    ok = False
                else:
                    # Verify the column's VALUES actually match the ground
                    # truth's (same-named column, default threshold) before
                    # trusting monotonicity -- otherwise a candidate could
                    # satisfy "sorted" by replacing the column with a
                    # constant (every adjacent pair trivially >=/<=) or any
                    # other unrelated monotonic sequence, without showing
                    # the requested measure at all.
                    value_check = execution_tier.computed_value_correctness(cand["tier2"], truth["tier2"], col)
                    if not value_check["passed"]:
                        ok = False
                    else:
                        def _monotonic(seq: list) -> bool:
                            # Generic ordering check (works for numbers,
                            # strings, and ISO-date strings alike) rather
                            # than requiring numeric values. Nulls are
                            # skipped for the comparison itself (sorting
                            # nullable data with nulls first/last is a
                            # valid, common convention) but must be
                            # CONTIGUOUS at one end, not scattered through
                            # otherwise-ordered values.
                            non_null = [v for v in seq if v is not None]
                            if not non_null:
                                return False
                            try:
                                ordered = (
                                    all(a >= b for a, b in zip(non_null, non_null[1:])) if direction == "desc"
                                    else all(a <= b for a, b in zip(non_null, non_null[1:]))
                                )
                            except TypeError:
                                return False
                            if not ordered:
                                return False
                            null_positions = [i for i, v in enumerate(seq) if v is None]
                            if not null_positions:
                                return True
                            at_start = null_positions == list(range(len(null_positions)))
                            at_end = null_positions == list(range(len(seq) - len(null_positions), len(seq)))
                            return at_start or at_end

                        if scope == "within_group":
                            group_ids = cand["tier2"].get("row_group_ids")
                            if not group_ids or len(group_ids) != len(vals):
                                ok = False
                            else:
                                segments: dict[Any, list] = {}
                                for v, g in zip(vals, group_ids):
                                    segments.setdefault(g, []).append(v)
                                ok = all(_monotonic(seg) for seg in segments.values())
                        else:
                            ok = _monotonic(vals)
        else:
            ok = False
        satisfied += 1 if ok else 0
        if not ok:
            notes.append(f"{key}={expected!r} not satisfied")
    pts = _round_points(satisfied / total, 5)
    detail = f"{satisfied}/{total} required instructions satisfied"
    if notes:
        detail += "; " + "; ".join(notes)
    return CheckResult(name, 5, pts, satisfied == total, detail)


def check_column_set(cand: dict, truth: dict, meta: dict) -> CheckResult:
    name = "Column set shown vs. hidden"
    cand_cols, truth_cols = _visible_columns(cand), _visible_columns(truth)
    if not truth_cols:
        return _na(name, "ground truth failed to execute; visible column set unknown")
    if not cand_cols:
        return CheckResult(name, 4, 0, False, f"candidate failed to execute: {cand['tier2'].get('error')}")
    union = cand_cols | truth_cols
    jaccard = len(cand_cols & truth_cols) / len(union) if union else 1.0
    pts = _round_points(jaccard, 4)
    return CheckResult(
        name, 4, pts, cand_cols == truth_cols,
        f"visible-column overlap {jaccard:.2f} (candidate-only={sorted(cand_cols - truth_cols)}, "
        f"missing={sorted(truth_cols - cand_cols)})",
    )


def check_grouping_existence(cand: dict, truth: dict, meta: dict) -> CheckResult:
    name = "Grouping existence"
    ok = bool(cand["tier1"].get("grouping_present")) == bool(truth["tier1"].get("grouping_present"))
    return CheckResult(name, 3, 3 if ok else 0, ok, f"candidate grouping_present={cand['tier1'].get('grouping_present')}, truth={truth['tier1'].get('grouping_present')}")


def check_spanner_existence(cand: dict, truth: dict, meta: dict) -> CheckResult:
    name = "Column-group spanners existence"
    ok = bool(cand["tier1"].get("spanner_present")) == bool(truth["tier1"].get("spanner_present"))
    return CheckResult(name, 2, 2 if ok else 0, ok, f"candidate spanner_present={cand['tier1'].get('spanner_present')}, truth={truth['tier1'].get('spanner_present')}")


def check_stub_existence(cand: dict, truth: dict, meta: dict) -> CheckResult:
    name = "Stub existence"
    ok = bool(cand["tier1"].get("stub_present")) == bool(truth["tier1"].get("stub_present"))
    return CheckResult(name, 2, 2 if ok else 0, ok, f"candidate stub_present={cand['tier1'].get('stub_present')}, truth={truth['tier1'].get('stub_present')}")


def check_hue_collision(cand: dict, truth: dict, meta: dict) -> CheckResult:
    name = "No same-family hue collision across 2 measures"
    mechanics = cand["tier1"].get("color_mechanics", [])
    # Same distinct-(palette, domain) dedup as check_colored_measure_
    # selection's ceiling count -- the same conceptual measure applied via
    # multiple calls that share a palette+domain is one measure, not two,
    # and its (necessarily identical) palette against itself must not read
    # as "two measures colliding on the same hue".
    distinct_measures = list({(m.get("palette"), m.get("domain")) for m in mechanics})
    if len(distinct_measures) < 2:
        return _na(name, "fewer than 2 distinct colored measures; no collision possible")
    palettes = [p for p, _ in distinct_measures[:2]]
    # Normalize through the SAME sequential-palette -> DA-family mapping
    # check_band_hue_harmonization already uses -- `Reds` and `Oranges`
    # are different palette NAMES but the same oxblood family, so an
    # exact-string comparison let a two-measure candidate use both and
    # still pass "no same-family collision" despite rendering the same
    # visual hue for two different measures. A palette not in the mapping
    # (a diverging palette, or an unrecognized name) falls back to
    # comparing its own lowercased name, unchanged from before.
    families = [_SEQ_PALETTE_TO_DA_FAMILY.get((p or "").lower(), (p or "").lower()) for p in palettes]
    collision = palettes[0] is not None and families[0] == families[1]
    return CheckResult(name, 1, 0 if collision else 1, not collision, f"colored-measure palettes: {palettes}")


def check_summary_row_existence(cand: dict, truth: dict, meta: dict) -> CheckResult:
    name = "Summary-row existence + correct aggregation values"
    truth_tier2 = truth["tier2"]
    truth_summary = truth_tier2.get("summary_rows") or []
    if not truth_summary:
        if truth_tier2.get("summary_rows_error"):
            return CheckResult(
                name, 1, 0, False,
                f"ground-truth summary-row extraction failed ({truth_tier2.get('summary_rows_error')}) "
                "-- fingerprint invalid, not a genuine 'no summary row' case",
            )
        return _na(name, "ground truth has no grand-summary row")
    if not cand["tier2"].get("ok"):
        return CheckResult(name, 1, 0, False, f"candidate failed to execute: {cand['tier2'].get('error')}")
    cand_summary = cand["tier2"].get("summary_rows") or []
    if not cand_summary:
        return CheckResult(name, 1, 0, False, "candidate has no grand-summary row")
    # Compare EVERY truth summary row (not just the first -- a ground truth
    # can have multiple, e.g. per-group subtotals) and require EVERY
    # truth-declared value to have a matching, correct candidate value (not
    # just whichever columns the candidate happens to also supply) --
    # otherwise a candidate reproducing one value from the first summary
    # row while omitting its other aggregates (and every later summary
    # row entirely) previously still earned full credit here. Truth rows
    # are matched to candidate rows by label, falling back to position
    # when labels don't line up (e.g. one side omits a label).
    cand_by_label = {r.get("label"): r for r in cand_summary}
    all_ok = True
    compared_cols: list[str] = []
    for i, truth_row in enumerate(truth_summary):
        cand_row = cand_by_label.get(truth_row.get("label"))
        if cand_row is None:
            cand_row = cand_summary[i] if i < len(cand_summary) else None
        truth_values = truth_row.get("values", {})
        cand_values = cand_row.get("values", {}) if cand_row is not None else {}
        for k, tv in truth_values.items():
            compared_cols.append(k)
            if k not in cand_values or not execution_tier.values_close(cand_values[k], tv):
                all_ok = False
    if not compared_cols:
        return CheckResult(name, 1, 0, False, "summary rows share no comparable columns")
    return CheckResult(name, 1, 1 if all_ok else 0, all_ok, f"summary values compared on {sorted(set(compared_cols))}")


def check_label_concept_correctness(cand: dict, truth: dict, meta: dict) -> CheckResult:
    # Moved to the judge per .planning/10-hybrid-comparator.md §3: a
    # LABEL_SYNONYMS literal-substring lookup can't handle all valid
    # phrasings for "is this column labeled with the right concept" --
    # same name/points/slot as before, computation only moved. LABEL_
    # SYNONYMS itself is still passed to the judge as grounding context
    # (see runner.judge._build_user_content), just no longer gates here.
    return _judge_dimension_check(meta, "label_concept_correctness", "Column-label concept-correctness", 1)


def check_grouping_choice_quality(cand: dict, truth: dict, meta: dict) -> CheckResult:
    # New per .planning/10-hybrid-comparator.md §3: no existing check graded
    # WHICH grouping variable (or the choice not to group) was a sensible,
    # goal-serving decision -- only whether grouping was present at all
    # (check_grouping_existence, unchanged above). The judge itself gates
    # applicability (ground truth groups AND REQUIRED_INSTRUCTIONS has no
    # "grouping" key -- see judge_rubric.py), so no extra gating is needed
    # here beyond the shared _judge_dimension_check degrade path.
    return _judge_dimension_check(meta, "grouping_choice_quality", "Grouping-choice quality", 3)


DATA_CHECKS: list[CheckFn] = [
    check_row_selection_identity,
    check_computed_value_correctness,
    check_colored_measure_selection,
    check_sequential_vs_diverging,
    check_explicit_instructions,
    check_column_set,
    check_grouping_existence,
    check_grouping_choice_quality,
    check_spanner_existence,
    check_stub_existence,
    check_hue_collision,
    check_summary_row_existence,
    check_label_concept_correctness,
]


# ----------------------------------------------------------------------- #
# Formatting-compliance checks (§9, 50 pts)
# ----------------------------------------------------------------------- #

def _domain_element_symmetric(lo: str, hi: str, value_range: tuple[float, float] | None = None) -> bool:
    try:
        flo, fhi = float(lo), float(hi)
    except ValueError:
        # Non-numeric literal (a variable/expression pair, e.g. `[-m, m]`
        # or two DIFFERENTLY-named variables computed elsewhere as
        # negations of each other, `lo = -m; hi = m` then `[lo, hi]`).
        # Tracing that generally requires resolving assignments this
        # function can't see from the domain's own text alone -- benefit
        # of the doubt here, same as every other genuinely unresolvable
        # domain expression elsewhere in this check (a bare variable
        # reference, an entirely non-bracketed expression, etc.).
        return True
    # Require an actually-negative lower bound and an actually-positive
    # upper bound, not just equal magnitudes -- a collapsed `[0, 0]` domain
    # (zero-width; every value maps to the same color) and a REVERSED
    # `[1, -1]` domain (lo > hi) both pass a bare `isclose(lo, -hi)`
    # magnitude check despite one being degenerate and the other backwards.
    if not (flo < 0 < fhi and math.isclose(flo, -fhi, rel_tol=1e-6, abs_tol=1e-9)):
        return False
    if value_range is None:
        return True
    # Symmetric alone isn't sufficient: `[-1, 1]` is symmetric but clips
    # nearly every value to a palette extreme over data spanning -100..100.
    # Require the endpoints to also cover the real data's min/max, same
    # coverage requirement the sequential branch already applies.
    actual_lo, actual_hi = value_range
    return flo <= actual_lo and fhi >= actual_hi


def check_domain_computation(cand: dict, truth: dict, meta: dict) -> CheckResult:
    name = "Domain computation (symmetric / full-range / data-driven)"
    mechanics = cand["tier1"].get("color_mechanics", [])
    if not mechanics:
        if _truth_requires_color(meta):
            return CheckResult(name, 8, 0, False, "ground truth requires colored measure(s) but candidate has none")
        return _na(name, "candidate has no colored measures")
    correct, total, notes = 0, 0, []
    for i, entry in enumerate(mechanics):
        shape = _measure_signedness(cand, _mechanics_columns(entry, cand))
        if shape is None:
            continue
        total += 1
        # Per-entry `domain` (added alongside `palette`) — NOT
        # `domain_signature`, which is sorted for stable repeat-vs-repeat
        # comparison and so can't be zipped positionally against this
        # (true source order) list.
        dom = entry.get("domain")
        if dom is not None:
            dom = dom.strip()
        if dom in (None, "None"):
            if entry.get("via_helper"):
                # heatmap()'s auto-derived domain is shape-correct by
                # construction ONLY when the declared `kind=` (what its
                # domain math is actually keyed off) matches the real
                # data -- a `kind="sequential"` call on genuinely
                # diverging data computes a full-range, non-symmetric
                # domain, which is not "shape-correct" despite going
                # through the helper. `kind` unresolved (a dynamic
                # expression) keeps the prior benefit-of-the-doubt.
                helper_kind = entry.get("kind")
                if helper_kind in (None, "") or helper_kind == shape:
                    correct += 1
                else:
                    notes.append(f"measure {i} ({entry.get('columns')}): heatmap() kind='{helper_kind}' doesn't match {shape} data")
                continue
            # A literal .data_color(...) that omits domain= instead falls
            # back to great_tables' OWN auto-inferred range, which is NOT
            # guaranteed symmetric around zero for diverging data (nor
            # consistently shared across facets) -- a real domain-
            # computation gap, not benefit-of-the-doubt territory.
            notes.append(f"measure {i} ({entry.get('columns')}): literal data_color omits domain= (not guaranteed {shape}-correct)")
            continue
        # Split on the TOP-LEVEL comma only (via the shared paren-depth-aware
        # splitter) -- a flat `[(.+?),(.+)]` regex misreads a nested comma
        # inside e.g. `[-max(abs(lo), abs(hi)), max(abs(lo), abs(hi))]` and
        # mis-splits a perfectly valid symmetric domain.
        elems = None
        if dom.startswith("[") and dom.endswith("]"):
            parts = convergence._split_top_level(dom[1:-1])
            if len(parts) == 2:
                elems = parts
        if elems is None:
            # Not a literal 2-element bracketed domain -- e.g. a bare
            # variable reference (`domain=domain`). Not statically
            # verifiable either way from source text alone; benefit of the
            # doubt, same as the auto-derived (None) case above, rather
            # than penalizing a domain expression this check simply can't
            # see through.
            correct += 1
            continue
        if shape == "diverging":
            ok = _domain_element_symmetric(elems[0], elems[1], _actual_value_range(cand, _mechanics_columns(entry, cand)))
        else:
            # Sequential: for a literal NUMERIC 2-element domain, verify it
            # actually COVERS the real data range (lo < hi, lo <= actual
            # min, hi >= actual max) -- merely being well-formed let a
            # collapsed [0, 0], a reversed [1, 0], or an under-covering
            # [0, 1] (over data spanning 0-100) all pass previously. A
            # non-numeric literal (e.g. a variable-derived expression that
            # still parses as a bracketed pair, like `[dens_lo, dens_hi]`)
            # keeps the prior benefit-of-the-doubt -- there's nothing
            # further to verify from static text alone.
            try:
                flo, fhi = float(elems[0]), float(elems[1])
            except ValueError:
                ok = True
            else:
                value_range = _actual_value_range(cand, _mechanics_columns(entry, cand))
                if value_range is None:
                    ok = True
                else:
                    actual_lo, actual_hi = value_range
                    ok = flo < fhi and flo <= actual_lo and fhi >= actual_hi
        correct += 1 if ok else 0
        if not ok:
            notes.append(f"measure {i} ({entry.get('columns')}): domain '{dom}' doesn't match a {shape} shape")
    if total == 0:
        return _na(name, "no colored measure had usable numeric values to classify")
    pts = _round_points(correct / total, 8)
    detail = f"{correct}/{total} colored measures have a shape-appropriate domain"
    if notes:
        detail += "; " + "; ".join(notes)
    return CheckResult(name, 8, pts, correct == total, detail)


def check_frame_hairlines_dividers(cand: dict, truth: dict, meta: dict) -> CheckResult:
    name = "Frame + hairlines + dividers"
    t1 = cand["tier1"]
    frame_ok = bool(t1.get("frame_present"))
    hairlines_ok = bool(t1.get("hairlines_present"))
    dividers_expected = bool(t1.get("spanner_present"))
    dividers_ok = bool(t1.get("dividers_present")) == dividers_expected
    pts = (2 if frame_ok else 0) + (2 if hairlines_ok else 0) + (2 if dividers_ok else 0)
    dividers_detail = (
        "OK" if dividers_ok
        else f"expected={dividers_expected} (gated on spanners), got={t1.get('dividers_present')}"
    )
    detail = (
        f"frame={'OK' if frame_ok else 'MISSING (global constant, always required)'}; "
        f"hairlines={'OK' if hairlines_ok else 'MISSING (Step 5a, always required)'}; "
        f"dividers={dividers_detail}"
    )
    return CheckResult(name, 6, pts, pts == 6, detail)


def check_striping_gate(cand: dict, truth: dict, meta: dict) -> CheckResult:
    name = "Striping gate correctness"
    n = _n_rows(cand)
    if n is None:
        # Codex round-1 finding: `_n_rows()` returns `None` exactly when
        # the candidate's Tier-2 execution failed (see its own
        # docstring/impl) -- there's no OTHER way to reach this branch, so
        # this is never a genuine "not applicable" case. Treating it as
        # N/A (0/0, excluded from the denominator) let a candidate that
        # crashes outright dodge this 5-point penalty entirely, sometimes
        # scoring a HIGHER percentage than one that runs but stripes
        # incorrectly. A hard, graded 0/5 failure reserves N/A for
        # genuine inapplicability elsewhere in this file.
        return CheckResult(name, 5, 0, False, f"candidate failed to execute: {cand['tier2'].get('error')}")
    t1 = cand["tier1"]
    mechanics = t1.get("color_mechanics", [])
    # Structural columns (the stub, the group column) can never be colored
    # or bolded as a "measure" -- counting them in the denominator dilutes
    # a genuinely fully-covered body (e.g. 3 colored/bold columns + 1 stub
    # would read as 3/4 = 0.75, under the 0.8 gate, even though every real
    # data column IS accounted for).
    tier2 = cand["tier2"]
    visible = _visible_columns(cand) - {tier2.get("stub_column"), tier2.get("group_column")}
    # "Essentially fully filled" counts a bold, uncolored HERO column as
    # accounted-for too, not just an actually-colored one — Step 3's rule
    # is that the hero gets bold text specifically AS THE ALTERNATIVE to a
    # third color fill, so it occupies the same "this column carries
    # meaning" role a colored measure would for this gate's purposes.
    accounted_for: set[str] = set(t1.get("bold_columns") or [])
    for e in mechanics:
        accounted_for |= set(_mechanics_columns(e, cand))
    fully_filled = bool(accounted_for) and bool(visible) and (len(accounted_for & visible) / len(visible) >= 0.8)
    expected = n >= 10 and not fully_filled
    actual = bool(t1.get("striping_present"))
    ok = expected == actual
    return CheckResult(name, 5, 5 if ok else 0, ok, f"n_rows={n}, fully_filled={fully_filled} -> expected striping={expected}, actual={actual}")


def check_stub_tint(cand: dict, truth: dict, meta: dict) -> CheckResult:
    name = "Stub tint + grey-budget correctness"
    t1 = cand["tier1"]
    stub = bool(t1.get("stub_present"))
    striped = bool(t1.get("striping_present"))
    expected_on = stub and not striped
    actual_on = bool(t1.get("stub_tint_present"))
    ok = expected_on == actual_on
    return CheckResult(name, 5, 5 if ok else 0, ok, f"stub={stub}, striped={striped} -> expected tint={expected_on}, actual={actual_on}")


_SEQ_PALETTE_TO_DA_FAMILY = {"blues": "navy", "greens": "forest", "reds": "oxblood", "oranges": "oxblood"}


def check_band_hue_harmonization(cand: dict, truth: dict, meta: dict) -> CheckResult:
    name = "Heading band hue harmonization"
    t1 = cand["tier1"]
    has_color = bool(t1.get("color_mechanics"))
    expected_shade = "light" if has_color else "dark"
    actual_shade = t1.get("heading_band_shade", "none")
    shade_ok = actual_shade == expected_shade
    shade_pts = 2 if shade_ok else 0
    # Hue harmonization is only strictly checkable when there's exactly one
    # DISTINCT colored measure overall (same (palette, domain) dedup
    # check_colored_measure_selection/check_hue_collision use) AND that one
    # measure uses a recognized sequential palette -- a diverging-only
    # table, "no color", or MULTIPLE measures (even if only one of them is
    # a recognized-sequential name -- e.g. one sequential + one diverging)
    # all mean there's no longer a single, unambiguous color story to
    # harmonize the band to. Counting only recognized-sequential entries
    # (the previous approach) wrongly entered strict mode for a valid
    # 2-measure table where the second measure just happened to be
    # diverging (and thus excluded from that count).
    distinct_measures = list({(e.get("palette"), e.get("domain")) for e in t1.get("color_mechanics", [])})
    sole_palette = (distinct_measures[0][0] or "").lower() if len(distinct_measures) == 1 else None
    if has_color and sole_palette in _SEQ_PALETTE_TO_DA_FAMILY:
        expected_family = _SEQ_PALETTE_TO_DA_FAMILY[sole_palette]
        hue_ok = t1.get("heading_band_hue") == expected_family
        hue_detail = f"expected hue family '{expected_family}' for palette '{sole_palette}', got '{t1.get('heading_band_hue')}'"
    else:
        hue_ok = True
        hue_detail = "hue harmonization not strictly verifiable for this color configuration (benefit of the doubt)"
    hue_pts = 3 if hue_ok else 0
    pts = shade_pts + hue_pts
    return CheckResult(name, 5, pts, pts == 5, f"shade expected={expected_shade} actual={actual_shade}; {hue_detail}")


def _mechanics_entry_for_column(mechanics: list[dict], fp: dict, column: str) -> dict | None:
    """The `color_mechanics` entry (if any) that targets `column`."""
    for entry in mechanics:
        if column in _mechanics_columns(entry, fp):
            return entry
    return None


def check_color_mechanics(cand: dict, truth: dict, meta: dict) -> CheckResult:
    name = "Color mechanics (na_color, truncate, autocolor_text)"
    mechanics = cand["tier1"].get("color_mechanics", [])
    if not mechanics:
        if _truth_requires_color(meta):
            return CheckResult(name, 4, 0, False, "ground truth requires colored measure(s) but candidate has none")
        return _na(name, "candidate has no colored measures")
    n = len(mechanics)
    na_ok = sum(1 for e in mechanics if e.get("na_color") == "#808080")
    trunc_ok = sum(1 for e in mechanics if e.get("truncate") == "False")
    autocolor_ok = sum(1 for e in mechanics if e.get("autocolor_text") == "True")
    # `reverse` has no universal "correct" value the way na_color/truncate/
    # autocolor_text do -- whether a measure's polarity should be inverted
    # (e.g. RdYlGn with reverse=True so green=decline, for a "more is
    # worse" measure) depends on the DATA's own semantics, not derivable
    # from the candidate alone. The ground truth's own reverse setting for
    # the SAME matched measure (by value, via CANONICAL_MEASURES) is the
    # only mechanical signal available without new §5 metadata -- checked
    # only for measures where a truth mechanics entry and a value-matched
    # candidate column both resolve, so a ground truth without
    # CANONICAL_MEASURES declared (or an unmatched candidate) doesn't
    # shrink this denominator on nothing.
    reverse_ok, reverse_total = 0, 0
    if cand["tier2"].get("ok") and truth["tier2"].get("ok"):
        truth_mechanics = truth["tier1"].get("color_mechanics", [])
        for m in meta["CANONICAL_MEASURES"].get("colored", []):
            truth_entry = _mechanics_entry_for_column(truth_mechanics, truth, m)
            if truth_entry is None:
                continue
            matched_col = execution_tier.match_measure_by_value(cand["tier2"], truth["tier2"], m)
            if matched_col is None:
                continue
            cand_entry = _mechanics_entry_for_column(mechanics, cand, matched_col)
            if cand_entry is None:
                continue
            reverse_total += 1
            if cand_entry.get("reverse") == truth_entry.get("reverse"):
                reverse_ok += 1
    # A single rounding over all sub-checks (rather than one
    # _round_points() call per dimension) so a fully-correct candidate
    # always sums to exactly 4, and "autocolor_text=False" (readable text
    # isn't guaranteed over a dark fill) actually costs points -- the name
    # already promised this field was checked; it wasn't.
    total_checks = 3 * n + reverse_total
    total_ok = na_ok + trunc_ok + autocolor_ok + reverse_ok
    pts = _round_points(total_ok / total_checks, 4)
    return CheckResult(
        name, 4, pts, total_ok == total_checks,
        f"na_color correct {na_ok}/{n}, truncate=False correct {trunc_ok}/{n}, autocolor_text=True correct {autocolor_ok}/{n}"
        + (f", reverse orientation matches truth {reverse_ok}/{reverse_total}" if reverse_total else ""),
    )


def check_summary_row_formatting(cand: dict, truth: dict, meta: dict) -> CheckResult:
    name = "Summary-row formatting matches body"
    # Applicability is gated on the GROUND TRUTH having a summary row, not
    # the candidate — otherwise a candidate that omits a required summary
    # entirely scores N/A (0/0, no penalty) while one that includes a
    # badly-formatted summary scores worse (0/4), making omission the
    # better-scoring strategy.
    truth_tier2 = truth["tier2"]
    truth_summary = truth_tier2.get("summary_rows") or []
    if not truth_summary:
        if truth_tier2.get("summary_rows_error"):
            return CheckResult(
                name, 4, 0, False,
                f"ground-truth summary-row extraction failed ({truth_tier2.get('summary_rows_error')})",
            )
        return _na(name, "ground truth has no grand-summary row to check")
    cand_summary = cand["tier2"].get("summary_rows") or [] if cand["tier2"].get("ok") else []
    if not cand_summary:
        return CheckResult(name, 4, 0, False, "ground truth has a grand-summary row but candidate has none")
    fmt_map = cand["tier1"].get("fmt_column_map", {})
    # Required numeric columns come from the GROUND TRUTH's summary rows, not
    # the candidate's -- otherwise a candidate that replaces a required
    # numeric aggregate with text/empty (or omits it) makes the required set
    # come back empty from ITS OWN data, scoring this 4-point check N/A
    # (no penalty) for the very removal it's meant to catch, while the
    # separate existence/correctness check only costs 1 point for the same
    # thing.
    #
    # Codex round-1 finding: this previously only looked at `truth_summary[0]`
    # -- a ground truth with MULTIPLE grand-summary rows (e.g. per-group
    # subtotals) whose LATER row introduces a numeric aggregate the first
    # row doesn't have silently dropped that column from the requirement, so
    # a candidate could leave it raw/unformatted and still score full
    # credit. Now iterates every truth summary row, same label-matching
    # (falling back to position) `check_summary_row_existence` already uses,
    # accumulating per (row, column) pairs rather than per distinct column
    # name -- a column present in multiple rows must be checked in EACH row
    # it's expected in, not just once overall.
    cand_by_label = {r.get("label"): r for r in cand_summary}
    required_pairs = 0
    covered_pairs = 0
    distinct_cols: set[str] = set()
    for i, truth_row in enumerate(truth_summary):
        row_numeric_cols = [
            k for k, v in truth_row.get("values", {}).items() if isinstance(v, (int, float))
        ]
        if not row_numeric_cols:
            continue
        cand_row = cand_by_label.get(truth_row.get("label"))
        if cand_row is None:
            cand_row = cand_summary[i] if i < len(cand_summary) else None
        cand_values = cand_row.get("values", {}) if cand_row is not None else {}
        for c in row_numeric_cols:
            distinct_cols.add(c)
            required_pairs += 1
            if isinstance(cand_values.get(c), (int, float)) and fmt_map.get(c, fmt_map.get(convergence._ALL_COLUMNS)):
                covered_pairs += 1
    if required_pairs == 0:
        return _na(name, "grand-summary row(s) have no numeric values to check")
    pts = _round_points(covered_pairs / required_pairs, 4)
    detail = (
        f"{covered_pairs}/{required_pairs} numeric summary-row/column pairs across "
        f"{len(truth_summary)} ground-truth summary row(s) ({sorted(distinct_cols)}) are covered by a "
        "fmt_* call (great_tables does not auto-apply body formatting to grand_summary_rows -- Defect C)"
    )
    return CheckResult(name, 4, pts, covered_pairs == required_pairs, detail)


_SEMANTIC_TO_FMT = {
    "percent": {"fmt_percent"},
    "number": {"fmt_number", "fmt_integer"},
    "currency": {"fmt_currency"},
    "integer": {"fmt_integer", "fmt_number"},
}


def check_fmt_semantic_type(cand: dict, truth: dict, meta: dict) -> CheckResult:
    name = "fmt_* per column semantic type"
    semantic_types = meta["SEMANTIC_TYPES"]
    if not semantic_types:
        return _na(name, "ground truth declares no SEMANTIC_TYPES to check")
    if not cand["tier2"].get("ok"):
        return CheckResult(name, 4, 0, False, f"candidate failed to execute: {cand['tier2'].get('error')}")
    # Applicability is gated on the candidate's VISIBLE columns, not on
    # which ones it happened to format -- otherwise a candidate with ZERO
    # fmt_* calls has an empty fmt_map, `applicable` comes back empty, and
    # this required semantic-format check scores N/A (no penalty) instead
    # of failing every visible semantic-typed column that renders raw.
    visible = _visible_columns(cand)
    applicable = {c: t for c, t in semantic_types.items() if c in visible}
    if not applicable:
        return _na(name, "none of the ground truth's semantic-typed columns are visible in the candidate")
    fmt_map = cand["tier1"].get("fmt_column_map", {})
    ok_count = sum(
        1 for c, t in applicable.items()
        if fmt_map.get(c, fmt_map.get(convergence._ALL_COLUMNS)) in _SEMANTIC_TO_FMT.get(t, set())
    )
    all_ok = ok_count == len(applicable)
    return CheckResult(name, 4, _round_points(ok_count / len(applicable), 4), all_ok, f"{ok_count}/{len(applicable)} columns formatted per their semantic type")


def check_title_subtitle_caption_source(cand: dict, truth: dict, meta: dict) -> CheckResult:
    name = "Title/subtitle/caption/source presence per gating rules"
    t1 = cand["tier1"]
    # Presence-only signals (title_present / caption_present -- the latter
    # is convergence.py's field name for "tab_header's subtitle= kwarg is
    # present", not the source-note caption computed a few lines below;
    # unrelated pre-existing name collision), NOT title_text/subtitle_text
    # -- those are literal-extraction fields that return None for a
    # dynamic value (a variable or f-string title/subtitle), which would
    # otherwise wrongly read as "missing" for an output-identical candidate.
    title_pts = 1 if t1.get("title_present") else 0
    subtitle_pts = 1 if t1.get("caption_present") else 0
    n = _n_rows(cand)
    caption_expected = n is not None and n >= 5
    # `None` means a `tab_source_note(...)` call exists but its text is a
    # dynamic expression (a variable, an unresolved f-string) -- same
    # benefit-of-the-doubt treatment as title_text/subtitle_text above: the
    # call is genuinely present, just not statically readable, so it must
    # not read as "missing" the way an explicit empty-string literal would.
    # Codex round-1 finding: the code below previously contradicted this
    # comment -- it required `notes[i] is not None`, docking the point from
    # a candidate whose caption/source-note call genuinely exists but is a
    # dynamic expression. `source_note_texts`'s own contract (see
    # `convergence._source_note_texts`'s docstring) is ONE list entry per
    # call, always -- so the SLOT existing (`len(notes) >= N`) is what
    # establishes "the call is present," independent of whether its text
    # happened to resolve statically.
    notes = cand["tier1"].get("source_note_texts") or []
    caption_present = len(notes) >= 1
    source_expected = bool(truth["tier1"].get("source_note_texts")) and len(truth["tier1"]["source_note_texts"]) >= 2
    source_present = len(notes) >= 2
    # "present if expected" for both -- neither ever REQUIRES absence when
    # optional (fewer than 5 rows): a compliant short table that
    # voluntarily includes a caption anyway must not lose this point, the
    # same tolerance already given to an optional source note.
    footer_ok = (caption_present or not caption_expected) and (source_present or not source_expected)
    footer_pts = 1 if footer_ok else 0
    pts = title_pts + subtitle_pts + footer_pts
    return CheckResult(
        name, 3, pts, pts == 3,
        f"title={'OK' if title_pts else 'MISSING'}, subtitle={'OK' if subtitle_pts else 'MISSING'}, "
        f"caption expected={caption_expected} present={caption_present}, source expected={source_expected} present={source_present}",
    )


def check_hero_column_formatting(cand: dict, truth: dict, meta: dict) -> CheckResult:
    name = "Hero-column formatting when nothing is colored"
    if cand["tier1"].get("color_mechanics"):
        return _na(name, "candidate has colored measures; hero-bold rule doesn't apply")
    hero_measures = meta["CANONICAL_MEASURES"].get("hero_uncolored", [])
    if not hero_measures:
        # No canonical hero measure declared to target -- fall back to the
        # original "some column is bold" signal (there's nothing more
        # specific to check against).
        bolded = bool(cand["tier1"].get("bold_columns"))
        return CheckResult(
            name, 2, 2 if bolded else 0, bolded,
            f"bold_columns={cand['tier1'].get('bold_columns')} (no canonical hero measure declared)",
        )
    if not cand["tier2"].get("ok"):
        return CheckResult(name, 2, 0, False, f"candidate failed to execute: {cand['tier2'].get('error')}")
    # Bolding is only meaningful when it targets the ACTUAL declared hero
    # measure(s), matched by VALUE (not name) like every other measure
    # check here -- bolding an unrelated identifier or secondary metric
    # previously earned full credit just for being nonempty.
    bold_cols = set(cand["tier1"].get("bold_columns") or [])
    covered = 0
    for m in hero_measures:
        matched_col = execution_tier.match_measure_by_value(cand["tier2"], truth["tier2"], m)
        if matched_col and matched_col in bold_cols:
            covered += 1
    pts = _round_points(covered / len(hero_measures), 2)
    return CheckResult(
        name, 2, pts, covered == len(hero_measures),
        f"{covered}/{len(hero_measures)} canonical hero-uncolored measures are bolded",
    )


def check_render_mechanics(cand: dict, truth: dict, meta: dict) -> CheckResult:
    name = "Render mechanics (zoom/expand fit-order rule)"
    params = cand["tier1"].get("render_params") or {}
    if not params:
        # `render_params` is `{}` for two DIFFERENT cases that must not be
        # scored the same way: no gtsave()/finalize() call at all (the
        # mandatory table image was never produced -- a hard failure, not
        # unverifiable) vs. a render call that exists but whose params
        # aren't statically resolvable (e.g. a **kwargs expansion --
        # genuinely unverifiable, benefit of the doubt).
        if not cand["tier1"].get("render_call_present"):
            return CheckResult(name, 2, 0, False, "no gtsave()/finalize() call found -- the required table image was never rendered")
        return _na(name, "render params unresolved (e.g. a **kwargs expansion) -- not verifiable, benefit of the doubt")
    try:
        zoom = float(params.get("zoom", "2.0"))
    except ValueError:
        return _na(name, f"non-literal zoom value '{params.get('zoom')}' -- not verifiable")
    if zoom >= 2.0:
        return CheckResult(name, 2, 2, True, f"zoom={zoom} >= default 2.0")
    try:
        expand = float(params.get("expand", "5"))
    except ValueError:
        expand = 5.0
    # The fit-order rule is "grow room before shrinking zoom" -- vwidth/
    # vheight are an EQUALLY valid way to grow room as expand is (both are
    # captured by _render_params, but only expand was ever checked here).
    # Neither has a fixed numeric default (great_tables sizes them
    # dynamically when omitted), so simply being EXPLICITLY set at all is
    # the signal that the candidate deliberately grew the canvas.
    viewport_raised = "vwidth" in params or "vheight" in params
    if expand > 5.0 or viewport_raised:
        via = "expand" if expand > 5.0 and not viewport_raised else (
            "vwidth/vheight" if viewport_raised and expand <= 5.0 else "expand and vwidth/vheight"
        )
        return CheckResult(name, 2, 1, False, f"zoom={zoom} < 2.0, but {via} was raised first (partial credit per the fit-order rule)")
    return CheckResult(name, 2, 0, False, f"zoom={zoom} < default 2.0 without raising expand/vwidth/vheight first")


def _summary_row_style_is_distinctive(source: str) -> bool:
    """True if a `tab_style(...)` call scoped to the grand-summary row
    (`loc.grand_summary()`/`loc.summary_rows()`) applies an ACTUALLY
    distinctive style -- bold text, a visible (non-zero, non-"none")
    border, or a visible (non-transparent) fill.

    Replaces two loose signals that don't verify anything real: a bare
    `#BDBDBD` substring search anywhere in the WHOLE source (which also
    matches `group_emphasis()`'s unrelated row-group border, a comment, or
    a docstring), and a bare "does `loc.grand_summary_rows(...)` appear
    anywhere" check (which a no-op like `style.text(weight="normal")`
    scoped to that location would also satisfy, despite rendering
    identically to the body).
    """
    for block in convergence._call_arg_blocks(source, "tab_style"):
        loc_val = convergence._kwarg_value(block, "locations")
        if loc_val is None:
            positionals = [
                p for p in convergence._split_top_level(block) if not re.match(r"[A-Za-z_]\w*\s*=", p)
            ]
            loc_val = positionals[1] if len(positionals) >= 2 else None
        if loc_val is None or not re.search(r"loc\s*\.\s*(?:grand_)?summary(?:_rows)?\s*\(", loc_val):
            continue
        style_val = convergence._kwarg_value(block, "style")
        if style_val is None:
            positionals = [
                p for p in convergence._split_top_level(block) if not re.match(r"[A-Za-z_]\w*\s*=", p)
            ]
            style_val = positionals[0] if positionals else None
        if not style_val:
            continue
        for tm in re.finditer(r"style\s*\.\s*text\s*\(", style_val):
            close_idx = convergence._scan_balanced_paren(style_val, tm.end() - 1)
            if close_idx is None:
                continue
            weight_val = convergence._kwarg_value(style_val[tm.end():close_idx], "weight")
            if weight_val:
                unquoted = convergence._unquote(weight_val)
                if unquoted and unquoted.strip().lower() not in ("normal", "regular", "400", ""):
                    return True
        for bm in re.finditer(r"style\s*\.\s*borders\s*\(", style_val):
            close_idx = convergence._scan_balanced_paren(style_val, bm.end() - 1)
            if close_idx is None:
                continue
            borders_block = style_val[bm.end():close_idx]
            border_style_val = convergence._kwarg_value(borders_block, "style")
            if border_style_val:
                unquoted = convergence._unquote(border_style_val)
                if unquoted and unquoted.strip().lower() in ("none", "hidden", ""):
                    continue
            weight_val = convergence._kwarg_value(borders_block, "weight")
            if weight_val:
                unquoted_w = convergence._unquote(weight_val)
                if unquoted_w and convergence._is_zero_length(unquoted_w):
                    continue
            return True
        for fm in re.finditer(r"style\s*\.\s*fill\s*\(", style_val):
            close_idx = convergence._scan_balanced_paren(style_val, fm.end() - 1)
            if close_idx is None:
                continue
            fill_block = style_val[fm.end():close_idx]
            color_val = convergence._kwarg_value(fill_block, "color")
            if color_val is None:
                fill_positionals = [
                    p for p in convergence._split_top_level(fill_block) if not re.match(r"[A-Za-z_]\w*\s*=", p)
                ]
                color_val = fill_positionals[0] if fill_positionals else None
            unquoted_color = convergence._unquote(color_val) if color_val else None
            # `convergence._is_effectively_transparent` doesn't exist in the
            # version of convergence.py merged to gtc/root -- see the
            # compatibility-shim section near `build_fingerprint()` above;
            # this reuses the local shim copy instead.
            if unquoted_color and _is_effectively_transparent(unquoted_color.strip()):
                continue
            return True
    return False


def check_summary_row_visual_distinction(cand: dict, truth: dict, meta: dict) -> CheckResult:
    name = "Summary-row visual distinction from body"
    # Same truth-gated applicability as check_summary_row_formatting (and
    # for the same reason): omitting a required summary must not score
    # better than including a poorly-distinguished one.
    truth_tier2 = truth["tier2"]
    truth_summary = truth_tier2.get("summary_rows") or []
    if not truth_summary:
        if truth_tier2.get("summary_rows_error"):
            return CheckResult(
                name, 1, 0, False,
                f"ground-truth summary-row extraction failed ({truth_tier2.get('summary_rows_error')})",
            )
        return _na(name, "ground truth has no grand-summary row to check")
    cand_summary = cand["tier2"].get("summary_rows") or [] if cand["tier2"].get("ok") else []
    if not cand_summary:
        return CheckResult(name, 1, 0, False, "ground truth has a grand-summary row but candidate has none")
    distinct = _summary_row_style_is_distinctive(cand["source"])
    return CheckResult(name, 1, 1 if distinct else 0, distinct, "checked for an active bold/border/fill style scoped to the summary row (not a bare token search)")


def check_caption_not_restating_subtitle(cand: dict, truth: dict, meta: dict) -> CheckResult:
    # Moved to the judge per .planning/10-hybrid-comparator.md §3: a
    # CAPTION_KEYWORDS lookup can't handle all valid phrasings for "does the
    # caption add real information beyond the subtitle" -- same name/points/
    # slot as before, computation only moved. CAPTION_KEYWORDS itself is
    # still passed to the judge as grounding context, just no longer gates.
    return _judge_dimension_check(meta, "caption_quality", "Caption doesn't just restate the subtitle", 1)


def check_title_quality(cand: dict, truth: dict, meta: dict) -> CheckResult:
    # New per .planning/10-hybrid-comparator.md §3: the prior
    # check_title_subtitle_caption_source above is presence-only ("does a
    # title exist"); this grades whether it's clear, accurate, and matches
    # the ground truth's core framing -- a wording judgment, not a fact.
    return _judge_dimension_check(meta, "title_quality", "Title quality", 3)


def check_subtitle_quality(cand: dict, truth: dict, meta: dict) -> CheckResult:
    # New, same rationale as check_title_quality: does the subtitle add real
    # clarifying context, non-redundant with the title.
    return _judge_dimension_check(meta, "subtitle_quality", "Subtitle quality", 3)


def check_column_order_quality(cand: dict, truth: dict, meta: dict) -> CheckResult:
    # New: `09` explicitly left column order ungraded ("Doesn't grade...
    # column order", `09` §3) since a sensible left-to-right reading order
    # is one of several valid choices, not a single fixed answer.
    return _judge_dimension_check(meta, "column_order_quality", "Column order quality", 2)


def check_color_theme_quality(cand: dict, truth: dict, meta: dict) -> CheckResult:
    # New: check_sequential_vs_diverging/check_domain_computation/check_
    # band_hue_harmonization above already verify shape/family/mechanics
    # correctness deterministically; this grades the remaining subjective
    # layer -- is the SPECIFIC hue/palette choice tasteful and harmonious --
    # previously an explicit non-goal (`09` §3: "only family/shape-
    # correctness is checked").
    return _judge_dimension_check(meta, "color_theme_quality", "Color theme/palette taste", 3)


FORMAT_CHECKS: list[CheckFn] = [
    check_domain_computation,
    check_frame_hairlines_dividers,
    check_striping_gate,
    check_stub_tint,
    check_band_hue_harmonization,
    check_color_mechanics,
    check_summary_row_formatting,
    check_fmt_semantic_type,
    check_title_subtitle_caption_source,
    check_hero_column_formatting,
    check_render_mechanics,
    check_summary_row_visual_distinction,
    check_title_quality,
    check_subtitle_quality,
    check_column_order_quality,
    check_color_theme_quality,
    check_caption_not_restating_subtitle,
]


# ----------------------------------------------------------------------- #
# scoring rollup + report
# ----------------------------------------------------------------------- #

@dataclass
class ComparatorReport:
    candidate_path: str
    ground_truth_path: str
    data_earned: int
    data_possible: int
    format_earned: int
    format_possible: int
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def total_earned(self) -> int:
        return self.data_earned + self.format_earned

    @property
    def total_possible(self) -> int:
        return self.data_possible + self.format_possible


def compare(candidate_path: Path, ground_truth_path: Path, prompt_text: str = "") -> ComparatorReport:
    """Run every check and roll up the score. Never raises on a candidate
    that fails to execute or parse — every check function is written to
    degrade to a 0-point failure (or an N/A skip) rather than crash, so a
    broken candidate still gets a full, itemized report.

    ``prompt_text`` is the original natural-language prompt's own text
    (``gt_compare.py`` resolves it from ``prompts/<difficulty>/<prompt_id>.json``'s
    ``"prompt"`` field) -- threaded straight through to the one grounded
    judge call below. It's optional (defaults to ``""``) so a caller that
    only needs the deterministic checks (e.g. a unit test) doesn't have to
    supply it; the judge call itself still runs and simply has less context
    to ground its wording judgments in.

    The judge is invoked exactly ONCE per comparison (§4 of
    ``.planning/10-hybrid-comparator.md``: "one batched call... scoring all
    7 dimensions together"), and its single combined result is stashed in
    ``meta["_judge_result"]`` before any check function runs, so every
    judge-backed check (see ``_judge_dimension_check``) reads from the same
    call rather than each triggering its own. Candidate/ground-truth PNGs
    are derived by the same convention this repo already uses elsewhere:
    each `.py` has a checked-in or freshly-rendered `.png` twin alongside
    it. If either PNG doesn't exist, or the model call itself fails,
    ``judge()`` degrades to its own "unavailable" result (see that
    function's docstring) -- this never raises and never blocks the
    deterministic checks from running.
    """
    cand = build_fingerprint(candidate_path)
    truth = build_fingerprint(ground_truth_path)
    meta = load_ground_truth_metadata(ground_truth_path)

    candidate_png = candidate_path.with_suffix(".png")
    truth_png = ground_truth_path.with_suffix(".png")
    meta["_judge_result"] = judge_module.judge(candidate_png, truth_png, prompt_text, meta)

    data_results = [fn(cand, truth, meta) for fn in DATA_CHECKS]
    format_results = [fn(cand, truth, meta) for fn in FORMAT_CHECKS]

    return ComparatorReport(
        candidate_path=str(candidate_path),
        ground_truth_path=str(ground_truth_path),
        data_earned=sum(r.points_earned for r in data_results),
        data_possible=sum(r.points_possible for r in data_results),
        format_earned=sum(r.points_earned for r in format_results),
        format_possible=sum(r.points_possible for r in format_results),
        checks=data_results + format_results,
    )


def format_report(report: ComparatorReport) -> str:
    """Human-readable report: total + subtotals + one line per check."""
    lines = [
        f"Ground-truth comparison: {report.candidate_path} vs {report.ground_truth_path}",
        "",
        f"TOTAL: {report.total_earned}/{report.total_possible}"
        + (f" ({100 * report.total_earned / report.total_possible:.1f}%)" if report.total_possible else ""),
        f"  Data-compliance:        {report.data_earned}/{report.data_possible}",
        f"  Formatting-compliance:  {report.format_earned}/{report.format_possible}",
        "",
    ]
    for r in report.checks:
        # `_na()` results have `passed=True` (so they don't drag down a
        # rollup) but graded nothing (points_possible == 0) -- reporting
        # those as PASS claims the condition was verified when it wasn't.
        mark = "N/A" if r.points_possible == 0 else ("PASS" if r.passed else "FAIL")
        # Per .planning/10-hybrid-comparator.md §7/§8: make judge-backed vs.
        # mechanical visible in the printed report itself, not just in code
        # comments -- a reader shouldn't have to open comparator.py to know
        # whether a given line came from a regex/execution check or an LLM
        # call.
        tier_tag = "JUDGE" if r.tier == "judge" else "MECHANICAL"
        lines.append(f"[{mark}] [{tier_tag}] {r.name}: {r.points_earned}/{r.points_possible} -- {r.detail}")
    return "\n".join(lines)
