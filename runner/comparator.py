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


def _find_band_color_last(source: str) -> str | None:
    """Like `convergence._find_band_color`, but returns the LAST literal
    color occurrence of the preferred key across the whole source, not
    the first.

    Codex round-8 finding: `convergence._find_band_color` (off-limits --
    see this file's Tier-1 compatibility-shim section) uses `re.search`,
    which returns the FIRST match in the whole source -- the same "first
    call wins instead of the last, effective one" bug class already
    fixed elsewhere in this file (title/subtitle presence, render-target
    resolution, striping, reverse orientation, na_color/truncate/
    autocolor_text). A script that sets an initial band color via one
    `tab_options(...)` call and overrides it via a LATER call (an
    initial-theme-then-override pattern) had the ORIGINAL, overridden
    value trusted instead of the one actually rendered. `runner/
    convergence.py` is a hard non-goal for this slice, so this is the
    same shim pattern used throughout: a corrected local
    reimplementation (`re.findall` + take the last match, instead of
    `re.search`'s first-match), otherwise identical to the original --
    same two keys, checked in the same preference order (`column_labels_
    background_color` over `heading_background_color`, not merged
    together).
    """
    for key in ("column_labels_background_color", "heading_background_color"):
        matches = re.findall(rf"{key}\s*=\s*['\"]([^'\"]+)['\"]", source)
        if matches:
            return matches[-1]
    return None


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


# Minimal CSS named-color -> hex table, scoped to exactly what
# `_normalize_css_color` below needs to recognize (not a general
# CSS-color-parsing library -- see that function's docstring for why no
# pip dependency was added for this bounded need).
_CSS_NAMED_COLORS = {
    "gray": "#808080",
    "grey": "#808080",
    "white": "#FFFFFF",
    "black": "#000000",
}


def _normalize_css_color(value: str | None) -> str | None:
    """Best-effort normalization of a CSS color literal to a canonical
    `#RRGGBB` (uppercase) string, or `None` if it can't be parsed as a
    color at all (a variable, a genuinely unrecognized value).

    Codex round-2 finding: `check_color_mechanics` compared `na_color` as a
    raw string against the literal `"#808080"`, so CSS-equivalent
    spellings of that exact color (`na_color="gray"`,
    `na_color="rgb(128, 128, 128)"`) were rejected even though they render
    IDENTICALLY -- inconsistent with this file's outcome-based scoring
    philosophy everywhere else. This is a small, self-contained
    normalizer for that bounded need, NOT a general CSS-color-parsing
    package (one was considered and explicitly declined -- a short named-
    color table plus a simple `rgb()`/`rgba()` regex parser covers what
    this repo's own conventions plausibly produce): hex (`#rgb`/
    `#rrggbb`/`#rrggbbaa`), `rgb(...)`/`rgba(...)` functional notation, and
    a tiny named-color table for the specific keyword spellings
    (`gray`/`grey`) most likely to appear for the required neutral
    `#808080`.

    Codex round-4 finding: an `#RRGGBBAA`/`rgba(...)` alpha channel was
    previously DISCARDED entirely, so a fully (or partially) transparent
    `na_color="#80808000"` normalized to opaque `"#808080"` and wrongly
    matched the required color despite rendering invisible, not gray. A
    non-opaque alpha now makes normalization return `None` (doesn't match
    ANY expected color) rather than silently rounding it up to fully
    opaque.
    """
    if value is None:
        return None
    v = value.strip()
    low = v.lower()
    if low in _CSS_NAMED_COLORS:
        return _CSS_NAMED_COLORS[low]
    m = re.fullmatch(r"#([0-9A-Fa-f]{3})", v)
    if m:
        h = m.group(1)
        return "#" + "".join(ch * 2 for ch in h).upper()
    m = re.fullmatch(r"#([0-9A-Fa-f]{6})", v)
    if m:
        return "#" + m.group(1).upper()
    m = re.fullmatch(r"#([0-9A-Fa-f]{8})", v)  # RRGGBBAA
    if m:
        if m.group(1)[6:8].upper() != "FF":  # non-opaque alpha -- don't trust as a solid color
            return None
        return "#" + m.group(1)[:6].upper()
    m = re.fullmatch(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([\d.]+)\s*)?\)", v, re.I)
    if m:
        alpha_text = m.group(4)
        if alpha_text is not None:
            try:
                if float(alpha_text) < 1.0:  # non-opaque -- don't trust as a solid color
                    return None
            except ValueError:
                return None
        try:
            r, g, b = (int(m.group(i)) for i in (1, 2, 3))
        except ValueError:
            return None
        if not all(0 <= x <= 255 for x in (r, g, b)):
            return None
        return "#{:02X}{:02X}{:02X}".format(r, g, b)
    return None


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

    Sweep-A finding (round 8): this returned True on the FIRST `loc.stub(
    )`-scoped `tab_style(...)` call that resolved to a visible, approved
    color, without checking whether a LATER `loc.stub()`-scoped call
    overrides it with a different (possibly invisible/unapproved) one --
    `tab_style` calls targeting the SAME location apply in order, so only
    the LAST one actually determines the stub's final rendered fill.
    Every stub-scoped call is now collected first, in source order, and
    only the LAST one is evaluated.
    """
    if convergence._find_stub_tint_hue(source) is not None:
        return True
    stub_blocks: list[str] = []
    for block in convergence._call_arg_blocks(source, "tab_style"):
        loc_val = convergence._kwarg_value(block, "locations")
        if loc_val is None:
            positionals = [
                p for p in convergence._split_top_level(block) if not re.match(r"[A-Za-z_]\w*\s*=", p)
            ]
            loc_val = positionals[1] if len(positionals) >= 2 else None
        if loc_val is None or not re.search(r"loc\s*\.\s*stub\s*\(", loc_val):
            continue
        stub_blocks.append(block)
    if not stub_blocks:
        return False
    block = stub_blocks[-1]
    style_val = convergence._kwarg_value(block, "style")
    if style_val is None:
        positionals = [
            p for p in convergence._split_top_level(block) if not re.match(r"[A-Za-z_]\w*\s*=", p)
        ]
        style_val = positionals[0] if positionals else None
    if not style_val:
        return False
    fm = re.search(r"style\s*\.\s*fill\s*\(", style_val)
    if not fm:
        return False
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
            return False
        # Codex round-6 finding: this only ever validated a color
        # literal that starts with "#", so a named CSS color like
        # `style.fill(color="red")` bypassed the approved-color check
        # entirely (a saturated color, never one of palettes.md §2's
        # neutral/washed tints, silently treated as approved). Reuses
        # `_normalize_css_color` (the SAME normalizer already built
        # for `na_color`, per Codex's own suggestion) so hex, `rgb()`/
        # `rgba()`, and the small recognized named-color spellings all
        # get resolved equally before checking `_ALLOWED_TINT_HEXES`.
        # Only a genuinely UNRESOLVABLE expression (a bare variable
        # reference, not a quoted literal at all) keeps the benefit of
        # the doubt below -- a real, statically-known literal that
        # isn't transparent and doesn't normalize to an approved hex
        # is a real, visible, non-approved color and must fail here,
        # whether or not it happens to be spelled as a "#..." string.
        literal_color = _quoted_string_literal_value(color_val) if color_val else None
        if literal_color is not None:
            normalized = _normalize_css_color(literal_color.strip())
            if normalized is None or normalized not in _ALLOWED_TINT_HEXES:
                return False
    return True


def _render_target_var_literals(source: str, tree: ast.Module) -> dict[tuple[int, int], str]:
    """`{gtsave/finalize CALL NODE's own (lineno, col_offset) -> resolved
    literal string}` for a NARROW, purely syntactic pattern: a plain
    `name = "literal"` assignment on the statement IMMEDIATELY PRECEDING
    (same body/scope) the SPECIFIC statement containing a call passing
    that same bare name as its path argument -- e.g. `output =
    "backup.png"` then `gt.gtsave(output)` on the very next line of the
    same function (or module) body.

    Codex round-7 finding: `_blocks_target_table_png` gave UNCONDITIONAL
    benefit of the doubt to any non-literal render-target argument,
    including a bare variable whose value is trivially resolvable from
    static text -- `output = "backup.png"; gt.gtsave(output)` was scored
    identically to a genuinely dynamic/unknowable path. This deliberately
    does NOT attempt general data-flow analysis: a function parameter, a
    computed/formatted string (an f-string, `+` concatenation, `.format(
    )`), or an assignment several statements earlier or in a DIFFERENT
    scope/branch all still correctly resolve to nothing here, and callers
    keep their existing benefit-of-the-doubt behavior for them.

    Codex round-8 follow-up: round 7's version keyed its result dict by
    VARIABLE NAME, globally across the whole source -- `output =
    "table.png"; gt.gtsave(output); output = "backup.png";
    gt.gtsave(output)` had the SECOND assignment clobber the single
    name-keyed entry used to judge BOTH calls, misjudging the first
    (correct) call using the second (wrong) value. Keyed by the CALL
    NODE's own `(lineno, col_offset)` instead -- the exact same sort key
    `_ast_call_blocks` already uses for this same call node -- so each
    call site resolves strictly against the statement immediately
    preceding IT, never a different call's binding. `tree` is passed in
    (rather than re-parsed here) so callers building `_ast_call_blocks`
    results from the SAME parse can look up by identical keys.
    """

    def _matching_calls(stmt: ast.stmt) -> list[tuple[ast.Call, str]]:
        result: list[tuple[ast.Call, str]] = []
        for node in ast.walk(stmt):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            is_gtsave = isinstance(func, ast.Attribute) and func.attr == "gtsave"
            is_finalize = isinstance(func, ast.Name) and func.id == "finalize"
            if not (is_gtsave or is_finalize):
                continue
            var_name = None
            for kw in node.keywords:
                if kw.arg in ("file", "path") and isinstance(kw.value, ast.Name):
                    var_name = kw.value.id
                    break
            if var_name is None:
                idx = 0 if is_gtsave else 1
                if len(node.args) > idx and isinstance(node.args[idx], ast.Name):
                    var_name = node.args[idx].id
            if var_name is not None:
                result.append((node, var_name))
        return result

    out: dict[tuple[int, int], str] = {}
    for scope_node in ast.walk(tree):
        for field in ("body", "orelse", "finalbody"):
            stmts = getattr(scope_node, field, None)
            if not isinstance(stmts, list):
                continue
            for i in range(1, len(stmts)):
                prev = stmts[i - 1]
                if not (
                    isinstance(prev, ast.Assign)
                    and len(prev.targets) == 1
                    and isinstance(prev.targets[0], ast.Name)
                    and isinstance(prev.value, ast.Constant)
                    and isinstance(prev.value.value, str)
                ):
                    continue
                for call_node, var_name in _matching_calls(stmts[i]):
                    if var_name == prev.targets[0].id:
                        out[(call_node.lineno, call_node.col_offset)] = prev.value.value
    return out


def _blocks_target_table_png(
    blocks: list[tuple[tuple[int, int], str]],
    path_kwarg: str,
    path_index: int,
    var_literals: dict[tuple[int, int], str] | None = None,
) -> bool:
    """True if any call block's path argument plausibly targets `table.png`.

    `blocks` is `(call_node_position, arg_block_text)` pairs, the same
    shape `_ast_call_blocks` returns -- the position is what lets this
    look up `var_literals` PER CALL SITE (see `_render_target_var_
    literals`) instead of by variable name globally.

    A literal path only counts when `convergence._targets_table_png`
    confirms it; a non-literal path (a variable, an f-string) can't be
    proven wrong from source text alone and gets the benefit of the doubt
    -- UNLESS `var_literals` resolves THIS SPECIFIC call's bare-variable
    path to a known literal, in which case it's checked directly and does
    NOT fall back to the benefit of the doubt (a resolved-but-wrong
    literal is a real, provable failure, not an unknowable one).
    """
    for pos, b in blocks:
        path_val = convergence._kwarg_value(b, path_kwarg)
        if path_val is None:
            positionals = [
                p for p in convergence._split_top_level_quoted(b) if not re.match(r"[A-Za-z_]\w*\s*=", p)
            ]
            path_val = positionals[path_index] if len(positionals) > path_index else None
        if path_val is None:
            continue
        stripped = path_val.strip()
        if var_literals and pos in var_literals and re.fullmatch(r"[A-Za-z_]\w*", stripped):
            if convergence._targets_table_png(var_literals[pos]):
                return True
            continue  # resolved to a known, non-matching literal -- not "unknown"
        if not _is_static_string_literal(stripped):
            return True  # non-literal -- can't prove it's the wrong target
        if convergence._targets_table_png(path_val):
            return True
    return False


def _has_real_call(source: str, func_name: str, *, allow_bare: bool = False) -> bool:
    """True if `source` contains a GENUINE `ast.Call` node naming
    `func_name` -- `allow_bare=True` also matches a bare call
    (`func_name(...)`), otherwise only an attribute/method call
    (`.func_name(...)`). Unlike a source-wide regex
    (a source-wide `re.search` for `func_name` followed by an open paren),
    this can't be fooled by a
    `def func_name(...):` function DEFINITION, a comment, or a docstring
    merely mentioning the name -- it only ever visits nodes that are
    ACTUALLY calls in the executable code.

    Codex round-6 finding: `_frame_present`'s own `frame(...)`/
    `finalize(...)` detection still used exactly this kind of source-wide
    regex, never migrated to the AST-based approach already built for
    color-mechanics call detection (`_ast_call_blocks`) -- a candidate
    script defining its OWN helper function named `frame`
    (`def frame(gt, ...):`), or a comment/docstring merely mentioning
    "frame(", satisfied it despite never actually CALLING anything.

    Returns `False` for unparseable source -- consistent with
    `_enrich_color_mechanics`'s own "can't prove a call exists, so don't
    fabricate one" behavior for a broken candidate.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr == func_name:
            return True
        if allow_bare and isinstance(func, ast.Name) and func.id == func_name:
            return True
    return False


def _frame_present(source: str) -> bool:
    """True if a candidate's table FRAME is genuinely VISIBLE -- not merely
    whether a frame-related option/call NAME appears in the source.

    Codex round-2 finding: `convergence.parse_design_choices`'s own
    `frame_present` (out of scope to modify) is a bare token search --
    `table_border_left_width="0px"`, `table_border_left_style="none"`, or
    a transparent `table_border_left_color=` all satisfy that regex
    despite rendering NO visible frame at all, so a candidate stating
    these disabling values still got full credit for "has a frame."

    Checks each accepted mechanism's ACTUAL resolved value instead:
    - `opt_table_outline(...)`: present unless explicitly disabled via a
      `style="none"`/`"hidden"` kwarg (its only disabling kwarg).
    - `.tab_options(table_border_<side>_...)`: a side counts as framed
      only if its own style/width/color (whichever are set) are all
      non-disabling -- style not "none"/"hidden", width not a zero
      length, color not effectively transparent. Reuses `_is_zero_length`/
      `_is_effectively_transparent`, the same visibility tests
      `_stub_tint_present` already applies elsewhere in this file.
    - `frame(...)` (the scripted skill's helper): kept as an unconditional
      True when called, same as convergence.py's own bare-token behavior
      -- the helper exposes no disabling kwarg. Codex round-6 finding:
      detected via `_has_real_call` (AST-based, same approach `_ast_call_
      blocks` already uses for color mechanics) instead of a source-wide
      regex, which a `def frame(gt, ...):` function definition, a
      comment, or a docstring mentioning "frame(" could all satisfy
      despite no call ever happening.

    Codex round-8 finding: `finalize(gt, path="table.png", **overrides)`
    (`.claude/skills/great-tables-ci/scripts/gt_consistency.py`) is a
    thin passthrough to `gt.gtsave(path, **opts)` -- it sets NO border
    options at all, so it confers no frame whatsoever. That same skill's
    own `gt_check.py` (`check_frame`'s docstring: "finalize(...) is NOT
    accepted -- it only calls gtsave and [does not set border options]")
    already documents this explicitly. `finalize(...)` is removed from
    frame detection here (it still separately confers `render_call_
    present` via `_render_call_present`, which is the check it actually
    satisfies).
    """
    if _has_real_call(source, "frame", allow_bare=True):
        return True
    # Sweep-A finding (round 8): this returned True on the FIRST
    # `opt_table_outline(...)` call that wasn't itself disabling, without
    # checking whether a LATER call in the same source overrides it --
    # `.opt_table_outline().opt_table_outline(style="none")` (enable then
    # disable) read as "outline present" from the first call despite the
    # second, effective call turning it back off. Only the LAST call's
    # own value is consulted now, mirroring the same fix already applied
    # to `_striping_present`/`_option_line_present`.
    outline_blocks = convergence._call_arg_blocks(source, "opt_table_outline")
    if outline_blocks:
        style_val = convergence._kwarg_value(outline_blocks[-1], "style")
        disabled = False
        if style_val is not None:
            unquoted = convergence._unquote(style_val)
            disabled = bool(unquoted and unquoted.strip().lower() in ("none", "hidden"))
        if not disabled:
            return True
    for side in ("left", "right"):
        # Sweep-A finding (round 8): `re.search` returns the FIRST
        # occurrence in the whole source -- a script setting an initial
        # border and overriding it later (or repeating the kwarg across
        # chained `.tab_options(...)` calls) had the ORIGINAL, overridden
        # value trusted instead of the one actually rendered. `re.findall`
        # + the last match mirrors `_option_line_present`'s existing
        # "last occurrence wins" handling of the exact same `table_border_
        # *`-shaped `.tab_options(...)` kwargs for hairlines/dividers.
        style_matches = re.findall(rf"table_border_{side}_style\s*=\s*([^\s,)]+)", source)
        width_matches = re.findall(rf"table_border_{side}_width\s*=\s*([^\s,)]+)", source)
        color_matches = re.findall(rf"table_border_{side}_color\s*=\s*([^\s,)]+)", source)
        if not (style_matches or width_matches or color_matches):
            continue
        if style_matches:
            s = convergence._unquote(style_matches[-1])
            if s and s.strip().lower() in ("none", "hidden"):
                continue
        if width_matches:
            w = convergence._unquote(width_matches[-1])
            if w and convergence._is_zero_length(w):
                continue
        if color_matches:
            col = convergence._unquote(color_matches[-1])
            if col and _is_effectively_transparent(col.strip()):
                continue
        return True
    return False


def _has_visible_tab_style_border(source: str, side_pattern: str, location_pattern: str) -> bool:
    """Like `convergence._has_active_tab_style_border`, but ALSO rejects an
    effectively-transparent border COLOR, and validates that the call's
    OWN `locations=` argument actually matches `location_pattern`.

    Codex round-3 finding: `convergence._has_active_tab_style_border`
    (shared by its own `_hlines_active`/`_vlines_active`) already checks a
    disabling `style="none"/"hidden"` and a zero-length `weight`, but never
    checks whether `color=` is itself invisible -- a `tab_style(style=
    style.borders(sides="top", color="transparent"), ...)` call satisfied
    that function's own "is a border present" test despite rendering no
    visible line at all. Same class of bug as round 2's `_frame_present`
    fix; reuses this file's own `_is_effectively_transparent`.

    Codex round-8 finding: this validated the border's `sides=` value but
    never checked the SURROUNDING `tab_style(locations=...)` argument at
    all -- a border styled with `sides="top"`/`"bottom"` but scoped to
    `loc.column_labels()` or `loc.stub()` (a header-row or stub-column
    rule, not a body row) still counted as a genuine body hairline, and
    likewise a `sides="left"`/`"right"` border on `loc.stub()` counted as
    a column-group divider despite the stub not being a group boundary.
    Per `.claude/skills/great-tables-ci/references/small_color.md`, a
    body hairline is scoped to `loc.body(...)`, and a column-group
    divider is scoped to `loc.body(...)` and/or `loc.column_labels(...)`
    (both drawn so the seam runs the table's full height) -- callers pass
    the `locations` pattern actually associated with what they're
    checking (`_hairlines_present`/`_dividers_present` below).
    """
    for block in convergence._call_arg_blocks(source, "tab_style"):
        style_val = convergence._kwarg_value(block, "style")
        if style_val is None:
            positionals = [
                p for p in convergence._split_top_level(block) if not re.match(r"[A-Za-z_]\w*\s*=", p)
            ]
            style_val = positionals[0] if positionals else None
        if style_val is None:
            continue
        locations_val = convergence._kwarg_value(block, "locations")
        if locations_val is None:
            positionals = [
                p for p in convergence._split_top_level(block) if not re.match(r"[A-Za-z_]\w*\s*=", p)
            ]
            locations_val = positionals[1] if len(positionals) >= 2 else None
        if locations_val is None or not re.search(location_pattern, locations_val):
            continue
        for bm in re.finditer(r"style\s*\.\s*borders\s*\(", style_val):
            open_idx = bm.end() - 1
            close_idx = convergence._scan_balanced_paren(style_val, open_idx)
            if close_idx is None:
                continue
            borders_block = style_val[open_idx + 1:close_idx]
            border_style_val = convergence._kwarg_value(borders_block, "style")
            if border_style_val is not None:
                unquoted = convergence._unquote(border_style_val)
                if unquoted and unquoted.strip().lower() in ("none", "hidden", ""):
                    continue
            weight_val = convergence._kwarg_value(borders_block, "weight")
            if weight_val is not None:
                unquoted_weight = convergence._unquote(weight_val)
                if unquoted_weight and convergence._is_zero_length(unquoted_weight):
                    continue
            color_val = convergence._kwarg_value(borders_block, "color")
            if color_val is not None:
                unquoted_color = convergence._unquote(color_val)
                if unquoted_color and _is_effectively_transparent(unquoted_color.strip()):
                    continue
            sides_val = convergence._kwarg_value(borders_block, "sides")
            if sides_val is None:
                positionals = [
                    p for p in convergence._split_top_level(borders_block) if not re.match(r"[A-Za-z_]\w*\s*=", p)
                ]
                sides_val = positionals[0] if positionals else None
            if sides_val and re.search(rf"['\"](?:{side_pattern})['\"]", sides_val):
                return True
    return False


def _option_line_present(source: str, prefix: str) -> bool | None:
    """True/False if `{prefix}_style`/`{prefix}_width`/`{prefix}_color`
    (whichever are set, taking the LAST occurrence of each -- a script
    commonly chains multiple `.tab_options(...)` calls, and a later one
    overrides an earlier one for the same attribute) together indicate a
    genuinely VISIBLE line; `None` if none of the three are set at all
    (this option-family contributes nothing either way).

    Codex round-6 finding: `_hairlines_present`/`_dividers_present`
    previously checked style/width/color INDEPENDENTLY -- an early
    `return True` as soon as ANY ONE indicated a non-disabling value let a
    non-disabling `style` short-circuit past a genuinely transparent
    `color` set on the SAME options call:
    `table_body_hlines_style="solid", table_body_hlines_color=
    "transparent"` still read as "present" because the style check ran
    (and returned) before the color was ever inspected. All THREE
    attributes that are actually set must agree the line is visible; any
    ONE of them indicating invisibility (an explicit `"none"`/`"hidden"`
    style, a zero-length width, or an effectively-transparent color) is
    authoritative and disables it, regardless of what the others say.
    """
    def _last(attr: str) -> str | None:
        matches = re.findall(rf"{re.escape(prefix)}_{attr}\s*=\s*['\"]([^'\"]+)['\"]", source)
        return matches[-1] if matches else None

    style = _last("style")
    width = _last("width")
    color = _last("color")
    if style is None and width is None and color is None:
        return None
    if style is not None and style.strip().lower() in ("none", "hidden", ""):
        return False
    if width is not None and convergence._is_zero_length(width):
        return False
    if color is not None and _is_effectively_transparent(color.strip()):
        return False
    return True


def _hairlines_present(source: str) -> bool:
    """Like `convergence._hlines_active`, but ALSO validates that
    `table_body_hlines_style`/`_width`/`_color` (whichever are set)
    TOGETHER indicate a genuinely visible line -- see
    `_option_line_present`'s docstring for the exact bug this fixes. The
    `tab_style` fallback mechanism goes through `_has_visible_tab_style_
    border` instead of convergence.py's own (color-blind)
    `_has_active_tab_style_border`, and (round 8) requires the border's
    own `locations=` to actually target `loc.body(...)` -- a hairline
    scoped to the column-labels row or the stub isn't a body row rule.
    """
    if _option_line_present(source, "table_body_hlines"):
        return True
    return _has_visible_tab_style_border(source, "top|bottom", r"loc\s*\.\s*body\s*\(")


def _dividers_present(source: str) -> bool:
    """Like `convergence._vlines_active`, but ALSO validates that
    `table_body_vlines_*`/`column_labels_vlines_*` (whichever of style/
    width/color are set, checked as ONE combination per prefix, not
    independently -- see `_option_line_present`'s docstring) indicate a
    genuinely visible divider. The `tab_style` fallback (round 8) requires
    the border's own `locations=` to target `loc.body(...)` or
    `loc.column_labels(...)` -- per `.claude/skills/great-tables-ci/
    references/small_color.md`'s own column-group-divider recipe, a
    genuine divider is drawn in one or both of those (so the seam runs
    the table's full height); `loc.stub()` or any other location isn't a
    column-group boundary.
    """
    for prefix in ("table_body_vlines", "column_labels_vlines"):
        if _option_line_present(source, prefix):
            return True
    return _has_visible_tab_style_border(source, "left|right", r"loc\s*\.\s*(?:body|column_labels)\s*\(")


def _striping_present(source: str) -> bool:
    """Like `convergence._striping_present`-equivalent bare token search
    (inlined in `parse_design_choices`), but ALSO validates that
    `row_striping_background_color=` (when set) is genuinely visible --
    convergence.py's own regex is a bare `option=` NAME search that never
    even reads the value at all, so `row_striping_background_color=
    "transparent"` satisfied it despite rendering no visible stripe.

    Found during the round-4 proactive sweep for this exact "presence
    without visibility" pattern (not flagged directly by Codex, but the
    same class of bug as `frame_present`/`hairlines_present`/
    `dividers_present`). `opt_row_striping(row_striping: bool = True)`
    (verified against the installed `great_tables` signature) has no
    color parameter -- calling it with a truthy/omitted `row_striping`
    always means "stripe with great_tables' own default, visible color."

    Codex round-5 finding: this originally treated ANY `opt_row_striping(`
    call as striping present, without reading its own `row_striping=`
    argument -- `opt_row_striping(row_striping=False)` (a valid, if
    unusual, EXPLICIT opt-out) was still counted as striping being
    present. Now inspects that argument's actual value.

    Codex round-8 finding: this returned `True` as soon as it found ANY
    enabled/omitted `opt_row_striping(...)` call, without checking
    whether a LATER call in the same source disables it --
    `.opt_row_striping().opt_row_striping(row_striping=False)` (a valid,
    if unusual, override pattern) read as "striping present" from the
    FIRST call despite the SECOND, effective call explicitly turning it
    back off. Only the LAST `opt_row_striping(...)` call's own value is
    consulted now (mirroring `_option_line_present`'s "last call wins"
    pattern already used for hairlines/dividers) -- if that last call
    explicitly disables striping, this falls through to the OTHER
    independent striping mechanisms below (`row_striping_include_table_
    body`, `stripe(...)`, a literal background color) rather than
    returning `False` outright, since striping could still genuinely be
    present via one of those.
    """
    blocks = convergence._call_arg_blocks(source, "opt_row_striping")
    if blocks:
        block = blocks[-1]
        val = convergence._kwarg_value(block, "row_striping")
        if val is None:
            positionals = [
                p for p in convergence._split_top_level(block) if not re.match(r"[A-Za-z_]\w*\s*=", p)
            ]
            val = positionals[0] if positionals else None
        if val is None:
            return True  # omitted -- defaults to True per the installed signature
        unquoted = convergence._unquote(val)
        if not (unquoted and unquoted.strip() == "False"):
            return True  # explicit True, or an unresolvable expression -- benefit of the doubt
        # else: the LAST call explicitly disables striping -- fall through to
        # the other independent mechanisms below instead of returning False.
    #
    # Sweep-A finding (round 8): both checks below used `re.search`, which
    # returns the FIRST match in the whole source -- the same "first call
    # wins" bug already fixed for `opt_row_striping` just above. A script
    # setting `row_striping_include_table_body=True` once and later
    # `=False` (or a background color set once then overridden), across
    # repeated/chained `.tab_options(...)` calls, had the ORIGINAL value
    # trusted instead of the one actually rendered. `re.findall` + the
    # last match mirrors `_option_line_present`'s existing pattern for the
    # exact same `.tab_options(...)`-kwarg-repetition shape.
    include_matches = re.findall(r"row_striping_include_table_body\s*=\s*(\w+)", source)
    if include_matches and include_matches[-1] == "True":
        return True
    if convergence._bare_call_blocks(source, "stripe"):
        return True
    color_matches = re.findall(r"row_striping_background_color\s*=\s*['\"]([^'\"]+)['\"]", source)
    if color_matches and not _is_effectively_transparent(color_matches[-1].strip()):
        return True
    return False


def _render_call_present(source: str) -> bool:
    """True if some `gtsave`/`finalize` call plausibly produced the
    harness's mandated `table.png` artifact. Ported verbatim from the
    closed branch (`render_call_present` itself doesn't exist in the
    version of `convergence.py` merged to `gtc/root` today), plus the
    round-7/8 `_render_target_var_literals` resolution layer for a simple
    same-scope literal-string variable passed as the render target.

    Call sites are located via `_ast_call_blocks` (AST-based, already
    used for color-mechanics detection) rather than `convergence._call_
    arg_blocks`/`_bare_call_blocks` -- this is what gives each call its
    own `(lineno, col_offset)` position, which `_render_target_var_
    literals` (round-8 fix) needs to resolve a variable PER CALL SITE
    instead of by name globally.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    var_literals = _render_target_var_literals(source, tree)
    gtsave_blocks = _ast_call_blocks(source, tree, "gtsave", allow_bare=False)
    if _blocks_target_table_png(gtsave_blocks, "file", 0, var_literals):
        return True
    finalize_blocks = _ast_call_blocks(source, tree, "finalize", allow_bare=True)
    return _blocks_target_table_png(finalize_blocks, "path", 1, var_literals)


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

    Codex round-2 finding: this originally returned `True` merely because
    the argument SLOT was occupied at all, even by a statically-explicit
    `title=None` or `title=""` (or the positional equivalent) -- neither
    of which renders any title text, so this awarded the presence point
    for a header that doesn't actually have one. `_value_present` below
    keeps the benefit of the doubt for a genuinely UNRESOLVABLE expression
    (a variable, an f-string with interpolation) -- there's nothing further
    to verify from static text alone -- but a value that resolves to
    exactly `None` or `""` is provably absent, not merely un-checkable.
    """

    def _value_present(val: str | None) -> bool:
        if val is None:
            return False
        if val.strip() == "None":
            return False
        literal = convergence._extract_text_literal(val)
        if literal == "":
            return False
        return True

    blocks = convergence._call_arg_blocks(source, "tab_header")
    if not blocks:
        return False
    block = blocks[-1]
    kw_val = convergence._kwarg_value(block, kwarg)
    if kw_val is not None:
        return _value_present(kw_val)
    idx = convergence._TAB_HEADER_POSITIONAL_INDEX.get(kwarg)
    if idx is None:
        return False
    positionals = [
        p for p in convergence._split_top_level_quoted(block) if not re.match(r"[A-Za-z_]\w*\s*=", p)
    ]
    if idx >= len(positionals):
        return False
    return _value_present(positionals[idx])


# convergence.py's own `_DATA_COLOR_DEFAULTS` covers na_color/truncate/
# autocolor_text only (current convergence.py never checks `reverse`, so it
# never needed a default for it). `reverse` DOES have a universal
# great_tables default when omitted (`False`) even though it has no
# universal CORRECT value (see check_color_mechanics' own docstring) --
# layered on top locally rather than added to convergence.py's constant.
_DATA_COLOR_DEFAULTS_EXT = {**convergence._DATA_COLOR_DEFAULTS, "reverse": "False"}


def _is_noop_kwargs_expansion(token: str) -> bool:
    """True if `token` (a `**`-prefixed positional split from a call's
    argument list) is a LITERAL empty-dict/no-arg-call expansion --
    `**{}` or `**dict()` -- which is a genuine no-op at runtime (no kwargs
    are actually added by it), not a real, unresolvable kwargs expansion.

    Codex round-3 finding: `.data_color(columns="x", **{})` was previously
    treated identically to a genuinely unresolvable expansion (a variable,
    a non-empty dict built elsewhere) -- scoring every one of that entry's
    na_color/truncate/autocolor_text mechanics as a failure even though an
    empty `**{}` changes nothing and the documented defaults apply exactly
    as if it were omitted entirely. This deliberately does NOT attempt
    general kwargs-expansion resolution -- a non-empty dict literal, a
    dict-returning variable, etc. all still fall through to the existing
    "unresolvable" treatment, unchanged; only the specific, provably-empty
    literal forms are special-cased.
    """
    body = token.strip()[2:].strip()  # strip the leading "**"
    return body in ("{}", "dict()")


def _kwarg_or_default_positional(block: str, name: str, positionals: list[str], index: int) -> str | None:
    """Like `convergence._kwarg_or_default(block, name)`, but ALSO falls
    back to `positionals[index]` when the keyword isn't found -- the
    version of `_kwarg_or_default` merged to `gtc/root` today only supports
    the keyword form, not this positional fallback the closed branch's
    `_color_mechanics` needs (a `.data_color("sales", None, "Blues", [0,
    10], "red", None, False, False, True)` call sets `na_color`/
    `autocolor_text`/`truncate` purely positionally).
    """
    if any(
        p.strip().startswith("**") and not _is_noop_kwargs_expansion(p)
        for p in convergence._split_top_level_quoted(block)
    ):
        return None
    val = convergence._kwarg_value(block, name)
    if val is None and len(positionals) > index:
        val = positionals[index]
    v = convergence._unquote(val)
    if v is None or v == "None":
        return _DATA_COLOR_DEFAULTS_EXT[name]
    return v


def _ast_call_blocks(source: str, tree: ast.Module, func_name: str, allow_bare: bool) -> list[tuple[tuple[int, int], str]]:
    """`(sort_key, args_block_text)` for every GENUINE `ast.Call` node in
    `tree` naming `func_name` -- `allow_bare=True` also matches a bare
    call (`heatmap(...)`), `False` requires an attribute/method call
    (`.data_color(...)`) only, mirroring `data_color`'s own convention
    elsewhere in this file (never called bare). `args_block_text` is
    comment-stripped (an inline `#` comment inside a multi-line call's
    argument list must not corrupt the block text every downstream
    kwarg-parsing helper reads), matching what the old regex-based
    `convergence._call_arg_blocks_pos`/`_bare_call_blocks_pos` returned for
    a genuine call -- this function only changes HOW call sites are
    located, not the shape of what's returned for each one.

    Codex round-2 finding: round-1 fixed docstrings specifically (blanking
    their text before the regex scan), but an ORDINARY string argument --
    e.g. `tab_source_note(source_note="Built with .data_color(...)")` --
    still contains call-shaped text and got misdetected as a real call,
    corrupting the colored-measure count and every check that depends on
    it. Chasing more and more string-shaped exclusions via regex/
    preprocessing is an open-ended, always-catchable-up-with game; walking
    the AST instead only ever visits REAL `ast.Call` nodes in the first
    place -- a string literal's contents are never call nodes and a
    comment is invisible to the parser entirely, so this can't be fooled
    by either, without needing to specifically special-case either one.

    Codex round-3 finding: `node.col_offset`/`end_col_offset` are UTF-8
    BYTE offsets per the AST spec, NOT character offsets into a Python
    `str` -- the previous version of this function indexed `source`
    (character-indexed) directly with these byte offsets via manual
    line-start arithmetic, which silently misaligns as soon as any
    non-ASCII text appears earlier on the SAME line (e.g. `GT(df).
    tab_header(title="Café").data_color(...)`): `source.find("(",
    name_end)` could land on the wrong paren or return -1, silently
    dropping the real call from every color-mechanics check.
    `ast.get_source_segment()` is offset-aware -- it encodes each relevant
    line to UTF-8 bytes before slicing by these byte offsets, then decodes
    back to a real character-indexed string -- so this now asks it
    directly for each Call node's own exact text instead of manually
    walking byte offsets into `source` itself.

    A `Call` node's own span covers its ENTIRE receiver chain, not just
    `funcname(args)` -- for `GT(df).tab_header(...).data_color(cols)`, the
    `.data_color(...)` Call node's segment is the WHOLE chain text starting
    at `GT(df)`, so naively taking the FIRST `"("` in that segment would
    wrongly land on `GT(df)`'s own paren, not `.data_color`'s. Since
    `node.func` (the `Attribute`/`Name` being called) starts at the exact
    same position as `node` itself, `ast.get_source_segment(source,
    node.func)` is guaranteed to be a text PREFIX of `node`'s own segment
    -- stripping that prefix (a plain string operation, not an offset
    calculation) leaves exactly `"(args...)"`, however many lines the
    receiver chain or the call's own arguments span.

    The sort key is `(lineno, col_offset)` -- true SOURCE ORDER
    (interleaving `data_color`/`heatmap` calls correctly) is all this
    needs, and a (line, byte-offset) pair sorts identically to a (line,
    char-offset) pair on the same line (both increase monotonically
    together), so there's no need to convert to a character offset just
    to preserve ordering.
    """
    out: list[tuple[tuple[int, int], str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr == func_name:
            pass
        elif allow_bare and isinstance(func, ast.Name) and func.id == func_name:
            pass
        else:
            continue
        full_segment = ast.get_source_segment(source, node)
        func_segment = ast.get_source_segment(source, func)
        if full_segment is None or func_segment is None or not full_segment.startswith(func_segment):
            continue
        # Codex round-5 finding: legal Python allows whitespace between a
        # callable and its opening paren (`gt.data_color (columns=...)`)
        # -- `rest` then started with a SPACE, not "(", and this call was
        # silently dropped from detection entirely. Strip leading
        # whitespace before checking/extracting the argument block (the
        # Call node's own span still ends exactly at the closing paren
        # with nothing trailing, so only the leading side needs this).
        rest = full_segment[len(func_segment):].lstrip()
        if not (rest.startswith("(") and rest.endswith(")")):
            continue
        block = convergence._strip_line_comments(rest[1:-1])
        out.append(((node.lineno, node.col_offset), block))
    return out


def _ast_fmt_calls(source: str) -> list[tuple[str, str]]:
    """AST-based replacement for `convergence._fmt_calls`: every genuine
    `.fmt_*(...)` method CALL as `(formatter_name, arg_block_text)`, in
    true source order. Mirrors `_ast_call_blocks`'s call-detection
    approach (comment-stripped via `convergence._strip_line_comments`,
    UTF-8-byte-offset-safe via `ast.get_source_segment`, receiver-chain-
    safe by stripping `func_segment` as a text prefix) but matches the
    WILDCARD `fmt_*` method-name family instead of one fixed name, so it
    can't share `_ast_call_blocks`'s single-`func_name` signature
    directly.

    Codex round-7 finding: `convergence._fmt_calls` is a source-wide
    regex (`\\.(fmt_[a-z_]+)\\s*\\(`) -- the exact same bug class this
    file already fixed for color-mechanics call detection
    (`_ast_call_blocks`) and frame/finalize detection (`_has_real_
    call`): a comment (`# gt.fmt_percent(columns="rate")`) or a
    docstring mentioning `.fmt_number(...)` is misdetected as a real
    formatter call, corrupting `_fmt_column_map` and every check that
    depends on it. `runner/convergence.py` is a hard non-goal for this
    slice, so this is the same Tier-1 compatibility-shim pattern used
    throughout this file: walk genuine `ast.Call` nodes instead of
    re-scanning source text.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    out: list[tuple[tuple[int, int], str, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr.startswith("fmt_")):
            continue
        full_segment = ast.get_source_segment(source, node)
        func_segment = ast.get_source_segment(source, func)
        if full_segment is None or func_segment is None or not full_segment.startswith(func_segment):
            continue
        rest = full_segment[len(func_segment):].lstrip()
        if not (rest.startswith("(") and rest.endswith(")")):
            continue
        block = convergence._strip_line_comments(rest[1:-1])
        out.append(((node.lineno, node.col_offset), func.attr, block))
    out.sort(key=lambda e: e[0])
    return [(name, block) for _, name, block in out]


def _quoted_string_literal_value(value_text: str | None) -> str | None:
    """The unquoted value ONLY if `value_text` is an actual quoted string
    literal (e.g. `"sequential"`) -- `None` for anything else, including a
    bare identifier/variable reference whose NAME happens to textually
    match a value this file specifically checks for (e.g. `kind=kind` or
    `heatmap(..., hue=navy_var, ...)` -- a variable, not the literal
    string `"sequential"`/`"navy"`). `convergence._unquote` alone can't
    distinguish these: it happily returns an identifier's own name
    unchanged when there's no quote to strip, which then gets trusted as
    if it were a real value by any caller that compares it directly.

    Codex round-3 finding: `heatmap(gt, cols, kind=kind, ...)` (kind
    passed via a variable) had its raw source text ("kind", the variable
    name) stored and then compared as if it were a literal value,
    contradicting this file's own stated benefit-of-the-doubt convention
    for dynamic expressions elsewhere. Applied to both `kind` and the
    heatmap helper's `hue` (-> `palette`) extraction just below -- the
    identical risk applies to both (round 2's own band-harmonization fix
    now trusts a helper `palette` value directly whenever it matches a
    recognized Dark-Academia family name, which makes an unverified bare
    identifier there just as exploitable as `kind`).
    """
    if value_text is None:
        return None
    v = value_text.strip()
    if len(v) >= 2 and v[0] in "'\"" and v[-1] == v[0]:
        return convergence._unquote(v)
    return None


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


def _is_unresolvable_columns_selector(cols_val: str) -> bool:
    """True if `cols_val`'s text is a column-SELECTOR expression
    (`cs.starts_with(...)` and friends) that `convergence._resolve_columns_
    list` can't expand from static source text alone (it would need the
    real render-time schema).

    Codex round-2 finding: `convergence._resolve_columns_list` returns `[]`
    for this case -- but it ALSO returns `[]` for a genuinely-empty
    explicit columns list, and those two are not the same thing: one means
    "unknowable from source text," the other means "explicitly targets
    nothing." Conflating them silently excluded a selector's real (and
    very possibly non-empty) target columns from every colored-measure
    check that iterates them (identity, signedness, domain, striping
    coverage). Mirrors the exact selector-expression pattern `_resolve_
    columns_list` itself already recognizes as unresolvable.
    """
    return bool(re.match(r"^cs\s*\.\s*\w+\s*\(", cols_val.strip()))


# A distinct sentinel for "columns targeted by this call are UNKNOWN/
# unresolvable from static text" (e.g. `columns=cs.starts_with("rate_")`)
# -- deliberately NOT the same value as `None`, which is Tier 1's existing
# sentinel for "omitted/explicit `columns=None`, i.e. targets EVERY
# column" (`_mechanics_columns` expands `None` against the full visible
# schema). Codex round-5 finding: round 4 used `None` for BOTH cases,
# which made `_mechanics_columns` misread a genuinely-unresolvable
# selector as "colors everything" -- the opposite of the intended
# benefit-of-the-doubt ("we don't know, so credit/blame nothing specific
# to it") treatment.
_UNRESOLVED_COLUMNS = object()


def _enrich_color_mechanics(source: str) -> list[dict]:
    """One dict per colored-measure call (`data_color`/`heatmap`), in TRUE
    source order, carrying `columns`/`na_color`/`truncate`/`autocolor_text`
    PLUS `palette`/`domain`/`via_helper`/`kind`/`reverse` -- the per-entry
    fields `check_colored_measure_selection`, `check_sequential_vs_
    diverging`, `check_domain_computation`, `check_hue_collision`,
    `check_band_hue_harmonization`, and `check_color_mechanics` below all
    depend on and were 14-round Codex-reviewed against.

    This is a port of the closed `gtc/comparator` branch's OWN
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

    Call sites are located via the AST (`_ast_call_blocks`), not a
    source-wide regex scan (Codex round-1 found a docstring mentioning
    `.data_color(...)` got misdetected as a real call; round-2 found an
    ORDINARY string argument, e.g. a source-note explaining "Built with
    `.data_color(...)`", has the exact same problem -- an AST `ast.Call`
    node is never text sitting inside a string literal or a comment, so
    this can't be fooled by either without chasing more string patterns).
    An unparseable candidate (invalid syntax) returns no entries at all --
    strictly more honest than a regex scan that would still pattern-match
    broken text; every check that reads this list already degrades
    gracefully for a candidate with zero colored measures.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    var_map = convergence._list_var_map(source)
    entries: list[tuple[tuple[int, int], dict]] = []
    for pos, block in _ast_call_blocks(source, tree, "data_color", allow_bare=False):
        # `data_color(columns, rows, palette, domain, ...)` -- shared once so
        # `rows`/`columns`/`domain` positional fallbacks (slots 1/0/3) all
        # line up against the SAME split.
        #
        # Codex round-6 finding: a `**`-prefixed expansion token (whether
        # the no-op `**{}`/`**dict()` round-3 already special-cases, or a
        # genuinely unresolvable `**overrides`) was left IN this list, so
        # `.data_color("x", **{})` had `positionals = ['"x"', '**{}']` --
        # `rows_val = positionals[1]` then picked up the literal `"**{}"`
        # text, which isn't the string `"None"`, so the ENTIRE call was
        # wrongly discarded as row-restricted. A `**expansion` can only
        # ever be the LAST token in a call's argument list (Python doesn't
        # allow a positional arg after `**kwargs`), so dropping it from
        # this list never shifts any REAL positional argument's index --
        # it's always safe to exclude, whether or not it happens to be a
        # no-op.
        positionals = [
            p for p in convergence._split_top_level_quoted(block)
            if not re.match(r"[A-Za-z_]\w*\s*=", p) and not p.strip().startswith("**")
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
            resolved_columns = None  # omitted/explicit None -- targets EVERY column
        elif _is_unresolvable_columns_selector(cols_val):
            resolved_columns = _UNRESOLVED_COLUMNS  # unknown -- NOT the same as "every column"
        else:
            resolved_columns = convergence._resolve_columns_list(cols_val, var_map)
        domain_val = convergence._kwarg_value(block, "domain")
        if domain_val is None and len(positionals) > 3:
            domain_val = positionals[3]
        palette_val = convergence._kwarg_value(block, "palette")
        if palette_val is None and len(positionals) > 2:
            palette_val = positionals[2]
        entries.append((pos, {
            "columns": resolved_columns,
            "palette": _palette_of_block_positional(block, positionals),
            # Raw, UNCLASSIFIED palette source text (e.g. a literal hex-
            # list `["#112233", "#445566"]`, not just the generic "custom"
            # bucket `palette` collapses it to) -- used by check_hue_
            # collision to tell two DIFFERENT custom gradients apart
            # instead of treating any two "custom" palettes as an
            # automatic collision (Codex round-4 finding).
            "palette_raw": palette_val.strip() if palette_val else None,
            "domain": domain_val,
            # data_color(columns, rows, palette, domain, na_color, alpha,
            # reverse, autocolor_text, truncate) -- positional slots 4/6/7/8.
            "na_color": _kwarg_or_default_positional(block, "na_color", positionals, 4),
            "reverse": _kwarg_or_default_positional(block, "reverse", positionals, 6),
            "truncate": _kwarg_or_default_positional(block, "truncate", positionals, 8),
            "autocolor_text": _kwarg_or_default_positional(block, "autocolor_text", positionals, 7),
            "via_helper": False,
        }))
    for pos, block in _ast_call_blocks(source, tree, "heatmap", allow_bare=True):
        heatmap_cols_val = convergence._heatmap_columns_raw(block)
        if heatmap_cols_val is not None and _is_unresolvable_columns_selector(heatmap_cols_val):
            resolved_heatmap_columns = _UNRESOLVED_COLUMNS  # unknown -- NOT "every column"
        else:
            resolved_heatmap_columns = convergence._resolve_columns_list(heatmap_cols_val, var_map)
        hue_raw = convergence._kwarg_value(block, "hue")
        entries.append((pos, {
            "columns": resolved_heatmap_columns,
            "palette": _quoted_string_literal_value(hue_raw) or "default",
            "palette_raw": hue_raw.strip() if hue_raw else None,
            "domain": convergence._kwarg_value(block, "domain"),
            "kind": _quoted_string_literal_value(convergence._kwarg_value(block, "kind")),
            "na_color": "#808080",
            "truncate": "False",
            "autocolor_text": "True",
            "reverse": "False",
            "via_helper": True,
        }))
    entries.sort(key=lambda e: e[0])
    return [d for _, d in entries]


def _fmt_column_map(source: str) -> dict[str, str | bool]:
    """Best-effort `{source column -> the EFFECTIVE fmt_* name}`, with a
    special `convergence._ALL_COLUMNS` sentinel key for "every column not
    otherwise listed gets THIS formatter."

    Codex round-5 finding: the version of `_fmt_column_map` merged to
    `gtc/root` clears its whole map (`out.clear()`) whenever a LATER
    `fmt_*(...)` call omits `columns=` (meaning "apply to every column"),
    discarding the "every column now gets this formatter" fact entirely
    instead of recording it -- despite that function's OWN docstring (and
    its callers, `check_fmt_semantic_type`/`check_summary_row_formatting`,
    which already do `fmt_map.get(col, fmt_map.get(convergence.
    _ALL_COLUMNS))`) documenting exactly this `_ALL_COLUMNS` sentinel as
    the intended behavior. A table using a single unqualified
    `.fmt_number()` (or similar) for every column scored as "no formatting
    applied at all" for every semantic-typed column. `runner/convergence.py`
    is a hard non-goal for this slice (same pattern as this file's Tier-1
    compatibility shim from the vendoring commit), so this is a straight,
    verbatim port of the CORRECT implementation from the closed
    `gtc/comparator` branch (verified via `git show gtc/comparator:
    runner/convergence.py`) -- built only from `convergence._fmt_calls`
    (still present, unchanged) and other still-present low-level
    primitives, replacing the buggy version's output entirely rather than
    patching it (there's nothing to salvage from an already-cleared dict).

    Codex round-7 findings: (1) call detection now goes through `_ast_
    fmt_calls` (AST-based) instead of `convergence._fmt_calls` (a
    source-wide regex misdetecting a comment or docstring mentioning
    `.fmt_number(...)` as a real call -- same bug class already fixed
    here for color-mechanics/frame detection); (2) `**`-prefixed tokens
    are now excluded from `positionals` entirely (mirroring the
    identical round-6 fix for `_enrich_color_mechanics` -- a
    `**expansion` can only ever be the LAST token in a call's args per
    Python syntax, so dropping it never shifts any real positional
    index), and a genuinely no-op expansion (`**{}`/`**dict()`, via
    `_is_noop_kwargs_expansion`) no longer counts toward `row_
    restricted` -- previously `.fmt_number(columns="x", **{})` was
    treated identically to a genuinely unresolvable row-restricting
    expansion and lost its formatting credit entirely, despite the
    empty expansion changing nothing at runtime.
    """
    var_map = convergence._list_var_map(source)
    out: dict[str, str | bool] = {}
    for name, block in _ast_fmt_calls(source):
        positionals = [
            p for p in convergence._split_top_level_quoted(block)
            if not re.match(r"[A-Za-z_]\w*\s*=", p) and not p.strip().startswith("**")
        ]
        val = convergence._kwarg_value(block, "columns")
        if val is None:
            val = positionals[0] if positionals else None
        rows_val = convergence._kwarg_value(block, "rows")
        if rows_val is None and len(positionals) > 1:
            rows_val = positionals[1]
        has_expansion = any(
            p.strip().startswith("**") and not _is_noop_kwargs_expansion(p)
            for p in convergence._split_top_level_quoted(block)
        )
        row_restricted = has_expansion or (rows_val is not None and rows_val.strip() != "None")
        if row_restricted:
            if val is None or val.strip() == "None":
                out.clear()
            else:
                for col in convergence._resolve_columns_list(val, var_map):
                    if out.get(col, out.get(convergence._ALL_COLUMNS)) != name:
                        # `False` explicitly excludes JUST this column from
                        # the `_ALL_COLUMNS` fallback, rather than dropping
                        # the sentinel entirely and losing formatting
                        # credit for every OTHER, unaffected column too.
                        out[col] = False
            continue
        if val is None or val.strip() == "None":
            out.clear()
            out[convergence._ALL_COLUMNS] = name
            continue
        for col in convergence._resolve_columns_list(val, var_map):
            out[col] = name
    return out


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
    # Codex round-2 finding: convergence.py's own `frame_present` is a bare
    # token search that doesn't check whether the border option's actual
    # value is visible (nonzero width, non-"none" style, non-transparent
    # color) -- see `_frame_present`'s docstring.
    tier1["frame_present"] = _frame_present(source)
    # Codex round-3 finding: convergence.py's own `hairlines_present`/
    # `dividers_present` don't validate that a `color=` value is actually
    # visible (a transparent color satisfies their regexes), and the
    # `vlines` mechanism also never checked for a zero-length width --
    # see `_hairlines_present`/`_dividers_present`'s docstrings.
    tier1["hairlines_present"] = _hairlines_present(source)
    tier1["dividers_present"] = _dividers_present(source)
    # Round-4 proactive sweep finding (same class as the frame/hairlines/
    # dividers fixes above, not flagged directly by Codex): convergence.py's
    # own `striping_present` is a bare `option=` NAME search that never
    # reads the value -- see `_striping_present`'s docstring.
    tier1["striping_present"] = _striping_present(source)
    # Codex round-5 finding: convergence.py's own `_fmt_column_map` clears
    # its whole map instead of preserving an `_ALL_COLUMNS` sentinel when a
    # formatter call omits `columns=` -- see `_fmt_column_map`'s docstring.
    tier1["fmt_column_map"] = _fmt_column_map(source)
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
        # Codex round-8 finding: convergence.py's own `_find_band_color`
        # (which originally computed `heading_band_hex`) returns the
        # FIRST occurrence via `re.search`, not the LAST -- when a script
        # sets an initial band color and overrides it later (or repeats
        # the kwarg across chained `tab_options()` calls), the ORIGINAL,
        # overridden value was trusted instead of the one actually
        # rendered. Re-resolve to the last occurrence via the local
        # `_find_band_color_last` shim before normalizing/classifying
        # (falls back to convergence.py's own value if, for whatever
        # reason, the shim finds nothing -- keeps this a strict
        # improvement, never a regression).
        tier1["heading_band_hex"] = _find_band_color_last(source) or tier1["heading_band_hex"]
        # Codex round-7 finding: `_classify_hue_extended` (and convergence.
        # py's own `_band_shade`, both called below) only recognize HEX
        # strings -- a CSS-equivalent literal like `column_labels_
        # background_color="rgb(244, 214, 214)"` (== `#F4D6D6`) previously
        # failed to classify at all, collapsing BOTH the hue and the shade
        # to "unknown"/"none" despite rendering an identical, classifiable
        # color. Same "raw string, not rendered outcome" gap already fixed
        # for `na_color`/stub-tint -- reuses the same `_normalize_css_
        # color` normalizer (falling back to the raw text when it's
        # already a plain hex or genuinely unparseable, so this is a
        # strict superset of the previous hex-only behavior).
        normalized_band_hex = _normalize_css_color(tier1["heading_band_hex"]) or tier1["heading_band_hex"]
        tier1["heading_band_hue"] = _classify_hue_extended(normalized_band_hex)
        tier1["heading_band_shade"] = convergence._band_shade(normalized_band_hex)
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

    `entry["columns"] is _UNRESOLVED_COLUMNS` is a DIFFERENT sentinel --
    an unresolvable column-selector expression (`cs.starts_with(...)`),
    genuinely UNKNOWN rather than "every column." Codex round-5 finding:
    round 4 conflated this with the `None` ("every column") sentinel,
    so an unresolvable selector was misread as coloring the entire table.
    Returns an empty list for it instead -- benefit of the doubt means
    "credit/blame nothing specific to this entry," not "assume the most
    generous possible interpretation."
    """
    cols = entry.get("columns")
    if cols is _UNRESOLVED_COLUMNS:
        return []
    if cols is not None:
        return cols
    tier2 = fp["tier2"]
    visible = _visible_columns(fp) - {tier2.get("stub_column"), tier2.get("group_column")}
    return sorted(visible)


def _distinct_colored_measures(mechanics: list[dict], fp: dict) -> list[dict]:
    """One REPRESENTATIVE ENTRY per distinct `(palette, domain, columns)`
    key in `mechanics` -- the same conceptual measure applied via multiple
    calls that share a palette, domain, AND target the same columns
    collapses to one entry; a DIFFERENT set of target columns means a
    genuinely different measure even when its palette and domain happen
    to coincide. Returns full entry dicts (not just the key tuple) so
    callers that need more than palette/domain/columns -- e.g. `palette_
    raw`, for telling two different custom hex-list palettes apart -- can
    still get at it.

    Codex round-3 finding: every caller of this dedup previously keyed
    purely on `(palette, domain)`, which collapsed 3 GENUINELY DIFFERENT
    measures (different target columns, matching palette+domain purely by
    coincidence) into 1 -- silently dodging the ≤2-measure ceiling and
    under-reporting the hue-collision/band-harmonization checks. `columns`
    here is the RESOLVED column tuple (via `_mechanics_columns`, the same
    resolution every other check already uses), not the raw, possibly-
    `None` `entry["columns"]` sentinel -- two entries whose `columns=None`
    sentinel resolves to the SAME actual visible-column set still
    correctly collapse to one measure. Sorted for a deterministic
    iteration order (mirrors round-2's hue-collision fix, which stopped
    trusting Python's hash-randomized set order for this same kind of
    dedup).
    """
    seen: dict[tuple, dict] = {}
    for m in mechanics:
        key = (m.get("palette"), m.get("domain"), tuple(_mechanics_columns(m, fp)))
        seen.setdefault(key, m)
    return sorted(
        seen.values(),
        key=lambda m: ((m.get("palette") or ""), (m.get("domain") or ""), tuple(_mechanics_columns(m, fp))),
    )


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

def _row_multiset_identity(
    candidate_row_ids: list | None,
    truth_row_ids: list | None,
    *,
    candidate_group_ids: list | None = None,
    truth_group_ids: list | None = None,
) -> dict:
    """Like `execution_tier.row_set_identity`, but falls back to a
    MULTISET (duplicate-COUNT-preserving) comparison of bare row ids,
    instead of that function's own bare-SET fallback, specifically when
    grouping is present on exactly one side and at least one side's row
    ids contain duplicates.

    Codex round-7 finding: `execution_tier.row_set_identity` only keys by
    `(group_id, row_id)` when BOTH sides supply group ids (`use_groups =
    bool(candidate_group_ids) and bool(truth_group_ids)`) -- when only
    the ground truth is grouped (a candidate that chose NOT to group is
    itself a legitimate, separately-judged choice per `check_grouping_
    choice_quality`), it falls back to comparing BARE row-id SETS, which
    silently drops both the group boundaries AND each row's duplicate
    CARDINALITY (Python's `set()` collapses repeats). A ground truth with
    a stub id repeated once per group (e.g. "January" appearing once in
    each of 6 year-groups) then reads as a single set entry "January" --
    satisfied by a candidate with just ONE ungrouped "January" row,
    reporting a false `exact=True` row-identity match despite covering
    only 1/6th of the required rows.

    `runner/execution_tier.py` is a hard non-goal for this slice, so this
    wraps it rather than editing it: delegate straight through for every
    case that function already gets right (either side `None`, both-
    grouped, both-ungrouped, or grouped-on-exactly-one-side but with no
    actual duplicate row ids to lose), and only take over the comparison
    directly -- via `Counter` multisets, ignoring group labels on the
    grouped side too since only one side has them to compare against --
    for the narrow case its own set-based fallback mishandles.
    """
    if candidate_row_ids is None or truth_row_ids is None:
        return execution_tier.row_set_identity(
            candidate_row_ids, truth_row_ids,
            candidate_group_ids=candidate_group_ids, truth_group_ids=truth_group_ids,
        )
    use_groups = bool(candidate_group_ids) and bool(truth_group_ids)
    asymmetric_grouping = bool(candidate_group_ids) != bool(truth_group_ids)
    cand_norm = [execution_tier.normalize_id(r) for r in candidate_row_ids]
    truth_norm = [execution_tier.normalize_id(r) for r in truth_row_ids]
    has_duplicates = len(cand_norm) != len(set(cand_norm)) or len(truth_norm) != len(set(truth_norm))
    if use_groups or not (asymmetric_grouping and has_duplicates):
        return execution_tier.row_set_identity(
            candidate_row_ids, truth_row_ids,
            candidate_group_ids=candidate_group_ids, truth_group_ids=truth_group_ids,
        )
    cand_counts, truth_counts = Counter(cand_norm), Counter(truth_norm)
    matched = sum((cand_counts & truth_counts).values())
    cand_total, truth_total = sum(cand_counts.values()), sum(truth_counts.values())
    precision = (matched / cand_total) if cand_total else (1.0 if not truth_total else 0.0)
    recall = (matched / truth_total) if truth_total else (1.0 if not cand_total else 0.0)
    return {
        "matched": matched,
        "candidate_only": sorted((cand_counts - truth_counts).elements()),
        "truth_only": sorted((truth_counts - cand_counts).elements()),
        "precision": precision,
        "recall": recall,
        "exact": cand_counts == truth_counts,
    }


def check_row_selection_identity(cand: dict, truth: dict, meta: dict) -> CheckResult:
    name = "Row/entity selection identity"
    truth_ids = truth["tier2"].get("row_ids") if truth["tier2"].get("ok") else None
    cand_ids = cand["tier2"].get("row_ids") if cand["tier2"].get("ok") else None
    if truth_ids is None:
        return _na(name, "ground truth has no stub column; row identity not verifiable")
    if cand_ids is None:
        return CheckResult(name, 10, 0, False, "candidate has no stub column; row selection unverifiable")
    cand_group_ids = cand["tier2"].get("row_group_ids")
    truth_group_ids = truth["tier2"].get("row_group_ids")
    # Codex round-4 finding: execution_tier.row_set_identity compares
    # (group_id, row_id) tuples LITERALLY, so a candidate that groups the
    # exact right rows the exact right way but spells its group labels
    # differently than the ground truth (e.g. "FY2010"/"FY2011" instead of
    # "2010"/"2011") lost row-identity credit purely from the label
    # difference -- relabel the candidate's group ids to their value-
    # matched truth counterpart first (see `_relabel_candidate_groups`).
    if cand_group_ids and truth_group_ids:
        relabeled = _relabel_candidate_groups(cand_ids, cand_group_ids, truth_ids, truth_group_ids)
        if relabeled is not None:
            cand_group_ids = relabeled
    result = _row_multiset_identity(
        cand_ids, truth_ids,
        candidate_group_ids=cand_group_ids,
        truth_group_ids=truth_group_ids,
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
    # Count DISTINCT (palette, domain, columns) triples as "measures", not
    # raw .data_color()/heatmap() CALLS -- the same conceptual measure
    # applied via multiple calls that share a palette+domain AND target
    # the same columns is one measure, not N, and must not be rejected as
    # exceeding the ≤2 ceiling. Columns are part of the key (Codex round-3
    # finding) so 3 GENUINELY DIFFERENT measures that merely happen to
    # share a palette+domain, but target different columns, correctly
    # count as 3, not 1.
    n_measures = len(_distinct_colored_measures(cand_mechanics, cand))
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
        #
        # Codex round-4 finding: also intersect with the candidate's
        # VISIBLE columns -- without this, a candidate could color a
        # HIDDEN duplicate of a measure (via `cols_hide(...)`) while
        # showing an uncolored visible duplicate with the same values, and
        # this credited full coverage even though the reader never
        # actually sees any coloring on the rendered table.
        colored_cols = {c for m in cand_mechanics for c in _mechanics_columns(m, cand)} & _visible_columns(cand)
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


def _hungarian_min_cost(cost: list[list[float]]) -> list[int]:
    """Solve the assignment problem on a SQUARE `cost` matrix (minimize
    total cost of a one-to-one row->column assignment) via the classic
    O(n^3) Hungarian algorithm (primal-dual / shortest-augmenting-path
    formulation). Returns `assignment` where `assignment[i]` is the column
    index assigned to row `i`.

    Used by `_group_partition_match` to replace a GREEDY "each truth group
    independently picks whichever candidate group currently overlaps it
    most" approach (Codex round-2 finding: that greedy approach reports a
    false `one_to_one=False` whenever multiple truth groups TIE on overlap
    with the same candidate group -- e.g. a candidate that simply relabels
    every group, "2010"/"2011" -> "FY2010"/"FY2011", where every cross-pair
    overlap ties because every group shares the same 12 month labels; the
    greedy loop then designates the SAME candidate group for every truth
    group instead of finding the correct one-to-one relabeling). This
    computes the GLOBALLY OPTIMAL one-to-one assignment (maximizing total
    overlap, via minimizing negated overlap as cost) instead, which is
    guaranteed to find a perfect relabeling whenever one exists -- and,
    when every candidate is equally good (the fully-tied case), still
    returns SOME valid one-to-one assignment achieving the same optimal
    total, which is all correctness here actually requires.

    Standard reference implementation (e.g. the "Hungarian algorithm with
    potentials" commonly attributed to the e-maxx/competitive-programming
    literature) -- 1-indexed internally to match that reference exactly,
    translated to 0-indexed at the boundary.
    """
    n = len(cost)
    INF = float("inf")
    u = [0.0] * (n + 1)
    v = [0.0] * (n + 1)
    p = [0] * (n + 1)  # p[j] = 1-indexed row assigned to column j, 0 = none
    way = [0] * (n + 1)
    for i in range(1, n + 1):
        p[0] = i
        j0 = 0
        minv = [INF] * (n + 1)
        used = [False] * (n + 1)
        while True:
            used[j0] = True
            i0 = p[j0]
            delta = INF
            j1 = -1
            for j in range(1, n + 1):
                if not used[j]:
                    cur = cost[i0 - 1][j - 1] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j] = cur
                        way[j] = j0
                    if minv[j] < delta:
                        delta = minv[j]
                        j1 = j
            for j in range(n + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while j0:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
    assignment = [0] * n
    for j in range(1, n + 1):
        if p[j] != 0:
            assignment[p[j] - 1] = j - 1
    return assignment


def _hungarian_group_assignment(
    cand_groups: dict[Any, Counter], truth_groups: dict[Any, Counter],
) -> tuple[list, list, list[list[int]], list[int]]:
    """Shared setup for `_group_partition_match`/`_relabel_candidate_groups`:
    sorted truth/candidate group-id lists, their pairwise row-content
    overlap matrix (square, zero-padded to the larger side -- a truth/
    candidate group beyond the other side's actual count is a "dummy"
    with zero overlap, contributing nothing), and the Hungarian-optimal
    one-to-one assignment (`assignment[i]` is the column index -- into
    `cand_keys` -- assigned to `truth_keys[i]`; an index `>= len(cand_keys)`
    means that truth group has no real candidate counterpart in the
    optimal assignment).
    """
    truth_keys = sorted(truth_groups, key=str)
    cand_keys = sorted(cand_groups, key=str)
    n = max(len(truth_keys), len(cand_keys))
    overlap_matrix = [[0] * n for _ in range(n)]
    for i, tg in enumerate(truth_keys):
        for j, cg in enumerate(cand_keys):
            overlap_matrix[i][j] = _group_overlap(truth_groups[tg], cand_groups[cg])
    cost = [[-overlap_matrix[i][j] for j in range(n)] for i in range(n)]  # minimize cost == maximize overlap
    assignment = _hungarian_min_cost(cost)
    return truth_keys, cand_keys, overlap_matrix, assignment


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
    # Codex round-2 finding: the ORIGINAL greedy version had every truth
    # group independently pick whichever candidate group overlapped it
    # most -- correct when overlaps are unambiguous, but wrong under ties
    # (e.g. a candidate that relabels "2010"/"2011" to "FY2010"/"FY2011":
    # every group shares the same 12 month labels, so every cross-pair
    # overlap ties, and the greedy loop designated the SAME candidate
    # group for every truth group, falsely reporting `one_to_one=False`
    # for an actually-perfect relabeling). Solving this as a genuine
    # one-to-one ASSIGNMENT problem (maximize total overlap across a
    # global one-to-one mapping, via the Hungarian algorithm) finds the
    # correct relabeling whenever one exists, and still returns SOME valid
    # one-to-one mapping achieving the same optimal total when multiple
    # mappings tie -- exactly the guarantee this check needs.
    truth_keys, cand_keys, overlap_matrix, assignment = _hungarian_group_assignment(cand_groups, truth_groups)
    agree = 0
    matched_cand_indices: set[int] = set()
    for i in range(len(truth_keys)):
        j = assignment[i]
        if j < len(cand_keys):
            agree += overlap_matrix[i][j]
            matched_cand_indices.add(j)
    # A valid partition match additionally requires the mapping to be
    # one-to-one -- two DIFFERENT truth groups must not designate the SAME
    # candidate group (that would mean the candidate merged two real
    # groups into one). The Hungarian assignment is one-to-one BY
    # CONSTRUCTION (each row index maps to a distinct column index), so
    # this only fails when a truth group had no real candidate
    # counterpart to be assigned at all (mapped to a dummy column).
    one_to_one = len(matched_cand_indices) == len(truth_keys)
    match = one_to_one and agree / shared_rows >= execution_tier._MATCH_THRESHOLD
    return {"comparable": True, "match": match, "shared_rows": shared_rows}


def _relabel_candidate_groups(
    candidate_row_ids: list, candidate_group_ids: list, truth_row_ids: list, truth_group_ids: list,
) -> list | None:
    """Remap each candidate group id to whichever TRUTH group id its row
    CONTENT overlaps with most (via the same Hungarian-optimal one-to-one
    assignment `_group_partition_match` uses), so a candidate that groups
    the exact right rows the exact right way, but spells its group labels
    differently than the ground truth (e.g. "FY2010"/"FY2011" instead of
    "2010"/"2011"), doesn't lose row-identity credit purely from the label
    difference. Returns `None` when there's nothing to relabel against (no
    shared row content at all between any candidate/truth group pair) --
    the caller falls back to the candidate's own, unrelabeled group ids in
    that case.

    Codex round-4 finding: `execution_tier.row_set_identity` compares
    `(group_id, row_id)` tuples LITERALLY -- necessary so a repeated stub
    id across groups doesn't dedupe away (see that function's own
    docstring), but it means a pure group RELABELING (same partition,
    different label text) was scored as a near-total row-identity
    failure. `runner/execution_tier.py` is a hard non-goal for this slice,
    so this relabels the candidate's group ids BEFORE calling it, reusing
    the exact same Hungarian-assignment machinery `_group_partition_match`
    (built in round 2 for the analogous "same partition, different
    labels" problem in `check_explicit_instructions`) rather than
    inventing new matching logic.
    """
    cand_groups = _group_row_multisets(candidate_row_ids, candidate_group_ids)
    truth_groups = _group_row_multisets(truth_row_ids, truth_group_ids)
    if not cand_groups or not truth_groups:
        return None
    truth_keys, cand_keys, overlap_matrix, assignment = _hungarian_group_assignment(cand_groups, truth_groups)
    relabel: dict[Any, Any] = {}
    for i, tg in enumerate(truth_keys):
        j = assignment[i]
        if j < len(cand_keys) and overlap_matrix[i][j] > 0:
            relabel[cand_keys[j]] = tg
    if not relabel:
        return None
    return [relabel.get(gid, gid) for gid in candidate_group_ids]


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
                # Codex round-4 finding: `col` is the TRUTH's own source
                # column name -- resolving it against the CANDIDATE's
                # columns by that same name (the previous approach, via
                # `computed_value_correctness`, which itself only ever
                # compares same-named columns) failed this required-sort
                # instruction outright for a candidate that renamed the
                # column but kept its values and order exactly right (same
                # class of bug check_fmt_semantic_type/check_column_set
                # had). `match_measure_by_value`'s value-based search
                # (name-blind, used throughout this file) both resolves
                # the renamed column AND verifies its values match the
                # ground truth's well enough to trust -- a candidate
                # satisfying "sorted" by replacing the column with an
                # unrelated monotonic sequence still won't value-match and
                # so still won't resolve here.
                matched_col = execution_tier.match_measure_by_value(cand["tier2"], truth["tier2"], col)
                if matched_col is None:
                    ok = False
                else:
                    vals = cand["tier2"].get("columns", {}).get(matched_col)
                    if not vals:
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
    # Codex round-3 finding: a raw-NAME Jaccard double-penalized a
    # renamed-but-value-equivalent column (same class of bug round 2 fixed
    # in check_fmt_semantic_type) -- a candidate showing the ground
    # truth's `hp` values under the name `horsepower` had `hp` counted as
    # missing AND `horsepower` counted as an extra candidate-only column,
    # even though the measure IS actually shown. For every truth column
    # not already present by name, look for a value-matched candidate
    # column (via `execution_tier.match_measure_by_value`, the same
    # value-based matching used throughout this file) and relabel it to
    # the candidate's own name before computing set overlap -- a renamed
    # match then correctly reads as present in both sets, without
    # inflating the union with the truth column's original name (which
    # nothing on the candidate side actually corresponds to anymore).
    # Codex round-6 finding: matching each truth column independently let
    # TWO different truth columns with IDENTICAL values (e.g. a genuinely
    # duplicated measure) both value-match the SAME single candidate
    # column when the candidate kept only ONE renamed copy -- both entries
    # then collapsed to that one candidate name in `normalized_truth_cols`
    # below, hiding that the candidate is actually missing a whole column.
    # Consuming each candidate match ONE-TO-ONE (sorted for a
    # deterministic processing order, since which truth column "wins" a
    # genuine tie matters here) means a second truth column that would
    # otherwise re-claim an already-used candidate column instead gets NO
    # rename -- it correctly stays a real gap in the Jaccard math.
    renamed_truth_to_cand: dict[str, str] = {}
    used_cand_cols: set[str] = set()
    if cand["tier2"].get("ok") and truth["tier2"].get("ok"):
        for tc in sorted(truth_cols - cand_cols):
            matched_col = execution_tier.match_measure_by_value(cand["tier2"], truth["tier2"], tc)
            if matched_col is not None and matched_col in cand_cols and matched_col not in used_cand_cols:
                renamed_truth_to_cand[tc] = matched_col
                used_cand_cols.add(matched_col)
    normalized_truth_cols = {renamed_truth_to_cand.get(tc, tc) for tc in truth_cols}
    union = cand_cols | normalized_truth_cols
    jaccard = len(cand_cols & normalized_truth_cols) / len(union) if union else 1.0
    pts = _round_points(jaccard, 4)
    detail = (
        f"visible-column overlap {jaccard:.2f} (candidate-only={sorted(cand_cols - normalized_truth_cols)}, "
        f"missing={sorted(normalized_truth_cols - cand_cols)})"
    )
    if renamed_truth_to_cand:
        detail += f"; value-matched renamed columns: {renamed_truth_to_cand}"
    return CheckResult(name, 4, pts, cand_cols == normalized_truth_cols, detail)


def check_grouping_existence(cand: dict, truth: dict, meta: dict) -> CheckResult:
    name = "Grouping existence"
    # Codex round-7 finding ("conceptually important"): this unconditionally
    # required cand.grouping_present == truth.grouping_present even when
    # grouping is genuinely DISCRETIONARY -- directly contradicting check_
    # grouping_choice_quality (per .planning/10-hybrid-comparator.md §3 and
    # judge_rubric.py), which is deliberately gated to apply ONLY when the
    # ground truth's own rendering uses row grouping AND REQUIRED_
    # INSTRUCTIONS has no "grouping" key (i.e. grouping was the ground-
    # truth author's editorial choice, not a mandated instruction) -- see
    # check_grouping_choice_quality's own docstring and judge_rubric.py's
    # applicability rule. A candidate the judge correctly rates as making
    # a sound, well-reasoned choice NOT to group still lost these 3
    # mechanical points here purely for differing from the ground truth's
    # own discretionary choice. Mirror grouping_choice_quality's exact
    # gate: N/A here in precisely the same discretionary situation, and
    # keep this a strict presence check only when REQUIRED_INSTRUCTIONS
    # explicitly demands (or forbids) grouping, or when the ground truth
    # itself doesn't group at all (no discretionary "should we group"
    # question is being tested in that case either).
    truth_groups = bool(truth["tier1"].get("grouping_present"))
    grouping_is_mandated = "grouping" in meta["REQUIRED_INSTRUCTIONS"]
    if truth_groups and not grouping_is_mandated:
        return _na(
            name,
            "grouping is a discretionary editorial choice here (ground truth groups, but "
            "REQUIRED_INSTRUCTIONS has no 'grouping' key) -- judged separately by "
            "grouping_choice_quality, not scored as a strict presence match",
        )
    ok = bool(cand["tier1"].get("grouping_present")) == truth_groups
    return CheckResult(name, 3, 3 if ok else 0, ok, f"candidate grouping_present={cand['tier1'].get('grouping_present')}, truth={truth_groups}")


def check_spanner_existence(cand: dict, truth: dict, meta: dict) -> CheckResult:
    name = "Column-group spanners existence"
    ok = bool(cand["tier1"].get("spanner_present")) == bool(truth["tier1"].get("spanner_present"))
    return CheckResult(name, 2, 2 if ok else 0, ok, f"candidate spanner_present={cand['tier1'].get('spanner_present')}, truth={truth['tier1'].get('spanner_present')}")


def check_stub_existence(cand: dict, truth: dict, meta: dict) -> CheckResult:
    name = "Stub existence"
    ok = bool(cand["tier1"].get("stub_present")) == bool(truth["tier1"].get("stub_present"))
    return CheckResult(name, 2, 2 if ok else 0, ok, f"candidate stub_present={cand['tier1'].get('stub_present')}, truth={truth['tier1'].get('stub_present')}")


def _palettes_collide(entry_a: dict, entry_b: dict) -> bool:
    """True if two colored measures' palettes render the SAME hue family.

    For a RECOGNIZED ColorBrewer name on BOTH sides, via the shared
    sequential-palette -> DA-family mapping `check_band_hue_harmonization`
    also uses (`Reds`/`Oranges` are different names but the same oxblood
    family). For anything else -- a diverging palette name, a helper hue
    that's already a DA family name, "custom" (a literal hex-list), or any
    other unrecognized string -- only a genuinely IDENTICAL raw palette
    expression (`palette_raw`, the unclassified source text) counts as a
    collision.

    Codex round-4 finding: two DIFFERENT custom hex-list palettes (e.g. a
    blue gradient and a green gradient) both classify to the same generic
    `"custom"` bucket (`palette`), so comparing THAT classified value
    flagged them as an automatic collision despite being visually
    distinct. Real color classification for arbitrary hex lists is
    explicitly out of scope; falling back to raw-text identity gives two
    genuinely-different, unclassifiable palettes the benefit of the doubt
    while still catching a literal copy-paste of the same custom gradient
    onto two measures.
    """
    pa, pb = (entry_a.get("palette") or "").lower(), (entry_b.get("palette") or "").lower()
    fa, fb = _SEQ_PALETTE_TO_DA_FAMILY.get(pa), _SEQ_PALETTE_TO_DA_FAMILY.get(pb)
    if fa is not None and fb is not None:
        return fa == fb
    ra = (entry_a.get("palette_raw") or "").strip()
    rb = (entry_b.get("palette_raw") or "").strip()
    return bool(ra) and ra == rb


def check_hue_collision(cand: dict, truth: dict, meta: dict) -> CheckResult:
    name = "No same-family hue collision across 2 measures"
    mechanics = cand["tier1"].get("color_mechanics", [])
    # Same distinct-(palette, domain, columns) dedup as check_colored_
    # measure_selection's ceiling count -- the same conceptual measure
    # applied via multiple calls that share a palette+domain AND target
    # the same columns is one measure, not two, and its (necessarily
    # identical) palette against itself must not read as "two measures
    # colliding on the same hue". Columns are part of the key (Codex
    # round-3 finding) so 3 genuinely different measures that merely
    # coincide on palette+domain, but target different columns, are
    # correctly treated as 3 separate measures here too.
    #
    # Codex round-2 finding: casting to a `set` then slicing `[:2]` made
    # this check depend on `PYTHONHASHSEED` (Python's string-hash
    # randomization) and, with 3+ distinct measures, could silently pick
    # TWO non-colliding measures while a real colliding pair among the
    # others went unchecked (e.g. Reds/Oranges/Blues: Reds and Oranges are
    # both the oxblood family, but a `[:2]` slice could land on Blues/Reds
    # instead and miss it entirely). Sorted for determinism, and every
    # PAIR is checked, not just the first two.
    distinct_measures = _distinct_colored_measures(mechanics, cand)
    if len(distinct_measures) < 2:
        return _na(name, "fewer than 2 distinct colored measures; no collision possible")
    palettes = [m.get("palette") for m in distinct_measures]
    colliding_pairs = [
        (palettes[i], palettes[j])
        for i in range(len(distinct_measures))
        for j in range(i + 1, len(distinct_measures))
        if _palettes_collide(distinct_measures[i], distinct_measures[j])
    ]
    collision = bool(colliding_pairs)
    detail = f"colored-measure palettes: {palettes}"
    if colliding_pairs:
        detail += f"; colliding pair(s) sharing a hue family: {colliding_pairs}"
    return CheckResult(name, 1, 0 if collision else 1, not collision, detail)


def _match_summary_rows(cand_summary: list[dict], truth_summary: list[dict]) -> list[dict | None]:
    """One-to-one alignment: `result[i]` is the CANDIDATE row matched to
    `truth_summary[i]`, or `None` if no distinct candidate row remains
    available for it. Each candidate row is consumed by AT MOST ONE truth
    row -- by label when it's a real, UNIQUE, still-UNUSED match on both
    sides, falling back to position (also tracked as consumed) otherwise.

    Codex round-3 finding (partially fixed): the original per-truth-row
    lookup used a plain `{label: row}` dict, so multiple candidate rows
    sharing a label silently kept only the LAST one.

    Codex round-5 finding (the remaining gap): round 3's fix only
    dedup-tracked the CANDIDATE side. If the ground TRUTH ALSO has
    multiple rows sharing a label (e.g. two rows both labeled "Total")
    and the candidate has only ONE, checking "is there exactly one
    candidate row with this label" independently for each truth row let
    BOTH truth rows match that SAME single candidate row -- a candidate
    silently missing one of two required summary rows went undetected,
    since the one it does have satisfied the label lookup for both truth
    comparisons. This tracks which CANDIDATE ROW INDICES have already
    been consumed by an earlier truth row (whether matched by label or by
    position) so a second truth row can no longer reuse one, correctly
    leaving it unmatched (`None`) when the candidate doesn't actually have
    a second row to offer.
    """
    cand_by_label: dict[Any, list[int]] = {}
    for i, row in enumerate(cand_summary):
        cand_by_label.setdefault(row.get("label"), []).append(i)

    used_indices: set[int] = set()
    result: list[dict | None] = []
    for i, truth_row in enumerate(truth_summary):
        label = truth_row.get("label")
        matched_idx: int | None = None
        if label is not None:
            available = [j for j in cand_by_label.get(label, []) if j not in used_indices]
            if len(available) == 1:
                matched_idx = available[0]
            # 0 or 2+ still-available same-label candidates -- genuinely
            # ambiguous (or exhausted); fall through to positional below.
        if matched_idx is None and i < len(cand_summary) and i not in used_indices:
            matched_idx = i
        if matched_idx is not None:
            used_indices.add(matched_idx)
            result.append(cand_summary[matched_idx])
        else:
            result.append(None)
    return result


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
    # are matched to candidate rows one-to-one on BOTH sides (see
    # `_match_summary_rows`), falling back to position when labels don't
    # line up (e.g. one side omits a label, or a label is shared by
    # multiple rows on either side).
    matches = _match_summary_rows(cand_summary, truth_summary)
    all_ok = True
    compared_cols: list[str] = []
    truth_tier2_ok = truth_tier2.get("ok", True)  # summary_rows already implies a usable truth tier2
    for i, truth_row in enumerate(truth_summary):
        cand_row = matches[i]
        truth_values = truth_row.get("values", {})
        cand_values = cand_row.get("values", {}) if cand_row is not None else {}
        for k, tv in truth_values.items():
            compared_cols.append(k)
            # Codex round-4 finding: `k` is the TRUTH's own aggregate-column
            # name -- looking it up in `cand_values` by that same name
            # (same class of bug as the sort-instruction/column-set/
            # semantic-type checks) scored a renamed-but-value-equivalent
            # summary aggregate as simply missing. Resolve by value (over
            # the full BODY row arrays, the same robust matching every
            # other check uses) whenever the direct name lookup misses.
            matched_col = k
            if matched_col not in cand_values and truth_tier2_ok:
                matched_col = execution_tier.match_measure_by_value(cand["tier2"], truth["tier2"], k)
            if matched_col is None or matched_col not in cand_values or not execution_tier.values_close(cand_values[matched_col], tv):
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
    # Codex round-3 finding: a domain whose two endpoint EXPRESSIONS are
    # textually identical (e.g. `domain=[limit, limit]`) is a provably
    # collapsed, zero-width domain regardless of what "limit" evaluates to
    # at render time -- both ends resolve to the SAME value, which can
    # never be a valid negative-to-positive symmetric span. This doesn't
    # attempt general symbolic evaluation (resolving what "limit" actually
    # equals); it just rejects the identical-text case outright, before
    # falling through to the general unresolved-benefit-of-the-doubt path
    # below, which is still correct for two DIFFERENT (and therefore
    # potentially valid, e.g. `[-m, m]`) unresolvable expressions.
    if lo.strip() == hi.strip():
        return False
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
    # Codex round-8 finding: without this gate, a candidate with real
    # color_mechanics calls (syntactically present) but FAILED Tier-2
    # execution fell through to the `total == 0` branch below (`_measure_
    # signedness` returns `None` unconditionally when `tier2.get("ok")` is
    # False, for every entry), reading as "no colored measure had usable
    # numeric values to classify" -- the exact same N/A this check
    # legitimately gives a genuinely-uncheckable candidate -- letting an
    # execution failure dodge this 8-point check entirely instead of
    # scoring a real 0. `check_sequential_vs_diverging` (right above) and
    # several other checks already gate on this explicitly; this one
    # didn't.
    if not cand["tier2"].get("ok"):
        return CheckResult(name, 8, 0, False, f"candidate failed to execute: {cand['tier2'].get('error')}")
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
            # further to verify from static text alone. Codex round-3
            # finding: two IDENTICAL endpoint expressions (`[limit,
            # limit]`) are a provably-collapsed, zero-width domain
            # regardless of resolvability -- same fix as
            # `_domain_element_symmetric`'s diverging-branch counterpart,
            # checked before falling through to the general unresolved
            # benefit-of-the-doubt path.
            if elems[0].strip() == elems[1].strip():
                ok = False
            else:
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
    # Round-5 proactive sweep finding (same "expected gated on the
    # CANDIDATE's own state, not what the ground truth requires" shape as
    # check_stub_tint's round-5 fix, and round-4 #10's striping-gate fix
    # before that): gating purely on the CANDIDATE's own `spanner_present`
    # let a candidate that omits BOTH required spanners AND their dividers
    # look self-consistent (no spanners -> no dividers "expected" -> a
    # trivial match) and dodge this 2-point sub-check entirely, on top of
    # the separate penalty `check_spanner_existence` already applies for
    # the missing spanners themselves. ALSO checking the ground truth's own
    # spanner state (via `or`) closes that gap -- a required-but-omitted
    # spanner+divider pair now correctly reads as "dividers expected, none
    # present" -- while still not penalizing a candidate that VOLUNTARILY
    # adds its own spanners (and correctly matching dividers) the ground
    # truth didn't require: candidate-side `spanner_present=True` alone
    # still sets `dividers_expected=True` in that case, same as before.
    dividers_expected = bool(t1.get("spanner_present")) or bool(truth["tier1"].get("spanner_present"))
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
    #
    # Codex round-4 finding (real gaming vector): counting EVERY bold
    # column here, unrestricted, let a candidate bold every visible
    # column -- not just the declared hero measure -- to manufacture
    # "fully filled" and dodge the striping requirement on a long table
    # entirely. Only bold columns that VALUE-MATCH a declared `CANONICAL_
    # MEASURES.hero_uncolored` entry count toward this exemption; with no
    # declared hero measure to verify against, bold text alone no longer
    # counts (there's nothing to confirm it's a genuine hero column and
    # not just gaming).
    hero_measures = meta["CANONICAL_MEASURES"].get("hero_uncolored", [])
    bold_cols_raw = set(t1.get("bold_columns") or [])
    accounted_for: set[str] = set()
    if hero_measures and bold_cols_raw and cand["tier2"].get("ok") and truth["tier2"].get("ok"):
        for hm in hero_measures:
            matched_col = execution_tier.match_measure_by_value(cand["tier2"], truth["tier2"], hm)
            if matched_col is not None and matched_col in bold_cols_raw:
                accounted_for.add(matched_col)
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
    # Codex round-5 finding: `expected_on` was derived purely from the
    # CANDIDATE's own stub presence -- if the candidate simply omitted a
    # stub the ground truth requires, `stub=False` made `expected_on=
    # False` trivially match `actual_on=False` (no stub tint is possible
    # without a stub at all), earning full 5/5 credit for a table that
    # dodged the stub requirement entirely, on TOP of the separate
    # (smaller) penalty `check_stub_existence` already applies. Gate on
    # whether the GROUND TRUTH actually requires a stub first: a required-
    # but-missing stub is a graded failure HERE too, not a free pass.
    truth_requires_stub = bool(truth["tier1"].get("stub_present"))
    if truth_requires_stub and not stub:
        return CheckResult(name, 5, 0, False, "ground truth requires a stub but candidate has none; stub tint unverifiable")
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
    # DISTINCT colored measure overall (same (palette, domain, columns)
    # dedup check_colored_measure_selection/check_hue_collision use) AND
    # that one measure uses a recognized sequential palette -- a
    # diverging-only table, "no color", or MULTIPLE measures (even if only
    # one of them is a recognized-sequential name -- e.g. one sequential +
    # one diverging) all mean there's no longer a single, unambiguous
    # color story to harmonize the band to. Counting only recognized-
    # sequential entries (an earlier approach) wrongly entered strict mode
    # for a valid 2-measure table where the second measure just happened
    # to be diverging (and thus excluded from that count).
    distinct_measures = _distinct_colored_measures(t1.get("color_mechanics", []), cand)
    sole_palette = (distinct_measures[0].get("palette") or "").lower() if len(distinct_measures) == 1 else None
    expected_family = None
    if has_color and sole_palette is not None:
        if sole_palette in _SEQ_PALETTE_TO_DA_FAMILY:
            expected_family = _SEQ_PALETTE_TO_DA_FAMILY[sole_palette]
        elif sole_palette in _EXTENDED_FAMILY_HEXES:
            # Codex round-2 finding: a `heatmap(..., hue="navy")` HELPER
            # call stores the HUE FAMILY NAME directly as `palette` (see
            # `_enrich_color_mechanics`'s heatmap branch: `palette =
            # hue-kwarg-or-"default"`), not a ColorBrewer palette name --
            # `_SEQ_PALETTE_TO_DA_FAMILY` only ever mapped ColorBrewer
            # names (`blues`/`greens`/`reds`/`oranges`), so a helper-based
            # candidate's provably-wrong band hue got "unverifiable"
            # benefit of the doubt instead of being scored. When the
            # stored value is ALREADY a recognized DA family name
            # (`_EXTENDED_FAMILY_HEXES`'s keys), that IS the expected
            # family directly.
            expected_family = sole_palette
    if expected_family is not None:
        hue_ok = t1.get("heading_band_hue") == expected_family
        hue_detail = f"expected hue family '{expected_family}' for palette '{sole_palette}', got '{t1.get('heading_band_hue')}'"
    else:
        hue_ok = True
        hue_detail = "hue harmonization not strictly verifiable for this color configuration (benefit of the doubt)"
    hue_pts = 3 if hue_ok else 0
    pts = shade_pts + hue_pts
    return CheckResult(name, 5, pts, pts == 5, f"shade expected={expected_shade} actual={actual_shade}; {hue_detail}")


def _mechanics_entry_for_column(mechanics: list[dict], fp: dict, column: str) -> dict | None:
    """The `color_mechanics` entry that targets `column`, selecting the
    LAST such entry in true source order when multiple `data_color()`/
    `heatmap()` calls target the same column (an override pattern) --
    great_tables applies each call's styling in call order, so the LAST
    call targeting a column is what actually determines its final
    rendered mechanics, not the first.

    Codex round-7 finding: this previously returned the FIRST matching
    entry, so an early `data_color(reverse=True)` call followed by a
    later `data_color(reverse=False)` override on the SAME column (still
    one measure, still within the <=2-measure ceiling) let a candidate
    satisfy `check_color_mechanics`'s reverse-orientation check against
    the first call's value while the table actually renders with the
    opposite orientation from the later, silently-overriding call.
    """
    match = None
    for entry in mechanics:
        if column in _mechanics_columns(entry, fp):
            match = entry
    return match


def _effective_mechanics_units(mechanics: list[dict], fp: dict) -> list[dict]:
    """The list of EFFECTIVE `color_mechanics` entries to actually grade --
    collapses duplicate calls targeting the SAME resolvable column down to
    whichever call is effective (last one wins, via `_mechanics_entry_
    for_column`) for that column, so two `data_color()` calls on one
    column count as ONE checkable unit, not two. An entry with NO
    resolvable columns (an unresolvable selector like `cs.starts_with(
    ...)`, or a genuinely explicit empty columns list) can't be
    deduplicated by column identity at all -- kept as its own
    independent unit, exactly as before, since its na_color/truncate/
    autocolor_text are directly readable from that one call regardless
    of which columns it ends up targeting.

    Codex round-8 finding: round 7 fixed exactly this "first call wins
    instead of the last, effective one" bug for `reverse` (via
    `_mechanics_entry_for_column`, used directly in `check_color_
    mechanics` below), but left na_color/truncate/autocolor_text summing
    across EVERY raw mechanics entry (one per CALL) even when multiple
    calls targeted the SAME column -- an early, WRONG call overridden by
    a later, correct one still counted as a failure (and vice versa),
    despite only the LAST call's value ever actually being rendered.
    """
    resolved_columns: set[str] = set()
    independent_entries: list[dict] = []
    for entry in mechanics:
        cols = _mechanics_columns(entry, fp)
        if cols:
            resolved_columns.update(cols)
        else:
            independent_entries.append(entry)
    effective_by_column = [_mechanics_entry_for_column(mechanics, fp, col) for col in resolved_columns]
    return [e for e in (*effective_by_column, *independent_entries) if e is not None]


def check_color_mechanics(cand: dict, truth: dict, meta: dict) -> CheckResult:
    name = "Color mechanics (na_color, truncate, autocolor_text)"
    mechanics = cand["tier1"].get("color_mechanics", [])
    if not mechanics:
        if _truth_requires_color(meta):
            return CheckResult(name, 4, 0, False, "ground truth requires colored measure(s) but candidate has none")
        return _na(name, "candidate has no colored measures")
    units = _effective_mechanics_units(mechanics, cand)
    n = len(units)
    # Codex round-2 finding: a raw-string comparison rejected CSS-equivalent
    # spellings of the required color (`"gray"`, `"rgb(128, 128, 128)"`)
    # that render IDENTICALLY to `"#808080"` -- normalize both sides
    # through `_normalize_css_color` before comparing.
    na_ok = sum(1 for e in units if _normalize_css_color(e.get("na_color")) == "#808080")
    trunc_ok = sum(1 for e in units if e.get("truncate") == "False")
    autocolor_ok = sum(1 for e in units if e.get("autocolor_text") == "True")
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
    # credit. Now iterates every truth summary row, same one-to-one
    # matching (see `_match_summary_rows`, falling back to position)
    # `check_summary_row_existence` already uses, accumulating per (row,
    # column) pairs rather than per distinct column name -- a column
    # present in multiple rows must be checked in EACH row it's expected
    # in, not just once overall.
    matches = _match_summary_rows(cand_summary, truth_summary)
    required_pairs = 0
    covered_pairs = 0
    distinct_cols: set[str] = set()
    tier2_ok_for_matching = cand["tier2"].get("ok") and truth["tier2"].get("ok")
    semantic_types = meta.get("SEMANTIC_TYPES", {}) if meta else {}
    for i, truth_row in enumerate(truth_summary):
        row_numeric_cols = [
            k for k, v in truth_row.get("values", {}).items() if isinstance(v, (int, float))
        ]
        if not row_numeric_cols:
            continue
        cand_row = matches[i]
        cand_values = cand_row.get("values", {}) if cand_row is not None else {}
        for c in row_numeric_cols:
            distinct_cols.add(c)
            required_pairs += 1
            # Codex round-4 finding #1 (same class as the sort-instruction/
            # summary-value fixes above): resolve `c` (a TRUTH column name)
            # to its value-matched CANDIDATE column when the direct name
            # lookup misses, instead of only ever checking the same name.
            matched_col = c
            if matched_col not in cand_values and tier2_ok_for_matching:
                matched_col = execution_tier.match_measure_by_value(cand["tier2"], truth["tier2"], c)
            if matched_col is None or not isinstance(cand_values.get(matched_col), (int, float)):
                continue
            effective_fmt = fmt_map.get(matched_col, fmt_map.get(convergence._ALL_COLUMNS))
            if not effective_fmt:
                continue
            # Codex round-4 finding #2: this previously credited coverage
            # for ANY fmt_* call at all, so a percent column formatted with
            # fmt_currency (the wrong TYPE entirely) still scored full
            # credit. When the ground truth declares a SEMANTIC_TYPES entry
            # for this column, the effective formatter must actually match
            # it (same mapping check_fmt_semantic_type uses); with no
            # declared semantic type there's nothing to check the TYPE
            # against, so "some fmt_* call covers it" remains the
            # (weaker, but only available) signal.
            semantic_type = semantic_types.get(c)
            if semantic_type is not None:
                # Codex round-6 finding: `fmt_integer` on a "number"-typed
                # aggregate (e.g. a monthly average) silently rounds away
                # real fractional data -- only accept it when the actual
                # summary value is genuinely a whole number.
                if _fmt_covers_semantic_type(
                    semantic_type, effective_fmt, all_integral=_is_integral_value(cand_values.get(matched_col))
                ):
                    covered_pairs += 1
            else:
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


def _is_integral_value(v: Any) -> bool:
    """True if `v` is a whole number (works for an `int`, a `float`, or a
    numeric-looking string) -- `False` for anything non-numeric or
    genuinely fractional.
    """
    try:
        return float(v).is_integer()
    except (TypeError, ValueError):
        return False


def _column_values_are_integral(tier2: dict, column: str) -> bool:
    """True if every usable value in `tier2`'s `column` is a whole number,
    or the column has no usable numeric values at all (nothing to
    contradict "integral" -- benefit of the doubt, same as every other
    "can't verify from what's available" case in this file).
    """
    for v in tier2.get("columns", {}).get(column, []) or []:
        if v is None:
            continue
        try:
            fv = float(v)
        except (TypeError, ValueError):
            continue
        if not fv.is_integer():
            return False
    return True


def _fmt_covers_semantic_type(sem_type: str, effective_fmt: Any, *, all_integral: bool) -> bool:
    """True if `effective_fmt` is an honest, accepted formatter for
    `sem_type`.

    Codex round-6 finding: `_SEMANTIC_TO_FMT["number"]` accepts
    `fmt_integer` as well as `fmt_number` -- reasonable for a genuinely
    whole-number "number" column, but `fmt_integer()` silently ROUNDS AWAY
    real fractional data (a density, a monthly average, etc.), so a
    fractional "number"-typed measure formatted with `fmt_integer` was
    still credited as correctly formatted. `fmt_integer` is only accepted
    for a `"number"`-typed column when the actual matched value(s) are
    genuinely integral; every other accepted (formatter, semantic type)
    pairing is unaffected.
    """
    if effective_fmt not in _SEMANTIC_TO_FMT.get(sem_type, set()):
        return False
    if sem_type == "number" and effective_fmt == "fmt_integer" and not all_integral:
        return False
    return True


def check_fmt_semantic_type(cand: dict, truth: dict, meta: dict) -> CheckResult:
    name = "fmt_* per column semantic type"
    semantic_types = meta["SEMANTIC_TYPES"]
    if not semantic_types:
        return _na(name, "ground truth declares no SEMANTIC_TYPES to check")
    if not cand["tier2"].get("ok") or not truth["tier2"].get("ok"):
        return CheckResult(name, 4, 0, False, f"candidate failed to execute: {cand['tier2'].get('error')}")
    # Codex round-2 finding: `SEMANTIC_TYPES`' keys are the GROUND TRUTH's
    # own SOURCE column names -- matching them against the candidate's
    # visible columns by same NAME made a renamed-but-correct column
    # (ground truth `hp` values rendered as candidate `horsepower`)
    # invisible to this check entirely: `applicable` came back empty and
    # the whole 4-point check went N/A instead of failing an unformatted
    # renamed column. Resolves each semantic-typed measure to its VALUE-
    # matched candidate column instead, via `execution_tier.match_measure_
    # by_value` -- the same value-based matching `check_colored_measure_
    # selection`/`check_hero_column_formatting` already use elsewhere in
    # this file, rather than assuming the candidate preserved the name.
    #
    # Round-5 proactive sweep finding (same "expected/applicable gated on
    # the CANDIDATE's own state" shape as check_stub_tint/check_frame_
    # hairlines_dividers's round-5 fixes): the denominator here was every
    # semantic-typed column the candidate happened to still have VISIBLE
    # -- so a candidate that HID every semantic-typed column (via `cols_
    # hide(...)`) shrank `applicable` to empty and the whole 4-point check
    # went N/A instead of failing those hidden/missing columns. The
    # denominator is now EVERY semantic-typed column the ground truth
    # declares, always (once SEMANTIC_TYPES and both tier2s are usable,
    # already checked above) -- a hidden or genuinely-unmatched column now
    # counts as a required-but-uncovered column, not an excused one.
    visible = _visible_columns(cand)
    fmt_map = cand["tier1"].get("fmt_column_map", {})
    ok_count = 0
    uncovered: list[str] = []
    for c, sem_type in semantic_types.items():
        matched_col = execution_tier.match_measure_by_value(cand["tier2"], truth["tier2"], c)
        effective_fmt = fmt_map.get(matched_col, fmt_map.get(convergence._ALL_COLUMNS)) if matched_col else None
        if (
            matched_col is not None
            and matched_col in visible
            and _fmt_covers_semantic_type(
                sem_type, effective_fmt, all_integral=_column_values_are_integral(cand["tier2"], matched_col)
            )
        ):
            ok_count += 1
        else:
            uncovered.append(c)
    total = len(semantic_types)
    all_ok = ok_count == total
    detail = f"{ok_count}/{total} columns formatted per their semantic type"
    if uncovered:
        detail += f"; not covered (missing, hidden, or wrong format): {uncovered}"
    return CheckResult(name, 4, _round_points(ok_count / total, 4), all_ok, detail)


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
    #
    # Codex round-6 finding: a bare `len(notes) >= N` slot-existence check
    # doesn't distinguish a genuinely unresolved DYNAMIC expression
    # (`None` -- benefit of the doubt, still "present") from a statically
    # EXPLICIT empty-string literal (`tab_source_note(source_note="")`) --
    # the latter is a real call that adds NO actual text, not a footer
    # that's "present" in any meaningful sense.
    notes = cand["tier1"].get("source_note_texts") or []

    def _note_slot_present(index: int) -> bool:
        if index >= len(notes):
            return False
        val = notes[index]
        if val is None:
            return True  # dynamic expression -- benefit of the doubt
        return val.strip() != ""

    caption_present = _note_slot_present(0)
    source_expected = bool(truth["tier1"].get("source_note_texts")) and len(truth["tier1"]["source_note_texts"]) >= 2
    source_present = _note_slot_present(1)
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
    hero_measures = meta["CANONICAL_MEASURES"].get("hero_uncolored", [])
    if not hero_measures:
        # No canonical hero measure declared to target -- fall back to the
        # original "some column is bold" signal (there's nothing more
        # specific to check against). Step 3's rule is bold-hero-text as
        # the ALTERNATIVE to a third color fill, so with no specific
        # measure declared, this weaker heuristic only makes sense to
        # apply when the candidate has no colored measures at all --
        # unlike the declared-hero-measure branch below, there's nothing
        # concrete here to check independently of that context.
        if cand["tier1"].get("color_mechanics"):
            return _na(name, "candidate has colored measures and no canonical hero-uncolored measure is declared")
        bolded = bool(cand["tier1"].get("bold_columns"))
        return CheckResult(
            name, 2, 2 if bolded else 0, bolded,
            f"bold_columns={cand['tier1'].get('bold_columns')} (no canonical hero measure declared)",
        )
    # Codex round-2 finding: this whole check previously bailed to N/A
    # whenever the candidate had ANY colored measure at all -- but all 4
    # checked-in ground truths that declare `hero_uncolored` measures ALSO
    # declare and render colored measures (a hero column is precisely the
    # column that DOESN'T get a third color fill alongside the ≤2 that
    # do), so that early return made this check N/A for every one of
    # them, never actually exercised. A ground truth that DECLARES
    # specific hero_uncolored measures must have them checked directly,
    # regardless of whether other measures happen to be colored -- this
    # also catches a candidate that colors the supposed hero column
    # INSTEAD of bolding it (that measure's value-matched candidate
    # column then simply won't be in `bold_cols` below).
    if not cand["tier2"].get("ok"):
        return CheckResult(name, 2, 0, False, f"candidate failed to execute: {cand['tier2'].get('error')}")
    # Bolding is only meaningful when it targets the ACTUAL declared hero
    # measure(s), matched by VALUE (not name) like every other measure
    # check here -- bolding an unrelated identifier or secondary metric
    # previously earned full credit just for being nonempty.
    #
    # Codex round-6 finding (important): this never checked that the
    # bold, "hero_uncolored" column ISN'T *also* colored -- but the whole
    # design intent (per the metadata's own name, and Step 3's rule
    # elsewhere in this file: bold text is the ALTERNATIVE to a third
    # color fill, not an addition to it) is that a hero measure is
    # uncolored. Concretely, on `gtcars_hp_price`: a candidate could color
    # BOTH `msrp` and the supposedly-uncolored `hp` hero, bold `hp` too,
    # stay within the ≤2 colored-measure ceiling, and get full credit on
    # both check_colored_measure_selection AND this check simultaneously.
    # Excluding any column that's also colored-matched from hero coverage
    # closes that gap.
    bold_cols = set(cand["tier1"].get("bold_columns") or [])
    colored_cols = {c for m in cand["tier1"].get("color_mechanics", []) for c in _mechanics_columns(m, cand)}
    covered = 0
    for m in hero_measures:
        matched_col = execution_tier.match_measure_by_value(cand["tier2"], truth["tier2"], m)
        if matched_col and matched_col in bold_cols and matched_col not in colored_cols:
            covered += 1
    pts = _round_points(covered / len(hero_measures), 2)
    return CheckResult(
        name, 2, pts, covered == len(hero_measures),
        f"{covered}/{len(hero_measures)} canonical hero-uncolored measures are bolded",
    )


def check_render_mechanics(cand: dict, truth: dict, meta: dict) -> CheckResult:
    name = "Render mechanics (zoom/expand fit-order rule)"
    t1 = cand["tier1"]
    params = t1.get("render_params") or {}
    if not t1.get("render_call_present"):
        # Codex round-2 finding: this render-target check used to be
        # confined to the `not params` branch below, so a candidate
        # calling `gtsave("backup.png", zoom=2.0)` -- a resolvable zoom
        # kwarg, but the WRONG output filename -- fell through past this
        # gate entirely and was awarded full zoom/expand credit despite
        # never producing the harness's required `table.png`. A provably-
        # wrong (or missing) render target is a hard failure regardless of
        # what its other params say, so this is checked FIRST,
        # unconditionally.
        if not params:
            return CheckResult(name, 2, 0, False, "no gtsave()/finalize() call found -- the required table image was never rendered")
        return CheckResult(
            name, 2, 0, False,
            "gtsave()/finalize() call(s) found, but none targets the required table.png output",
        )
    if not params:
        # `render_params` is `{}` here only for a render call that exists,
        # DOES target table.png, but whose OTHER params aren't statically
        # resolvable (e.g. a **kwargs expansion) -- genuinely unverifiable,
        # benefit of the doubt.
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
            # Codex round-4 finding: this validated style/weight but never
            # checked whether the border's `color=` was actually visible --
            # `style.borders(..., color="transparent")` satisfied every
            # other check here despite rendering no distinguishing border
            # at all. Same transparency check already used for
            # `frame_present`/`_has_visible_tab_style_border`.
            border_color_val = convergence._kwarg_value(borders_block, "color")
            if border_color_val:
                unquoted_color = convergence._unquote(border_color_val)
                if unquoted_color and _is_effectively_transparent(unquoted_color.strip()):
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


# A checked-out ground-truth `.py`/`.png` pair legitimately produced
# TOGETHER (e.g. by the same `git checkout`) can still land a few
# milliseconds apart in mtime purely from filesystem/checkout ordering
# noise -- empirically observed as ~2ms on this repo's own checked-in
# corpus, nowhere close to a genuine "the source changed after the PNG was
# rendered" gap (which in real usage is realistically seconds to hours).
# This tolerance absorbs that noise without meaningfully weakening the
# freshness check's actual purpose.
_JUDGE_PNG_STALE_TOLERANCE_S = 5.0


def _judge_png_is_stale(candidate_png: Path, candidate_path: Path) -> bool:
    """True if `candidate_png` exists but is OLDER than `candidate_path`
    (its own source `.py`) by more than `_JUDGE_PNG_STALE_TOLERANCE_S` --
    i.e. a stale render from a since-changed (or now-broken) candidate
    script, not just filesystem/checkout timing noise between two files
    that were legitimately produced together.

    Codex round-4 finding: judge-backed checks were scoring whatever PNG
    happened to sit next to the candidate `.py`, with no check that it was
    actually produced by the CURRENT source -- an old `table.png` left
    over from a prior version of the script (since edited, or now failing
    to render at all) got scored by the judge while every deterministic
    check read the NEW source, awarding title/label/order/palette points
    for output the candidate no longer actually produces. Re-rendering to
    guarantee freshness is explicitly out of scope (this module never
    renders anything -- see `compare()`'s own docstring); a cheap mtime
    comparison is a strictly weaker but zero-cost substitute: if the PNG
    predates its own source file by a meaningful margin, it can't possibly
    reflect that source's current state, so it's treated as stale/
    unavailable, same as a missing file. A PNG that doesn't exist at all
    isn't "stale" by this definition -- `judge()` already handles a
    missing file as its own degrade case, so this only needs to catch the
    case where a file DOES exist but is provably outdated. A strict `<`
    with no tolerance was tried first and immediately false-flagged this
    repo's own checked-in ground-truth PNGs (a legitimately fresh pair,
    checked out within ~2ms of each other) as "stale" -- the tolerance
    fixes that without giving up the check's actual purpose.
    """
    if not candidate_png.is_file() or not candidate_path.is_file():
        return False
    return candidate_png.stat().st_mtime < candidate_path.stat().st_mtime - _JUDGE_PNG_STALE_TOLERANCE_S


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
    if not cand["tier2"].get("ok"):
        # Codex round-5 finding: gate the judge call on the candidate's OWN
        # Tier-2 execution having actually succeeded, as a HARD
        # precondition -- more fundamental than the mtime staleness check
        # below. Whatever PNG happens to sit next to a candidate `.py`
        # that fails to even EXECUTE cannot be trusted to reflect that
        # source at all (it could be leftover from any prior, unrelated
        # version), regardless of how recently it was written. This is
        # checked BEFORE the mtime check on purpose: a fresh-looking PNG
        # next to a currently-broken script is just as untrustworthy as a
        # stale one.
        reason = f"judge unavailable: candidate failed Tier-2 execution ({cand['tier2'].get('error')}); its PNG (if any) can't be trusted to reflect this source"
        meta["_judge_result"] = {
            key: judge_module.JudgeDimension(applicable=False, score=None, rationale=reason)
            for key in judge_module.DIMENSION_KEYS
        }
    elif _judge_png_is_stale(candidate_png, candidate_path):
        # Codex round-4 finding: see `_judge_png_is_stale`'s docstring --
        # degrade exactly like `judge()`'s own documented "unavailable"
        # contract (all 7 keys, applicable=False, rationale prefixed with
        # the literal "judge unavailable: " string) rather than scoring a
        # PNG that predates the source it's supposed to represent. This is
        # the SECONDARY signal, for the case where execution succeeds but
        # an older PNG might still be sitting there from a prior run.
        reason = f"judge unavailable: candidate PNG is older than its source .py ({candidate_png} predates {candidate_path})"
        meta["_judge_result"] = {
            key: judge_module.JudgeDimension(applicable=False, score=None, rationale=reason)
            for key in judge_module.DIMENSION_KEYS
        }
    else:
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
