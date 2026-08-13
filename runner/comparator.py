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
an open-ended space of valid choices (column-label clarity, title quality,
column order) — those are computed by one batched call to
``runner.judge.judge()`` (a vision-capable LLM call, see that module) and
read out of the single combined result ``compare()`` stashes in
``meta["_judge_result"]`` before running the check functions. Every check
function still has the exact same signature and every judge-backed check
degrades to the existing ``_na()`` pattern (0/0, excluded from the
denominator) if the judge is unavailable or the dimension doesn't apply to
this comparison — nothing ever silently passes or fails.
``CheckResult.tier`` ("mechanical" or "judge") makes the distinction
visible in the printed report, not just in code comments.

Report shape: a 0–108 total = Data-compliance (0–53) + Formatting-compliance
(0–55), plus one line per check naming its tier, what passed/failed, its
point value, and why (§7).

2026-08-12: the 6 ground truths were rewritten to pin down several
formerly per-table/discretionary decisions as flat, universal house rules
(deep-navy header/stub branding regardless of a table's own heatmap hue,
row striping by default, hero-uncolored measures never bold, force_sign
on signed percent measures, and a revived CAPTION_KEYWORDS check now that
captions are one short sentence each) -- see `check_header_branding`,
`check_stub_tint`, `check_stripe_color`, `check_hero_not_bold`,
`check_force_sign`, `check_caption_keywords` (new, +16 Formatting-
compliance points total) and the rewritten `check_striping_gate` (same
5 points, new formula). `check_band_hue_harmonization` is retired (now a
permanent 0/0 N/A stub, kept for its docstring's explanation rather than
silently vanishing) -- its old "light band when colored, dark band
matched to that measure's hue when not" formula is exactly backwards
against every current ground truth.

Per ``.planning/12-consensus-tuning.md``: 6 Formatting-compliance checks
were removed entirely across two passes, all for the same reason -- field
data across the eval corpus's real skill variants showed each one scoring
either near-zero (hero-column formatting, stub tint/grey-budget,
caption-not-restating-subtitle) or flat/non-discriminating (title/
subtitle/caption/source presence, subtitle quality, color theme/palette
taste) regardless of which skill produced the candidate, meaning each
measured something no current skill-guided output reliably achieves or
that doesn't actually distinguish skill quality, rather than a real
quality gap between skills.
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
    value trusted instead of the one actually rendered.

    Codex round-10 finding: the round-8 fix still scanned raw SOURCE TEXT
    via `re.findall`, with no comment/string stripping at all -- a `#
    column_labels_background_color="#000000"` comment (or a docstring
    mentioning the same) was misdetected as a real, later-OVERRIDING
    `tab_options()` call, the exact same source-wide-text-scan bug class
    already fixed for color-mechanics/frame/fmt_* detection.
    Extracts from genuine `.tab_options(...)` AST call blocks (via
    `_ast_call_blocks`, sorted into true source order, already scoped to
    top-level-only calls per the round-9 `_walk_top_level` fix) instead
    of raw text -- still takes the LAST occurrence of the preferred key
    across ALL `tab_options()` calls, preserving the round-8 override-
    resolution fix, and still only accepts a genuine quoted string
    literal as a value (via `_quoted_string_literal_value`), matching the
    original regex's own "only ever a quoted literal, never a bare
    variable" behavior exactly. `runner/convergence.py` is a hard
    non-goal for this slice, so this stays a local shim rather than a
    fix to `_find_band_color` itself.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    blocks = sorted(_ast_call_blocks(source, tree, "tab_options", allow_bare=False), key=lambda b: b[0])
    for key in ("column_labels_background_color", "heading_background_color"):
        last_value = None
        for _, block in blocks:
            val = convergence._kwarg_value(block, key)
            literal = _quoted_string_literal_value(val) if val is not None else None
            if literal is not None:
                last_value = literal
        if last_value is not None:
            return last_value
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
    NODE's own position instead -- the exact same sort key `_ast_call_
    blocks` already uses for this same call node -- so each call site
    resolves strictly against the statement immediately preceding IT,
    never a different call's binding. `tree` is passed in (rather than
    re-parsed here) so callers building `_ast_call_blocks` results from
    the SAME parse can look up by identical keys.

    Codex round-13 finding: keyed on `(lineno, col_offset)` -- the call's
    OWN START position -- which MUST match `_ast_call_blocks`'s own key
    exactly for the position-based correlation lookup to work at all.
    `_ast_call_blocks` switched to `(end_lineno, end_col_offset)` (its
    own round-13 fix, for fluent-chain ordering correctness) -- this
    function's key is updated identically, or every lookup here would
    silently miss.
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
                        out[(call_node.end_lineno, call_node.end_col_offset)] = prev.value.value
    return out


def _blocks_target_table_png(
    blocks: list[tuple[tuple[int, int], str]],
    path_kwarg: str,
    path_index: int,
    var_literals: dict[tuple[int, int], str] | None = None,
    *,
    default_path: str | None = None,
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

    Fresh-sweep finding (2026-08-12): a call whose path argument is
    absent entirely (neither `path_kwarg` nor a positional at `path_
    index` is set) previously always fell through to `continue` --
    treated as "nothing learned from this call." That's correct for
    `gtsave(file, ...)` (`file` has no default in `great_tables`'s own
    `GT.save`/`gtsave` signature -- omitting it is a `TypeError`, not a
    fallback to `table.png`), but WRONG for `great-tables-house`'s and
    `great-tables-ci`'s `finalize(gt, path="table.png", **overrides)`
    helper, whose OWN signature defaults `path` to `"table.png"` --  a
    bare `finalize(gt)` call genuinely renders to `table.png` via that
    documented default, not to nothing. `default_path` lets a caller that
    KNOWS its call form has such a default (only the `finalize(...)`
    call site does; `gtsave(...)` passes nothing here and keeps the old
    "no path argument -- can't tell" behavior) supply it so an absent
    argument is treated as that resolved literal instead of being
    silently skipped.
    """
    for pos, b in blocks:
        path_val = convergence._kwarg_value(b, path_kwarg)
        if path_val is None:
            positionals = [
                p for p in convergence._split_top_level_quoted(b) if not re.match(r"[A-Za-z_]\w*\s*=", p)
            ]
            path_val = positionals[path_index] if len(positionals) > path_index else None
        if path_val is None:
            if default_path is not None and convergence._targets_table_png(default_path):
                return True
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


def _module_level_functions(tree: ast.Module) -> dict[str, ast.FunctionDef]:
    """name -> node for every plain `def` sitting directly in `tree.body`
    -- used only to resolve the one special case `_walk_top_level` and
    `_walk_exported_scope` unwrap (see their docstrings): a bare
    `if __name__ == "__main__": some_name()` calling a function defined
    at module level.

    Deliberately excludes `async def` (2026-08-13 review finding): the
    guard shape this resolves is a BARE, non-awaited call
    (`_main_guard_call_target` requires it) -- calling an async function
    that way only constructs a coroutine object and never runs its body
    at all, so unwrapping it would score a script that renders NOTHING as
    if its whole body executed. An `async def` target now simply fails to
    resolve (falls back to the unrestricted walk), the same safe default
    used whenever the guard's target can't be resolved at all.
    """
    return {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }


def _main_guard_call_target(node: ast.stmt) -> str | None:
    """If `node` is exactly `if __name__ == "__main__": name()` -- a
    single bare, zero-argument call as the ENTIRE if-body, no `elif`/
    `else`, no other statements -- returns the called `name`;
    otherwise `None`. See `_walk_top_level`'s docstring for why this one
    shape gets special-cased instead of generalized into real
    reachability analysis.
    """
    if not isinstance(node, ast.If) or node.orelse:
        return None
    test = node.test
    if not (
        isinstance(test, ast.Compare)
        and isinstance(test.left, ast.Name)
        and test.left.id == "__name__"
        and len(test.ops) == 1
        and isinstance(test.ops[0], ast.Eq)
        and len(test.comparators) == 1
        and isinstance(test.comparators[0], ast.Constant)
        and test.comparators[0].value == "__main__"
    ):
        return None
    if len(node.body) != 1 or not isinstance(node.body[0], ast.Expr):
        return None
    call = node.body[0].value
    if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and not call.args and not call.keywords):
        return None
    return call.func.id


def _walk_top_level(tree: ast.AST):
    """Like `ast.walk`, but does NOT descend into the body of a `def`/
    `class` statement -- yields every node reachable from `tree` WITHOUT
    ever stepping inside a `FunctionDef`/`AsyncFunctionDef`/`ClassDef`'s
    own body.

    Codex round-9 finding: every AST-based call-detection helper in this
    file (`_has_real_call`, `_ast_call_blocks`, `_ast_fmt_calls`)
    previously used `ast.walk(tree)` unconditionally, which visits every
    node in the WHOLE module, including ones nested inside a function or
    class body -- a `.data_color(...)` call sitting inside a never-
    invoked helper function (or a dead branch inside one) still counted
    as real styling. A full fix would need actual reachability/call-graph
    analysis -- real scope creep for a file that does no execution beyond
    what Tier 2 already captures -- so this is the bounded, sufficient
    fix instead: every ground truth/candidate in this corpus is written
    as a linear TOP-LEVEL script, so restricting call detection to nodes
    that are never nested inside a `def`/`class` body at all is
    conservative (it can only under-count, never over-count, a call the
    harness would actually execute) and sufficient for this corpus's
    real shape. A call buried inside a function definition (called or
    not) is unusual enough to exclude outright rather than try to prove
    reachability.

    2026-08-13 addition: a script that wraps its ENTIRE body in
    `def build_table(): ...` and only calls it via `if __name__ ==
    "__main__": build_table()` is ordinary, idiomatic Python that
    executes exactly like an inlined top-level script when the harness
    runs `python table.py` -- but the blanket def/class exclusion above
    made it invisible to every check built on this function. Confirmed
    directly against the currently-committed `eval-results/house/
    samples/airquality_monthly_summary/repeat_1/table.py` (scored ~18%
    purely from this blind spot, not from any real quality problem).
    `eval-results/house/SUMMARY.md`'s own round-2 write-up attributes the
    same shape to `towny_growth_trends/repeat_1` in that round's sweep --
    that sweep has since been regenerated, so the sample currently
    checked in in its place no longer reproduces it; the attribution is
    real but not independently re-verifiable against today's tree. This
    is ONE narrow, additive special case, not a general
    call-graph/reachability analysis (still explicitly out of scope,
    per above): when the `if __name__ == "__main__":` guard's entire
    body is a single bare, zero-argument call to a name that resolves to
    a module-level `def` (`_main_guard_call_target` /
    `_module_level_functions`), that function's OWN body is walked in
    place of the `if` statement, as if inlined there -- one level of
    unwrapping only. A `def`/`class` nested inside the unwrapped
    function's own body is still excluded, same as ever.

    2026-08-13 review finding: the unwrap must be gated to ONLY the
    guard statement sitting directly in `tree.body` -- checking every
    popped node unconditionally (the first cut of this fix) let an
    unwrapped function's OWN body re-trigger the same special case if it
    happened to contain another (or the same) `__main__`-guard shape,
    which is not "one level" as claimed and, for a self-referential
    shape (`def build(): if __name__=="__main__": build()`), never
    terminates -- confirmed to push >200k nodes without returning.
    `guard_ids` (the `id()` of every statement literally in `tree.body`)
    restricts the special case to exactly those; anything reached BY an
    unwrap is walked normally, with no second chance to unwrap again.
    """
    main_guard_defs = _module_level_functions(tree) if isinstance(tree, ast.Module) else {}
    if isinstance(tree, ast.Module):
        guard_ids = {id(n) for n in tree.body}
        body_index = {id(n): i for i, n in enumerate(tree.body)}
    else:
        guard_ids = set()
        body_index = {}
    stack = [tree]
    while stack:
        node = stack.pop()
        target_def = None
        if id(node) in guard_ids:
            target_name = _main_guard_call_target(node)
            candidate = main_guard_defs.get(target_name)
            # The def must appear BEFORE the guard -- calling it any earlier
            # is a real `NameError` at runtime (2026-08-13 review finding),
            # not an inlined-equivalent script.
            if candidate is not None and body_index[id(candidate)] < body_index[id(node)]:
                target_def = candidate
        if target_def is not None:
            yield node
            stack.extend(reversed(target_def.body))
            continue
        yield node
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue  # do not descend into a def/class's own body
            stack.append(child)


def _exported_gt_name(tree: ast.Module) -> str | None:
    """The bare variable NAME whose call chain actually produces the
    script's EXPORTED/rendered table -- the root receiver of the
    (effective, last-by-position) `.gtsave(...)` call's whole chain, or
    the first positional argument of a bare `finalize(...)` call. `None`
    when no render call exists, or its receiver/argument isn't a simple,
    resolvable name/attribute-chain (an expression this bounded fix
    deliberately doesn't attempt to trace further -- see `_walk_exported_
    scope`'s own docstring for why giving up here is the SAFE default).
    """
    candidates: list[ast.Call] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr == "gtsave":
            candidates.append(node)
        elif isinstance(func, ast.Name) and func.id == "finalize":
            candidates.append(node)
    if not candidates:
        return None
    candidates.sort(key=lambda n: (n.end_lineno, n.end_col_offset))
    call_node = candidates[-1]
    func = call_node.func
    if isinstance(func, ast.Attribute) and func.attr == "gtsave":
        expr: ast.expr = func.value
        while isinstance(expr, ast.Call):
            if not isinstance(expr.func, ast.Attribute):
                return None  # a bare call mid-chain -- not the simple pattern this resolves
            expr = expr.func.value
        return expr.id if isinstance(expr, ast.Name) else None
    if isinstance(func, ast.Name) and func.id == "finalize":
        if call_node.args and isinstance(call_node.args[0], ast.Name):
            return call_node.args[0].id
        return None
    return None


def _stmt_targets_name(stmt: ast.stmt, name: str) -> bool:
    """True if `stmt` either (a) is an assignment whose target IS `name`
    (`gt = GT(df)`, `gt = gt.data_color(...)`, however many times `name`
    is progressively reassigned to itself), or (b) is a bare expression
    statement whose own call-chain root is `name` (`gt.gtsave(...)`,
    `gt.tab_header(...).gtsave(...)`, a bare `finalize(gt, ...)`).

    Internal review finding (2026-08-11): the bare-call branch below
    previously compared the wrong thing for a call shaped like `finalize(gt,
    ...)` -- `name` is
    the SCRIPT's exported variable ("gt"), but the code compared it against
    `func.id`, which is the CALLEE's own name ("finalize"), an equality
    that can never hold. That silently excluded every bare `finalize(gt,
    ...)` statement from `_walk_exported_scope`'s restricted walk -- so
    `_ast_call_blocks(source, tree, "finalize", allow_bare=True)` (called
    from `_render_call_present`, which `check_render_mechanics` reads via
    the `render_call_present` fingerprint field to detect a render call at
    all) never found it, scoring a perfectly correct, actually-rendered
    candidate as "no
    gtsave()/finalize() call found -- the required table image was never
    rendered." A bare call's SUBJECT is its first positional argument (the
    same convention `_exported_gt_name` above already uses to resolve
    `finalize(gt, ...)`'s target), not the function name -- check that.

    Follow-up review finding (same day): the first fix checked ANY bare
    call's first argument against `name`, not just `finalize(...)` --
    `debug_dump(gt, ...)` or even `print(gt)` would also match, pulling
    that statement's entire subtree into the exported scope (the exact
    false-positive class `_walk_exported_scope`'s round-14 fix exists to
    prevent, e.g. a throwaway `GT(df).data_color(...)` passed as some
    OTHER argument to that same bare call). Restricted to `func.id ==
    "finalize"` specifically -- the one bare-call render convention this
    corpus actually uses, matching `_exported_gt_name`'s own identical
    restriction just above. `finalize(gt=gt, ...)` (keyword-only) is
    still not resolved by either function -- benign today only because
    both degrade the same way (both return None/False, so a name that
    can't be resolved falls back to the unrestricted `_walk_top_level`
    rather than being wrongly excluded); a script that ALSO resolves the
    exported name some other way (e.g. `gt = gt.gtsave(...)` elsewhere)
    while using `finalize(gt=gt, ...)` for a bare call would silently
    drop that one statement from scope. Not handled -- keyword-only
    `finalize()` calls aren't a pattern this corpus uses.
    """
    if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
        return stmt.targets[0].id == name
    if isinstance(stmt, ast.Expr):
        expr = stmt.value
        while isinstance(expr, ast.Call):
            func = expr.func
            if isinstance(func, ast.Attribute):
                expr = func.value
            elif isinstance(func, ast.Name) and func.id == "finalize":
                # a bare `finalize(gt, ...)` call -- `name` is the call's
                # first ARGUMENT, not its callee.
                return bool(expr.args) and isinstance(expr.args[0], ast.Name) and expr.args[0].id == name
            else:
                return False
        return isinstance(expr, ast.Name) and expr.id == name
    return False


def _walk_exported_scope(tree: ast.AST):
    """Like `_walk_top_level`, but additionally restricted to only the
    MODULE-LEVEL statements that build the actual EXPORTED variable's own
    call chain (`_stmt_targets_name`, keyed on `_exported_gt_name`) -- a
    statement building some OTHER, unrelated/unused variable is skipped
    entirely, its calls never visited by anything built on this.

    Codex round-14 finding (bounded scope): AST-based call detection
    didn't distinguish "a call on some other variable" from "a call
    that's part of the chain building the actual exported table" -- a
    candidate could build a separate, unused table object with real
    color/formatting/frame calls (`preview = GT(df).data_color(...)`)
    while the ACTUALLY exported object stayed plain, and those calls
    still counted toward every check built on `_ast_call_blocks`/`_ast_
    fmt_calls`/`_has_real_call` (color mechanics, formatter detection,
    frame/stripe/spanner/stub-tint/tab_style/tab_header/source-note
    presence, and more -- every one of them, transparently, since this
    only changes what `_walk_top_level` itself visits).

    This deliberately does NOT attempt full data-flow or reachability
    analysis (same scope boundary as round 9's analogous finding on this
    same file) -- it only tracks SIMPLE, MODULE-LEVEL statements whose
    assignment target or call-chain root is LITERALLY the exported name,
    and conservatively falls back to the UNRESTRICTED `_walk_top_level`
    behavior whenever the exported name itself can't be resolved this
    way (`_exported_gt_name` returns `None`) -- there's no signal to
    restrict by in that case, so this stays a safe superset rather than
    silently excluding everything. A statement inside a nested `if`/
    `for`/`with`/`try` block, or a receiver expression that isn't a
    plain attribute chain, is NOT specially traced either -- excluded
    from the restricted scope like any other statement that doesn't
    directly, syntactically target the exported name, matching this
    corpus's own linear top-level script convention.

    2026-08-13 addition: this function's own `tree.body` loop -- unlike
    `_walk_top_level`'s internal stack -- filters each MODULE-level
    statement by `_stmt_targets_name` before ever calling `_walk_top_
    level` on it, so an `if __name__ == "__main__": build_table()`
    guard (an `ast.If`, not an `Assign`/`Expr`) never matched that filter
    and was skipped outright, even after `_walk_top_level` itself learned
    to unwrap it. Same fix, applied here too: when a top-level statement
    is that one special guard shape calling a module-level `def`, this
    walks the CALLED function's own body statements in its place,
    filtering each of THOSE by `_stmt_targets_name` exactly like any
    other module-level statement -- see `_walk_top_level`'s docstring for
    the exact false-negative (and the real candidates) this closes.
    """
    if not isinstance(tree, ast.Module):
        yield from _walk_top_level(tree)
        return
    exported_name = _exported_gt_name(tree)
    if exported_name is None:
        yield from _walk_top_level(tree)
        return
    main_guard_defs = _module_level_functions(tree)
    body_index = {id(n): i for i, n in enumerate(tree.body)}
    for guard_index, node in enumerate(tree.body):
        target_name = _main_guard_call_target(node)
        target_def = main_guard_defs.get(target_name)
        # Same "def must appear before the guard" rule as `_walk_top_level`
        # (2026-08-13 review finding) -- calling it any earlier is a real
        # `NameError` at runtime, not an inlined-equivalent script.
        if target_def is not None and body_index[id(target_def)] < guard_index:
            for inner in target_def.body:
                if not _stmt_targets_name(inner, exported_name):
                    continue
                yield from _walk_top_level(inner)
            continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if not _stmt_targets_name(node, exported_name):
            continue
        yield from _walk_top_level(node)


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

    Codex round-14 finding (bounded scope): now walks via `_walk_
    exported_scope` (built on `_walk_top_level`) instead of `_walk_top_
    level` directly -- a `frame(...)` call chained onto some OTHER,
    unused variable no longer counts toward the exported table's own
    frame. See `_walk_exported_scope`'s own docstring.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    for node in _walk_exported_scope(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr == func_name:
            return True
        if allow_bare and isinstance(func, ast.Name) and func.id == func_name:
            return True
    return False


def _spanner_present_local(source: str) -> bool:
    """AST-based replacement for convergence.py's own `spanner_present`
    field -- true if a genuine `.tab_spanner(...)` or `.tab_spanner_delim(
    ...)` call exists (both render column-group spanners -- a delimiter
    in column names via `tab_spanner_delim` counts too, not just an
    explicit `tab_spanner` call, matching convergence.py's own stated
    intent for this field).

    Codex round-13 finding: convergence.py's own `spanner_present` field
    (off-limits -- see this file's Tier-1 compatibility-shim section) is
    computed via `convergence._call_arg_blocks` (a source-wide regex with
    no comment/string stripping at all) -- the same recurring bug class
    already fixed for color-mechanics/frame/fmt_*/tab_options/tab_style/
    tab_header/stripe detection elsewhere in this file: a comment
    mentioning `.tab_spanner(...)` is misdetected as a real spanner.
    Switched to `_ast_call_arg_blocks` (AST-based).
    """
    return bool(_ast_call_arg_blocks(source, "tab_spanner") or _ast_call_arg_blocks(source, "tab_spanner_delim"))


def _source_note_texts_local(source: str) -> list[str | None]:
    """AST-based replacement for convergence.py's own `source_note_texts`
    field: literal text of every genuine `.tab_source_note(...)` call, in
    TRUE source order. ONE entry per call, always -- a call whose text
    can't be resolved statically (a dynamic expression, an f-string with
    an interpolation) contributes `None` rather than being dropped (see
    `convergence._source_note_texts`'s own docstring for why dropping
    would misalign the caption/source-note slot convention this
    comparator relies on).

    Codex round-14 finding: `convergence._source_note_texts` (off-limits
    -- see this file's Tier-1 compatibility-shim section) is computed via
    `convergence._call_arg_blocks` (a source-wide regex with no comment/
    string stripping at all) -- the same recurring bug class already
    fixed for color-mechanics/frame/fmt_*/tab_options/tab_style/tab_
    header/stripe/tab_spanner detection elsewhere in this file: a comment
    mentioning `.tab_source_note(...)` is misdetected as a real call.
    Switched to `_ast_call_arg_blocks` (AST-based) for call DETECTION;
    the per-block text extraction itself is unchanged (still `convergence.
    _kwarg_value`/`_split_top_level_quoted`/`_extract_text_literal`).
    """
    texts: list[str | None] = []
    for block in _ast_call_arg_blocks(source, "tab_source_note"):
        val = convergence._kwarg_value(block, "source_note")
        if val is None:
            positionals = [
                p for p in convergence._split_top_level_quoted(block) if not re.match(r"[A-Za-z_]\w*\s*=", p)
            ]
            val = positionals[0] if positionals else None
        texts.append(convergence._extract_text_literal(val) if val is not None else None)
    return texts


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
    - `.tab_options(table_border_<side>_...)`: per-side, framed only if
      that side's own style/width/color (whichever are set) are all
      non-disabling -- style not "none"/"hidden", width not a zero
      length, color not effectively transparent. Reuses `_is_zero_length`/
      `_is_effectively_transparent`, the same visibility tests applied
      elsewhere in this file. Codex round-10 finding: this returned `True`
      as soon as ONE side (left OR
      right) was visible, but this repo's own authoritative `gt_check.py`
      (already cited correctly in round 8's finding #4) requires BOTH a
      visible left AND a visible right border style for a genuine
      enclosing frame (`has_side_border_styles = _frame_style_set(source,
      "left") and _frame_style_set(source, "right")`) -- a single visible
      side is a partial border, not a box. Now requires BOTH sides.
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
    outline_blocks = _ast_call_arg_blocks(source, "opt_table_outline")
    if outline_blocks:
        style_val = convergence._kwarg_value(outline_blocks[-1], "style")
        disabled = False
        if style_val is not None:
            unquoted = convergence._unquote(style_val)
            disabled = bool(unquoted and unquoted.strip().lower() in ("none", "hidden"))
        if not disabled:
            return True
    def _side_border_visible(side: str) -> bool:
        # Sweep-A finding (round 8): `re.search` returns the FIRST
        # occurrence in the whole source -- a script setting an initial
        # border and overriding it later (or repeating the kwarg across
        # chained `.tab_options(...)` calls) had the ORIGINAL, overridden
        # value trusted instead of the one actually rendered.
        #
        # Codex round-12 finding (proactive AST conversion): this scanned
        # raw SOURCE TEXT via `re.findall`, with no comment/string
        # stripping -- the same recurring bug class already fixed for
        # `_option_line_present`/color-mechanics/etc. Extracts
        # from genuine `.tab_options(...)` AST call blocks (via `_ast_
        # call_arg_blocks`) instead, still taking the LAST occurrence of
        # each attribute across ALL real calls.
        style, width, color = None, None, None
        for block in _ast_call_arg_blocks(source, "tab_options"):
            style_val = convergence._kwarg_value(block, f"table_border_{side}_style")
            literal = _quoted_string_literal_value(style_val) if style_val is not None else None
            if literal is not None:
                style = literal
            width_val = convergence._kwarg_value(block, f"table_border_{side}_width")
            literal_w = _quoted_string_literal_value(width_val) if width_val is not None else None
            if literal_w is not None:
                width = literal_w
            color_val = convergence._kwarg_value(block, f"table_border_{side}_color")
            literal_c = _quoted_string_literal_value(color_val) if color_val is not None else None
            if literal_c is not None:
                color = literal_c
        # Codex round-12 finding: this previously accepted ANY ONE of
        # style/width/color as sufficient to proceed -- so setting ONLY
        # `table_border_{side}_color`/`_width` (no style at all) skipped
        # the (empty) style check entirely and returned True. But
        # great_tables defaults the side border STYLE to `"none"`
        # regardless of color/width -- an explicit, non-disabling style is
        # REQUIRED for this side to render at all, not merely checked
        # when present.
        if style is None or style.strip().lower() in ("none", "hidden", ""):
            return False
        if width is not None and convergence._is_zero_length(width):
            return False
        if color is not None and _is_effectively_transparent(color.strip()):
            return False
        return True

    # Codex round-10 finding: BOTH sides must be independently visible --
    # a lone visible left (or right) border alone is a partial rule, not
    # an enclosing box, matching `gt_check.py`'s own `has_side_border_
    # styles` requirement exactly.
    return _side_border_visible("left") and _side_border_visible("right")


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

    Codex round-12 finding (comprehensive sweep): scanned via `convergence.
    _call_arg_blocks` (a source-wide regex with no comment/string
    stripping) -- the same recurring bug class already fixed elsewhere in
    this file. Switched to `_ast_call_arg_blocks` (AST-based).
    """
    for block in _ast_call_arg_blocks(source, "tab_style"):
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

    Codex round-12 finding: this scanned raw SOURCE TEXT via `re.findall`,
    with no comment/string stripping at all -- the same recurring source-
    wide-regex bug class already fixed for color-mechanics/
    frame/fmt_*/heading-band-color/opt_row_striping detection: a comment
    mentioning `table_body_hlines_style="solid"` (or `"none"`) is
    misdetected as a real, score-affecting option. Extracts from genuine
    `.tab_options(...)` AST call blocks (via `_ast_call_arg_blocks`,
    already scoped to top-level-only calls per the round-9 `_walk_top_
    level` fix) instead of raw text -- still takes the LAST occurrence of
    each attribute ACROSS ALL real `tab_options()` calls, preserving the
    existing override-resolution behavior, and still only accepts a
    genuine quoted string literal as a value (via `_quoted_string_
    literal_value`), matching the original regex's own "only ever a
    quoted literal, never a bare variable" behavior exactly.
    """
    def _last(attr: str) -> str | None:
        last_val = None
        for block in _ast_call_arg_blocks(source, "tab_options"):
            val = convergence._kwarg_value(block, f"{prefix}_{attr}")
            literal = _quoted_string_literal_value(val) if val is not None else None
            if literal is not None:
                last_val = literal
        return last_val

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

    Fresh-sweep finding (2026-08-12, same family as `_frame_present`'s
    round-6 `frame(...)` helper check): `.claude/skills/great-tables-
    house/scripts/house_table.py` defines `hairlines(gt, color=None,
    width="1px", style="solid")` -- an UNCONDITIONAL helper (every table
    gets it, per its own docstring) whose body sets `table_body_hlines_
    style`/`_color`/`_width` via `tab_options(...)` INSIDE the helper's
    own function body, invisible to source-level parsing of a CANDIDATE
    script that only imports/calls `hairlines(gt)` -- it never inlines
    the helper's own body. Every `house`-skill candidate correctly
    calling this taught helper previously scored `hairlines_present=
    False` regardless, because neither `_option_line_present` nor
    `_has_visible_tab_style_border` can see literal `tab_options` kwargs
    that only exist inside the helper's own definition. Recognizing a
    genuine `hairlines(...)` CALL itself (via `_has_real_call`, the same
    AST-based approach `_frame_present` already uses for its own
    `frame(...)` helper -- immune to a candidate merely DEFINING its own
    `hairlines` function, a comment, or a docstring mention) closes this
    gap the same way, as an additional detection mechanism alongside the
    existing literal/tab_style checks below (which still correctly cover
    scripts that set the border directly instead of using this helper).
    """
    if _has_real_call(source, "hairlines", allow_bare=True):
        return True
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
    (inlined in `parse_design_choices`), but restricted to the mechanisms
    that actually ENABLE striping -- `opt_row_striping(...)`, `stripe(
    ...)`, or `row_striping_include_table_body=True` -- per this repo's
    own authoritative `.claude/skills/great-tables-ci/scripts/gt_check.py`
    (`check_striping_gate`'s own comment: "A bare `row_striping_
    background_color=` (color only) does NOT turn striping on, so it no
    longer counts").

    Codex round-10 finding: this previously ALSO treated a literal,
    non-transparent `row_striping_background_color=` as its own
    independent activation signal -- but that option only configures the
    stripe COLOR; it has no effect at all unless striping is separately
    enabled by one of the three real mechanisms above. Removed as an
    independent signal (still doesn't need its own visibility check,
    since it's not a mechanism this function trusts anymore).

    `opt_row_striping(row_striping: bool = True)` (verified against the
    installed `great_tables` signature) has no color parameter -- calling
    it with a truthy/omitted `row_striping` always means "stripe with
    great_tables' own default, visible color."

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
    pattern already used for hairlines/dividers).

    Codex round-14 finding: rounds 8/12 fixed "last call wins" WITHIN
    each mechanism independently, but the three mechanisms (`opt_row_
    striping(...)`, `tab_options(row_striping_include_table_body=True)`,
    `stripe(...)`) were still resolved via SEPARATE, fixed-priority
    early-return branches -- opt_row_striping's own last-call state
    checked first, then tab_options's, then stripe's mere existence.
    Mixing mechanisms in an order where a LATER, DIFFERENT-mechanism call
    should override an EARLIER one got the final state backwards: e.g.
    `stripe(gt)` (enables) followed by a LATER `.opt_row_striping(
    row_striping=False)` (explicitly disables) still returned `True`,
    because `stripe(...)`'s mere existence was checked independently of
    what the chronologically LATER opt_row_striping call said. All three
    mechanisms are now resolved as ONE chronologically-ordered sequence
    of (position, enabled) events -- the LAST event across ALL of them,
    not the last event within any single mechanism, determines the final
    state, exactly mirroring how a real render applies each call's
    effect in source order.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    events: list[tuple[tuple[int, int], bool]] = []

    for pos, block in _ast_call_blocks(source, tree, "opt_row_striping", allow_bare=False):
        val = convergence._kwarg_value(block, "row_striping")
        if val is None:
            positionals = [
                p for p in convergence._split_top_level(block) if not re.match(r"[A-Za-z_]\w*\s*=", p)
            ]
            val = positionals[0] if positionals else None
        if val is None:
            events.append((pos, True))  # omitted -- defaults to True per the installed signature
            continue
        unquoted = convergence._unquote(val)
        # Explicit True, or an unresolvable expression, is an ENABLING
        # event (benefit of the doubt); only an explicit `False` literal
        # is a DISABLING one.
        events.append((pos, not (unquoted and unquoted.strip() == "False")))

    # `row_striping_include_table_body` only ever contributes a POSITIVE
    # signal (matching this field's pre-existing semantics -- an explicit
    # `=False` here was never treated as an active disable, only as "no
    # signal from this mechanism," and this preserves that exactly, just
    # now correctly ordered relative to the other two mechanisms).
    for pos, block in _ast_call_blocks(source, tree, "tab_options", allow_bare=False):
        val = convergence._kwarg_value(block, "row_striping_include_table_body")
        if val is None:
            continue
        unquoted = convergence._unquote(val)
        if unquoted is not None and unquoted.strip() == "True":
            events.append((pos, True))

    # `stripe(...)` has no disabling parameter at all -- an unconditional
    # enabling event wherever it's called.
    for pos, _block in _ast_call_blocks(source, tree, "stripe", allow_bare=True):
        events.append((pos, True))

    if not events:
        return False
    events.sort(key=lambda e: e[0])
    return events[-1][1]


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
    return _blocks_target_table_png(finalize_blocks, "path", 1, var_literals, default_path="table.png")


def _render_params_local(source: str) -> dict:
    """Local replacement for `convergence._render_params`: `zoom`/
    `expand`/`vwidth`/`vheight` off the SAME render call `_render_call_
    present` determines actually produced `table.png` -- reusing its
    exact per-call resolved-target binding (`_ast_call_blocks` +
    `_render_target_var_literals`) instead of a separate, target-unaware
    "prefers a literal table.png text match" parser.

    Codex round-12 finding: `convergence._render_params` (off-limits) can
    only recognize a call as "targeting table.png" via its OWN literal-
    text check -- it has no knowledge of the per-call variable-resolution
    binding `_render_target_var_literals` (built in round 7/8
    specifically for `_render_call_present`). So `output = "table.png";
    gt.gtsave(output, zoom=2.0)` (correct) followed by an unrelated
    `gt.gtsave("backup.png", zoom=1.0)` had `render_call_present`
    correctly recognize the FIRST call as the one producing `table.png`
    (via the smarter binding), while `render_params` independently fell
    back to ITS OWN "last call overall" default (since NEITHER call
    textually/literally mentions "table.png" from its naive perspective)
    and scored the SECOND, unrelated call's zoom/expand values instead.
    Ported the same target-selection SHAPE `convergence._render_params`
    uses (prefer a call resolving to table.png; last-write-wins among
    multiple such calls; fall back to the overall last call when none
    resolves to table.png at all) but through the shared, smarter
    resolution machinery, so both checks agree on WHICH call actually
    produced the mandated artifact.

    Codex round-13 finding: this still mirrored `convergence._render_
    params`'s own STRUCTURE of trying every `gtsave(...)` call first and
    only falling back to `finalize(...)` calls when NO `gtsave(...)` call
    exists at all -- so a candidate using `finalize()` for the actual
    `table.png`-producing render, plus an unrelated `gtsave("backup.png",
    ...)` call elsewhere, never even considered the finalize call (since
    `gtsave_blocks` was non-empty) and scored the unrelated gtsave call's
    params instead. `gtsave(...)` and `finalize(...)` calls are now
    merged into ONE chronologically-ordered pool and the effective call
    is selected from that combined set, matching `_render_call_present`'s
    own "check both mechanisms together" semantics exactly.

    Fresh-sweep finding (2026-08-12, same gap as `_blocks_target_table_
    png`'s own `default_path` fix): this function's own nested `_call_
    targets_table_png` had the identical "path argument absent entirely
    -> not recognized" hole -- a bare `finalize(gt)` call (no explicit
    `path`) genuinely targets `table.png` via `finalize`'s own documented
    default, but was invisible to this selector, so its zoom/expand
    params were skipped over in favor of the LAST call overall (which
    could be an unrelated `gtsave("backup.png", ...)`) or simply
    excluded from ever being `chosen`. `_call_targets_table_png` now
    takes the same `default_path` (only ever supplied for `finalize`
    items, never `gtsave` items, matching `_blocks_target_table_png`'s
    own reasoning for why only `finalize` -- not `gtsave` -- gets one).
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {}
    var_literals = _render_target_var_literals(source, tree)

    def _call_targets_table_png(
        pos: tuple[int, int], block: str, path_kwarg: str, path_index: int, default_path: str | None = None
    ) -> bool:
        path_val = convergence._kwarg_value(block, path_kwarg)
        if path_val is None:
            positionals = [
                p for p in convergence._split_top_level_quoted(block) if not re.match(r"[A-Za-z_]\w*\s*=", p)
            ]
            path_val = positionals[path_index] if len(positionals) > path_index else None
        if path_val is None:
            return default_path is not None and convergence._targets_table_png(default_path)
        stripped = path_val.strip()
        if re.fullmatch(r"[A-Za-z_]\w*", stripped) and pos in var_literals:
            return convergence._targets_table_png(var_literals[pos])
        return _is_static_string_literal(stripped) and convergence._targets_table_png(path_val)

    def _extract_params(block: str, defaults: dict[str, str]) -> dict:
        # Same **overrides/**{...} guard as convergence._render_params --
        # an expansion can override the materialized defaults with values
        # this parser can't see.
        #
        # Codex round-14 finding: a genuinely no-op expansion (`**{}`/
        # `**dict()`, via `_is_noop_kwargs_expansion` -- already used for
        # this exact purpose in `_enrich_color_mechanics`/`_fmt_column_
        # map`) changes nothing at runtime and was wrongly treated
        # identically to a real, unresolvable `**overrides` expansion,
        # discarding params this parser CAN actually see just because a
        # no-op expansion happened to sit in the same call.
        if any(
            p.strip().startswith("**") and not _is_noop_kwargs_expansion(p)
            for p in convergence._split_top_level(block)
        ):
            return {}
        out = dict(defaults)
        for kw in ("zoom", "expand", "vwidth", "vheight"):
            v = convergence._kwarg_value(block, kw)
            if v is not None:
                out[kw] = v.strip()
        return out

    # Codex round-13 finding: this returned as soon as it found ANY
    # `gtsave(...)` call at all, never even looking at `finalize(...)`
    # calls in that case -- so a candidate using `finalize()` for the
    # CORRECT render (the one that actually produces `table.png`) plus a
    # separate, unrelated `gtsave("backup.png", ...)` call elsewhere had
    # this scored against the unrelated gtsave call's params instead,
    # even though `render_call_present`/`_blocks_target_table_png`
    # correctly recognize BOTH mechanisms together (checking gtsave OR
    # finalize, not gtsave THEN finalize only as a fallback when gtsave
    # is entirely absent). Both call forms are now merged into ONE
    # chronologically-ordered pool and the effective call is selected
    # from that combined set -- whichever call (from EITHER mechanism)
    # is the LAST one resolving to `table.png` wins; only when NONE of
    # them resolve to `table.png` does this fall back to the overall
    # last call from either mechanism.
    gtsave_items = [
        (pos, block, "file", 0, {"zoom": "2.0", "expand": "5"}, None)
        for pos, block in _ast_call_blocks(source, tree, "gtsave", allow_bare=False)
    ]
    finalize_items = [
        (pos, block, "path", 1, {"expand": "15", "zoom": "2.0"}, "table.png")
        for pos, block in _ast_call_blocks(source, tree, "finalize", allow_bare=True)
    ]
    combined = sorted(gtsave_items + finalize_items, key=lambda item: item[0])
    if not combined:
        return {}
    chosen = combined[-1]  # last-wins default when none resolves to table.png
    for item in combined:
        pos, block, path_kwarg, path_index, _defaults, default_path = item
        if _call_targets_table_png(pos, block, path_kwarg, path_index, default_path):
            chosen = item  # keep scanning -- a LATER table.png write (either mechanism) wins
    _, chosen_block, _, _, chosen_defaults, _chosen_default_path = chosen
    return _extract_params(chosen_block, chosen_defaults)


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

    Codex round-12 finding (comprehensive sweep): call sites were located
    via `convergence._call_arg_blocks` (a source-wide regex with no
    comment/string stripping) -- the same recurring bug class already
    fixed elsewhere in this file: a comment or docstring mentioning
    `tab_header(` was misdetected as a real call. Switched to `_ast_
    call_arg_blocks` (AST-based).
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

    blocks = _ast_call_arg_blocks(source, "tab_header")
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

    The sort key is `(end_lineno, end_col_offset)` -- true SOURCE ORDER
    (interleaving `data_color`/`heatmap` calls correctly) is all this
    needs, and a (line, byte-offset) pair sorts identically to a (line,
    char-offset) pair on the same line (both increase monotonically
    together), so there's no need to convert to a character offset just
    to preserve ordering.

    Codex round-13 finding: this originally keyed on `(node.lineno, node.
    col_offset)` -- the call's OWN START position. That's correct for
    calls in separate statements, but for a FLUENT CHAIN (`.tab_options(
    a=1).tab_options(a=2)`), EVERY link in the chain shares the exact
    SAME start position (a `Call` node's span starts at the beginning of
    its entire receiver chain -- see the docstring paragraph above -- so
    the outer, later call and the inner, earlier call both report the
    same `(lineno, col_offset)`). Sorting by a tied key falls back to
    Python's stable-sort, which preserves `_walk_top_level`'s own
    traversal order -- and that traversal visits the OUTER (later,
    effective) call before the INNER (earlier) one, so every consumer
    reading `blocks[-1]` to mean "the last/effective call" actually got
    the chronologically FIRST one for chained calls specifically. `end_
    lineno`/`end_col_offset` don't have this problem: each link's END
    position is exactly where ITS OWN closing paren is, strictly
    increasing outward through the chain (the outer call's closing paren
    always comes after every inner call's), so it correctly orders both
    chained AND separate-statement calls alike.

    Codex round-14 finding (bounded scope): now walks via `_walk_exported_
    scope` (built on `_walk_top_level`) instead of `_walk_top_level`
    directly -- a call chained onto some OTHER, unused variable
    (`preview = GT(df).data_color(...)` while the actually exported `gt`
    stays uncolored) no longer counts. See `_walk_exported_scope`'s own
    docstring.
    """
    out: list[tuple[tuple[int, int], str]] = []
    for node in _walk_exported_scope(tree):
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
        out.append(((node.end_lineno, node.end_col_offset), block))
    return out


def _ast_call_arg_blocks(source: str, func_name: str, *, allow_bare: bool = False) -> list[str]:
    """AST-based replacement for `convergence._call_arg_blocks` -- same
    `list[str]` shape (one entry per genuine call's argument block text,
    in true source order), built from `_ast_call_blocks` instead of a
    source-wide regex, so it's a drop-in replacement at call sites that
    don't need the position info `_ast_call_blocks` itself returns.

    Codex round-11 finding: `convergence._call_arg_blocks` (off-limits --
    see this file's Tier-1 compatibility-shim section) is a source-wide
    regex with no comment/string stripping at all -- the same recurring
    bug class already fixed for color-mechanics/frame/fmt_*/
    tab_options detection: `# .opt_row_striping()` in a comment, or a
    docstring mentioning the same text, is misdetected as a real call.
    Used for `opt_row_striping` (the flagged case) and, proactively, for
    `opt_table_outline` right next to it in `_frame_present` -- the
    identical vulnerability on the identical kind of call, not separately
    flagged but the same fix.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    blocks = sorted(_ast_call_blocks(source, tree, func_name, allow_bare), key=lambda b: b[0])
    return [block for _, block in blocks]


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

    Codex round-13 finding: sorted on `(node.lineno, node.col_offset)` --
    the call's OWN START position, which every link of a FLUENT CHAIN
    (`.fmt_number(...).fmt_percent(...)`) shares identically (see `_ast_
    call_blocks`'s own round-13 docstring paragraph for the full
    explanation) -- so a stable sort on a tied key could put the later,
    effective call before the earlier one. Sorts on `(end_lineno, end_
    col_offset)` instead, which strictly increases outward through a
    chain and still increases correctly across separate statements.

    Codex round-14 finding (bounded scope): now walks via `_walk_exported_
    scope` (built on `_walk_top_level`) instead of `_walk_top_level`
    directly -- a `.fmt_*(...)` call chained onto some OTHER, unused
    variable no longer counts. See `_walk_exported_scope`'s own
    docstring.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    out: list[tuple[tuple[int, int], str, str]] = []
    for node in _walk_exported_scope(tree):
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
        out.append(((node.end_lineno, node.end_col_offset), func.attr, block))
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
    domain into what looks like the same `(palette, domain)` measure when
    counting distinct colored measures (`_distinct_colored_measures`, used
    by `check_hue_collision`). Mirrors the positional handling every other
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


# The small, fixed set of `cs.<kind>("pattern")` column-selector shapes this
# file actually resolves -- NOT full tidyselect emulation (a compound
# expression via `|`/`&`/`~`, or any other `cs.*` function, stays genuinely
# unresolved). Each maps to a simple, one-argument STRING predicate against a
# real column name.
_CS_SELECTOR_KINDS = ("starts_with", "ends_with", "contains", "matches")


class _PendingColumnSelector:
    """A SIMPLE, single `cs.<kind>("pattern")` column-selector expression
    (see `_CS_SELECTOR_KINDS`) whose actual target columns can't be known
    until Tier-2's real visible-columns schema is available -- resolved
    lazily by `_mechanics_columns` once both tiers exist together, unlike
    `_UNRESOLVED_COLUMNS` (a selector this file doesn't know how to
    resolve AT ALL, even with the schema, e.g. a compound expression or
    an unrecognized `cs.*` function).

    Codex round-10 finding: `cs.starts_with(...)`/`ends_with`/`contains`/
    `matches` are a small, fixed set of prefix/suffix/substring/regex
    patterns (not full tidyselect emulation) -- Codex found a concrete
    real-world case where treating this as unresolved cost real points:
    `cs.starts_with("density_")` matches EXACTLY the density columns in
    `towny_growth_trends`'s own ground truth, and an equivalent candidate
    using that selector lost up to 9 points across the checks that
    iterate a colored measure's columns (identity, signedness, domain,
    striping coverage) purely because the selector was treated as
    "unknowable," despite its target being perfectly resolvable once the
    real column list is available.
    """

    __slots__ = ("kind", "pattern")

    def __init__(self, kind: str, pattern: str):
        self.kind = kind
        self.pattern = pattern

    def __repr__(self) -> str:
        # A few check functions interpolate `entry.get("columns")` directly
        # into a human-readable detail/notes string -- a readable `repr`
        # here (matching the source syntax) keeps those reports legible
        # instead of printing a bare object address.
        return f"cs.{self.kind}({self.pattern!r})"


def _parse_cs_selector(cols_val: str) -> tuple[str, str] | None:
    """Parse a SIMPLE, STANDALONE `cs.<kind>("pattern")` expression into
    `(kind, pattern)`, else `None` for anything this file doesn't
    implement: a compound expression (`cs.starts_with("a") | cs.ends_
    with("b")` -- rejected via the "nothing may follow this call's own
    closing paren" check below), an unrecognized `cs.*` function, or a
    non-literal/dynamic pattern argument (`cs.starts_with(prefix_var)`).
    All of those keep the existing `_UNRESOLVED_COLUMNS` benefit-of-the-
    doubt treatment, unchanged.
    """
    text = cols_val.strip()
    m = re.match(r"^cs\s*\.\s*(\w+)\s*\(", text)
    if not m:
        return None
    kind = m.group(1)
    if kind not in _CS_SELECTOR_KINDS:
        return None
    open_idx = m.end() - 1
    close_idx = convergence._scan_balanced_paren(text, open_idx)
    if close_idx is None:
        return None
    if text[close_idx + 1:].strip():
        return None  # trailing text after this call -- a compound expression
    arg_text = text[open_idx + 1 : close_idx]
    positionals = [
        p for p in convergence._split_top_level_quoted(arg_text) if not re.match(r"[A-Za-z_]\w*\s*=", p)
    ]
    pattern_val = convergence._kwarg_value(arg_text, "pattern") or (positionals[0] if positionals else None)
    pattern = _quoted_string_literal_value(pattern_val) if pattern_val else None
    if pattern is None:
        return None  # a dynamic/variable pattern argument -- can't resolve statically
    return kind, pattern


def _cs_selector_matches(kind: str, pattern: str, column: str) -> bool:
    """Does `column` match the SIMPLE `cs.<kind>("pattern")` selector --
    the same one-argument string predicate great_tables' own `cs.<kind>`
    applies (a case-sensitive Python string operation for the first
    three; `re.search` for `matches`, since that's the one genuinely
    regex-based selector). An invalid regex pattern (can't happen for a
    real great_tables script, but keeps this total) matches nothing
    rather than raising.
    """
    if kind == "starts_with":
        return column.startswith(pattern)
    if kind == "ends_with":
        return column.endswith(pattern)
    if kind == "contains":
        return pattern in column
    if kind == "matches":
        try:
            return re.search(pattern, column) is not None
        except re.error:
            return False
    return False


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

# A distinct sentinel for "a `.fmt_percent(...)` call's `scale_values=`
# argument IS present but its value is genuinely UNRESOLVABLE from static
# text" (a variable, an expression) -- deliberately NOT the same as `None`,
# which `_fmt_percent_scale_values_map`'s callers get from a plain
# `dict.get()` miss (a column NEVER touched by any `fmt_percent(...)` call
# at all, which really does resolve to great_tables' own `True` default with
# total confidence). Codex round-12 finding: collapsing "explicitly
# unresolvable" and "never set" into the same bare `None` made `_fmt_covers_
# semantic_type` default an UNRESOLVABLE override to `"True"` for validation
# purposes -- correct benefit-of-the-doubt when the matched column's data is
# fractional (True is right), but an active WRONG-answer assumption when the
# data is percentage-scale (False is right) -- rather than a genuine "don't
# penalize either way" skip.
_UNRESOLVED_SCALE_VALUES = object()

# Same sentinel shape as `_UNRESOLVED_SCALE_VALUES`, for `.fmt_number(...)`'s
# `decimals=` argument (round 14) -- `None` from `_fmt_number_decimals_map`
# means "never touched by any fmt_number(...) call at all" (confidently
# resolves to great_tables' own `decimals=2` default); this sentinel means
# "touched, but the argument itself is unresolvable" (a variable, an
# expression) -- kept distinct so `_fmt_covers_semantic_type` doesn't default
# an unresolvable expression to the wrong assumption either way.
_UNRESOLVED_FMT_NUMBER_DECIMALS = object()

# Same sentinel shape as `_UNRESOLVED_SCALE_VALUES`/`_UNRESOLVED_FMT_NUMBER_
# DECIMALS`, for `.fmt_percent(...)`'s `force_sign=` argument -- "touched by
# a call, but the argument itself is unresolvable" (a variable, an
# expression), distinct from `None` ("never touched at all," which resolves
# with total confidence to great_tables' own `force_sign=False` default).
# See `check_force_sign`.
_UNRESOLVED_FORCE_SIGN = object()
# `heatmap()`'s own hue->palette resolution table, mirroring `.claude/
# skills/great-tables-ci/scripts/gt_consistency.py`'s `PALETTE["sequential"]`/
# `PALETTE["diverging"]` dicts and its `_resolve_palette(kind, hue)` helper
# EXACTLY (`colorblind_safe` resolves to the FIRST of its two alternatives,
# `["RdBu", "PuOr"]`, same as `_resolve_palette` itself does for a
# list-valued diverging entry) -- see `_resolve_heatmap_palette` below.
_HEATMAP_SEQUENTIAL_HUE_TO_PALETTE = {
    "positive": "Greens",
    "warning": "Reds",
    "warning_alt": "Oranges",
    "neutral": "Blues",
}
_HEATMAP_DIVERGING_HUE_TO_PALETTE = {
    "default": "RdYlGn",
    "colorblind_safe": "RdBu",
}


def _resolve_heatmap_palette(kind: str | None, hue: str | None) -> str | None:
    """Mirror `gt_consistency.py`'s own `_resolve_palette(kind, hue)`: a
    `heatmap(..., hue=...)` call's `hue` is a SEMANTIC KEY (e.g.
    `"neutral"`, `"positive"`) resolved to an actual ColorBrewer palette
    NAME at runtime through the skill's own `PALETTE` dict -- NOT the
    effective color itself. An explicit palette name (or DA-family name,
    e.g. `hue="navy"`) that isn't one of the recognized semantic keys
    passes through unchanged, exactly as `_resolve_palette` does for "any
    other literal the model chose directly."

    Codex round-9 finding: `_enrich_color_mechanics`'s heatmap branch
    stored the RAW `hue=` key directly as `"palette"` -- so `heatmap(...,
    kind="sequential", hue="neutral")` (which `gt_consistency.py` itself
    resolves to the `"Blues"` palette at runtime) couldn't be connected
    to the navy DA-family for band harmonization (`_SEQ_PALETTE_TO_DA_
    FAMILY`, keyed on ColorBrewer names), and couldn't be detected as
    colliding with a literal `data_color(..., palette="Blues")` call on a
    DIFFERENT measure, even though both render the exact same effective
    color. `hue="navy"` (a DA-family name passed directly, per round-2's
    own finding on this same branch) still passes through unresolved
    here, unchanged from before -- `check_band_hue_harmonization`'s
    existing `elif sole_palette in _EXTENDED_FAMILY_HEXES` branch already
    handles that case correctly.
    """
    if hue is None:
        return None
    if kind == "sequential":
        return _HEATMAP_SEQUENTIAL_HUE_TO_PALETTE.get(hue, hue)
    if kind == "diverging":
        return _HEATMAP_DIVERGING_HUE_TO_PALETTE.get(hue, hue)
    return hue


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
    measure" when counting distinct colored measures). `build_fingerprint()` below replaces
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
            # Codex round-10 finding: a SIMPLE `cs.<kind>("pattern")` call
            # (see `_CS_SELECTOR_KINDS`) is resolvable once Tier-2's real
            # column schema is available -- deferred via `_PendingColumn
            # Selector` instead of the blanket `_UNRESOLVED_COLUMNS`
            # sentinel; only a genuinely unparseable/compound/dynamic
            # selector still falls back to that.
            parsed = _parse_cs_selector(cols_val)
            resolved_columns = _PendingColumnSelector(*parsed) if parsed is not None else _UNRESOLVED_COLUMNS
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
            # See the identical `_PendingColumnSelector` handling in the
            # `data_color` branch above (Codex round-10 finding).
            parsed = _parse_cs_selector(heatmap_cols_val)
            resolved_heatmap_columns = _PendingColumnSelector(*parsed) if parsed is not None else _UNRESOLVED_COLUMNS
        else:
            resolved_heatmap_columns = convergence._resolve_columns_list(heatmap_cols_val, var_map)
        hue_raw = convergence._kwarg_value(block, "hue")
        kind_literal = _quoted_string_literal_value(convergence._kwarg_value(block, "kind"))
        hue_literal = _quoted_string_literal_value(hue_raw)
        # Codex round-9 finding: `hue=` is a SEMANTIC KEY (e.g. "neutral")
        # resolved to an actual palette NAME ("Blues") at runtime by the
        # skill's own `_resolve_palette` -- storing the raw key here (as
        # this used to) made a helper call invisible to band-harmonization
        # and hue-collision checks that key on the ACTUAL ColorBrewer
        # name. See `_resolve_heatmap_palette`'s own docstring.
        resolved_palette = _resolve_heatmap_palette(kind_literal, hue_literal)
        entries.append((pos, {
            "columns": resolved_heatmap_columns,
            "palette": resolved_palette or "default",
            "palette_raw": hue_raw.strip() if hue_raw else None,
            "domain": convergence._kwarg_value(block, "domain"),
            "kind": kind_literal,
            "na_color": "#808080",
            "truncate": "False",
            "autocolor_text": "True",
            "reverse": "False",
            "via_helper": True,
        }))
    entries.sort(key=lambda e: e[0])
    return [d for _, d in entries]


def _fmt_column_map(source: str, visible_columns: set[str] | None = None) -> dict[str, str | bool]:
    """Best-effort `{source column -> the EFFECTIVE fmt_* name}`, with a
    special `convergence._ALL_COLUMNS` sentinel key for "every column not
    otherwise listed gets THIS formatter."

    Codex round-11 finding: a `columns=cs.starts_with(...)`-style
    selector (see `_PendingColumnSelector`/`_parse_cs_selector`/`_cs_
    selector_matches`, built in round 10 for color-mechanics resolution)
    previously went straight to `convergence._resolve_columns_list`,
    which returns `[]` for ANY selector expression -- so a `fmt_percent(
    columns=cs.starts_with("density_"))` call's target columns were
    silently invisible to this map entirely, the exact same round-10
    color-mechanics bug, now fixed for formatter calls too. `visible_
    columns` (Tier-2's real column list; `build_fingerprint` now computes
    Tier 2 BEFORE calling this, specifically so it's available here) lets
    a SIMPLE, single selector resolve directly at call time instead of
    deferring the way `_mechanics_columns` has to -- this function's
    return shape is a plain `{column: formatter}` dict, not a lazily-
    resolved entry list, so there's no later resolution point to defer
    to. A compound/dynamic/unrecognized selector (or a caller that
    doesn't pass `visible_columns` at all) still resolves to no columns,
    unchanged from before.

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

    def _resolve_cols(val: str) -> list[str]:
        if visible_columns is not None and _is_unresolvable_columns_selector(val):
            parsed = _parse_cs_selector(val)
            if parsed is not None:
                kind, pattern = parsed
                return sorted(c for c in visible_columns if _cs_selector_matches(kind, pattern, c))
        return convergence._resolve_columns_list(val, var_map)

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
                for col in _resolve_cols(val):
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
        for col in _resolve_cols(val):
            out[col] = name
    return out


def _fmt_percent_scale_values_map(source: str, visible_columns: set[str] | None) -> dict[str, object]:
    """`{column-or-_ALL_COLUMNS -> the resolved `scale_values=` state}`
    for every `.fmt_percent(...)` call, using the same column-resolution
    (positional/`_ALL_COLUMNS` sentinel/`cs.*` selector) as `_fmt_column_
    map`, but tracking `scale_values` instead of the formatter name --
    the one kwarg that changes what the RENDERED VALUE actually looks
    like for `fmt_percent` specifically (great_tables multiplies by 100
    when `scale_values=True`, its own default, and does NOT when
    `False`). A LATER call overrides an earlier one for the same column,
    same "last call wins" convention used throughout this file. A value
    is either `"True"`/`"False"` (a resolved literal -- an OMITTED kwarg
    resolves to `"True"`, great_tables' own default, not "nothing to
    record") or `_UNRESOLVED_SCALE_VALUES` (explicitly present but
    UNRESOLVABLE, e.g. a variable) -- the sentinel still overrides/clears
    whatever an earlier call recorded for the same column, since the
    later call is what actually determines the final rendered state even
    though this file can't see what it resolves to; it's deliberately
    NOT plain `None` (see that sentinel's own module-level comment for
    why the distinction matters to `_fmt_covers_semantic_type`).

    Codex round-11 finding: a candidate using `fmt_percent(columns=...,
    scale_values=False)` on genuinely FRACTIONAL ratio data (e.g. 0.05 to
    0.95) renders values 100x too small (`"0.05%"` instead of `"5%"`) --
    a real, meaningful data-fidelity bug -- but still earned full
    semantic-formatting credit, since `_fmt_column_map`/`check_fmt_
    semantic_type` only ever checked the METHOD NAME (`fmt_percent`),
    never this kwarg. See `_fmt_covers_semantic_type`'s own docstring for
    how this map's output is actually validated against the matched
    column's real data shape.

    Codex round-12 finding: the round-11 version `continue`d (recorded
    nothing at all) whenever `scale_values` was omitted OR unresolvable,
    which left a STALE earlier value in place for either case -- a LATER
    `fmt_percent(columns="rate")` (omitting `scale_values`, meaning
    "restore the True default") didn't override an earlier call's
    recorded `scale_values=False` for the same column at all. Omitted now
    resolves to the explicit literal `"True"` (great_tables' real
    default); a present-but-unresolvable value now explicitly clears
    (`_UNRESOLVED_SCALE_VALUES`) any prior entry for its columns instead
    of leaving it untouched, so a caller's `dict.get(col, dict.get(
    _ALL_COLUMNS))` lookup correctly stops at the sentinel rather than
    silently falling through to an unrelated, possibly stale `_ALL_
    COLUMNS` default.
    """
    var_map = convergence._list_var_map(source)

    def _resolve_cols(val: str) -> list[str]:
        if visible_columns is not None and _is_unresolvable_columns_selector(val):
            parsed = _parse_cs_selector(val)
            if parsed is not None:
                kind, pattern = parsed
                return sorted(c for c in visible_columns if _cs_selector_matches(kind, pattern, c))
        return convergence._resolve_columns_list(val, var_map)

    out: dict[str, object] = {}
    for name, block in _ast_fmt_calls(source):
        if name != "fmt_percent":
            continue
        positionals = [
            p for p in convergence._split_top_level_quoted(block)
            if not re.match(r"[A-Za-z_]\w*\s*=", p) and not p.strip().startswith("**")
        ]
        val = convergence._kwarg_value(block, "columns")
        if val is None:
            val = positionals[0] if positionals else None
        scale_val = convergence._kwarg_value(block, "scale_values")
        if scale_val is None:
            # Genuinely omitted from this call -- great_tables' own
            # default (True) applies, explicitly overriding whatever an
            # earlier call recorded for these columns.
            scale_literal: object = "True"
        else:
            unquoted = convergence._unquote(scale_val)
            resolved = unquoted.strip() if unquoted else None
            # Present but not a plain True/False literal (a variable, an
            # expression) -- unresolvable, but this call still OVERRIDES
            # any earlier recorded value for these columns;
            # `_UNRESOLVED_SCALE_VALUES` marks that explicitly rather
            # than leaving the stale entry alone.
            scale_literal = resolved if resolved in ("True", "False") else _UNRESOLVED_SCALE_VALUES
        if val is None or val.strip() == "None":
            out[convergence._ALL_COLUMNS] = scale_literal
            continue
        for col in _resolve_cols(val):
            out[col] = scale_literal
    return out


def _fmt_percent_force_sign_map(source: str, visible_columns: set[str] | None) -> dict[str, object]:
    """`{column-or-_ALL_COLUMNS -> the resolved `force_sign=` state}` for
    every `.fmt_percent(...)` call, mirroring `_fmt_percent_scale_values_
    map`'s exact column-resolution/override-tracking shape but for
    `force_sign` -- the kwarg that puts a leading "+" on a positive percent
    value (great_tables' own default is `force_sign=False`, a bare
    "3.8%"). Every current ground truth with a genuinely SIGNED percent
    measure (pct_change, growth %, best/worst day -- anything that can be
    either a gain or a loss) uses `force_sign=True`, so a reader can tell
    +3.8% from -3.8% at a glance without checking for a minus sign alone.
    See `check_force_sign`, which only requires this for a percent column
    whose real data actually crosses zero -- an always-positive percent
    has no genuine "sign" to force.
    """
    var_map = convergence._list_var_map(source)

    def _resolve_cols(val: str) -> list[str]:
        if visible_columns is not None and _is_unresolvable_columns_selector(val):
            parsed = _parse_cs_selector(val)
            if parsed is not None:
                kind, pattern = parsed
                return sorted(c for c in visible_columns if _cs_selector_matches(kind, pattern, c))
        return convergence._resolve_columns_list(val, var_map)

    out: dict[str, object] = {}
    for name, block in _ast_fmt_calls(source):
        if name != "fmt_percent":
            continue
        positionals = [
            p for p in convergence._split_top_level_quoted(block)
            if not re.match(r"[A-Za-z_]\w*\s*=", p) and not p.strip().startswith("**")
        ]
        val = convergence._kwarg_value(block, "columns")
        if val is None:
            val = positionals[0] if positionals else None
        fs_val = convergence._kwarg_value(block, "force_sign")
        if fs_val is None:
            # Genuinely omitted from this call -- great_tables' own
            # default (False) applies, explicitly overriding whatever an
            # earlier call recorded for these columns.
            fs_literal: object = "False"
        else:
            unquoted = convergence._unquote(fs_val)
            resolved = unquoted.strip() if unquoted else None
            fs_literal = resolved if resolved in ("True", "False") else _UNRESOLVED_FORCE_SIGN
        if val is None or val.strip() == "None":
            out[convergence._ALL_COLUMNS] = fs_literal
            continue
        for col in _resolve_cols(val):
            out[col] = fs_literal
    return out


def _fmt_number_decimals_map(source: str, visible_columns: set[str] | None) -> dict[str, object]:
    """`{column-or-_ALL_COLUMNS -> the resolved `decimals=` state}` for
    every `.fmt_number(...)` call, mirroring `_fmt_percent_scale_values_
    map`'s exact column-resolution/override-tracking shape but for
    `decimals` (an integer, not a boolean) -- the kwarg that determines
    whether `fmt_number` actually renders a clean integer (`decimals=0`)
    or shows fractional digits (great_tables' own default, `decimals=2`,
    verified against the installed signature, when omitted). A value is
    either a resolved literal integer STRING (an omitted kwarg resolves
    to `"2"`, great_tables' real default, not "nothing to record") or
    `_UNRESOLVED_FMT_NUMBER_DECIMALS` (present but unresolvable, e.g. a
    variable) -- the sentinel still overrides/clears whatever an earlier
    call recorded for the same column, same "last call wins" convention
    used throughout this file.

    Codex round-14 finding: `fmt_number` was accepted for `"integer"`-
    semantic-typed columns purely by METHOD NAME (see `_fmt_covers_
    semantic_type`) -- but `.fmt_number(columns="hp", decimals=2)` (or
    simply omitting `decimals=`, which defaults to `2`) renders `"200.00
    "` for what should be a clean integer count, yet still earned full
    semantic-formatting credit.
    """
    var_map = convergence._list_var_map(source)

    def _resolve_cols(val: str) -> list[str]:
        if visible_columns is not None and _is_unresolvable_columns_selector(val):
            parsed = _parse_cs_selector(val)
            if parsed is not None:
                kind, pattern = parsed
                return sorted(c for c in visible_columns if _cs_selector_matches(kind, pattern, c))
        return convergence._resolve_columns_list(val, var_map)

    out: dict[str, object] = {}
    for name, block in _ast_fmt_calls(source):
        if name != "fmt_number":
            continue
        positionals = [
            p for p in convergence._split_top_level_quoted(block)
            if not re.match(r"[A-Za-z_]\w*\s*=", p) and not p.strip().startswith("**")
        ]
        val = convergence._kwarg_value(block, "columns")
        if val is None:
            val = positionals[0] if positionals else None
        decimals_val = convergence._kwarg_value(block, "decimals")
        if decimals_val is None:
            decimals_literal: object = "2"  # great_tables' own default when omitted
        else:
            stripped = decimals_val.strip()
            decimals_literal = stripped if re.fullmatch(r"-?\d+", stripped) else _UNRESOLVED_FMT_NUMBER_DECIMALS
        if val is None or val.strip() == "None":
            out[convergence._ALL_COLUMNS] = decimals_literal
            continue
        for col in _resolve_cols(val):
            out[col] = decimals_literal
    return out


def _scale_shape_from_values(vals: list[float]) -> str | None:
    """Classify a set of numeric values as `"fractional"` (max absolute
    value comfortably `<= 1.5` -- e.g. 0.05-0.95, a ratio that NEEDS
    `fmt_percent`'s default `scale_values=True` to render as a real
    percentage) or `"percentage_scale"` (max absolute value comfortably
    `> 10` -- e.g. 5-95, a value that ALREADY IS the percentage number
    and needs `scale_values=False`). Returns `None` -- genuinely
    ambiguous, or no usable values at all -- for anything in between or
    unresolvable, same benefit-of-the-doubt convention as every other
    "can't verify from what's available" case in this file. The gap
    between the two thresholds is deliberate: a value like `3` could
    plausibly be either a growth ratio slightly over 1 or a small
    percentage, so it's left unclassified rather than guessed.
    """
    if not vals:
        return None
    max_abs = max(abs(v) for v in vals)
    if max_abs <= 1.5:
        return "fractional"
    if max_abs > 10:
        return "percentage_scale"
    return None


def _values_scale_shape(tier2: dict, column: str) -> str | None:
    """`_scale_shape_from_values` over every usable numeric value in
    `tier2`'s `column` (a whole body column)."""
    vals: list[float] = []
    for v in tier2.get("columns", {}).get(column, []) or []:
        if v is None:
            continue
        try:
            vals.append(float(v))
        except (TypeError, ValueError):
            continue
    return _scale_shape_from_values(vals)


def _value_scale_shape(v: Any) -> str | None:
    """`_scale_shape_from_values` for a single scalar value (a summary-row
    aggregate, not a whole column)."""
    try:
        fv = float(v)
    except (TypeError, ValueError):
        return None
    return _scale_shape_from_values([fv])


def build_fingerprint(py_path: Path) -> dict:
    """Tier 1 + Tier 2 fingerprint for one `table.py` (candidate OR ground
    truth — both are built identically, per the spec's "computed the same
    way" instruction).

    Overrides/adds Tier-1 fields (`color_mechanics`,
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
    `check_hue_collision`/`check_domain_computation`/
    `check_render_mechanics`/`check_band_hue_harmonization` without this
    shim). `title_present`/`caption_present` were separately found (Codex
    round-1) to have their own, unrelated bugs (keyword-only, all-calls-not-
    last-call) even though they aren't part of the vendoring-skew story --
    fixed here for the same "keep the compatibility shim" reason: `runner/
    convergence.py` is a hard non-goal for this slice either way, so the
    fix lives here instead, built only from primitives convergence.py
    already exposes.

    Codex round-11 finding: Tier 2 is now computed BEFORE the Tier-1 shim
    block below (it used to run last) specifically so `_fmt_column_map`
    can resolve a `cs.starts_with(...)`-style selector's `columns=`
    against the REAL visible-column list, the same way `_mechanics_
    columns` already does for color calls (round 10) -- see `_fmt_
    column_map`'s own docstring. Nothing else in the shim block below
    depends on Tier 2, so this reordering is a pure "compute it earlier"
    change with no other behavioral effect.
    """
    source = py_path.read_text()
    tier1 = convergence.parse_design_choices(source)
    tier2 = execution_tier.exec_table(py_path)
    visible_columns = set(tier2.get("columns", {}).keys()) - set(tier2.get("hidden_columns") or [])
    tier1["color_mechanics"] = _enrich_color_mechanics(source)
    tier1["render_call_present"] = _render_call_present(source)
    # Codex round-12 finding: convergence.py's own `render_params` can
    # only recognize a call as "targeting table.png" via a literal-text
    # check, with no knowledge of the per-call variable-resolution
    # binding `render_call_present` (just above) uses -- see `_render_
    # params_local`'s own docstring.
    tier1["render_params"] = _render_params_local(source)
    # Codex round-13 finding: convergence.py's own `spanner_present` is a
    # source-wide regex scan with no comment/string stripping -- see
    # `_spanner_present_local`'s own docstring.
    tier1["spanner_present"] = _spanner_present_local(source)
    # Codex round-14 finding: convergence.py's own `source_note_texts` is
    # a source-wide regex scan with no comment/string stripping -- see
    # `_source_note_texts_local`'s own docstring.
    tier1["source_note_texts"] = _source_note_texts_local(source)
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
    tier1["fmt_column_map"] = _fmt_column_map(source, visible_columns)
    # Codex round-11 finding: see `_fmt_percent_scale_values_map`'s own
    # docstring -- `fmt_percent`'s `scale_values` kwarg is tracked
    # separately from the formatter-name map above so `check_fmt_
    # semantic_type`/`check_summary_row_formatting` can validate it
    # against the matched column's actual data shape.
    tier1["fmt_percent_scale_values_map"] = _fmt_percent_scale_values_map(source, visible_columns)
    # See `_fmt_percent_force_sign_map`'s own docstring -- `fmt_percent`'s
    # `force_sign` kwarg is tracked separately so `check_force_sign` can
    # validate it against a signed percent-semantic column's real data.
    tier1["fmt_percent_force_sign_map"] = _fmt_percent_force_sign_map(source, visible_columns)
    # Codex round-14 finding: see `_fmt_number_decimals_map`'s own
    # docstring -- `fmt_number`'s `decimals` kwarg is tracked separately
    # so `check_fmt_semantic_type`/`check_summary_row_formatting` can
    # validate it against `"integer"` semantic-typed columns.
    tier1["fmt_number_decimals_map"] = _fmt_number_decimals_map(source, visible_columns)
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

    Codex round-10 finding: `entry["columns"]` can ALSO be a
    `_PendingColumnSelector` -- a SIMPLE `cs.<kind>("pattern")` call (see
    that class's own docstring) that couldn't be resolved at Tier-1 parse
    time (no schema available yet) but CAN be resolved now, against the
    same visible-columns base the `None` ("every column") sentinel
    already expands against, filtered down to whichever columns actually
    match the selector's own pattern.
    """
    cols = entry.get("columns")
    if cols is _UNRESOLVED_COLUMNS:
        return []
    tier2 = fp["tier2"]
    if isinstance(cols, _PendingColumnSelector):
        visible = _visible_columns(fp) - {tier2.get("stub_column"), tier2.get("group_column")}
        return sorted(c for c in visible if _cs_selector_matches(cols.kind, cols.pattern, c))
    if cols is not None:
        return cols
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
    coincidence) into 1 -- silently under-reporting the hue-collision/
    band-harmonization checks. `columns`
    here is the RESOLVED column tuple (via `_mechanics_columns`, the same
    resolution every other check already uses), not the raw, possibly-
    `None` `entry["columns"]` sentinel -- two entries whose `columns=None`
    sentinel resolves to the SAME actual visible-column set still
    correctly collapse to one measure. Sorted for a deterministic
    iteration order (mirrors round-2's hue-collision fix, which stopped
    trusting Python's hash-randomized set order for this same kind of
    dedup).

    Codex round-12 finding (comprehensive sweep): the dedup key's
    `columns` didn't intersect with `fp`'s actually-VISIBLE columns -- a
    colored measure entirely hidden via `cols_hide(...)` still counted as
    a real, distinct measure toward hue-collision detection
    (`check_hue_collision`, the only current caller of this helper --
    `check_band_hue_harmonization` is retired to an `_na` stub as of the
    2026-08-12 comparator generalization and no longer calls it) -- this
    exists to police what's ACTUALLY VISIBLE on the rendered table, not
    raw call syntax. An entry whose
    resolved columns have NO overlap with the visible-column set
    contributes nothing and is dropped entirely; an entry with a PARTIAL
    overlap (some, but not all, target columns hidden) is deduplicated by
    its VISIBLE subset only. Deliberately NOT applied to `_mechanics_
    columns` itself -- the domain/shape-validation checks need the FULL
    target list regardless of visibility, since a hidden column's
    underlying data and color mechanics are still real and worth
    validating; only the "how many/which VISIBLE distinct measures exist"
    question this function answers needs the filter.

    Codex round-14 finding: this still iterated raw `mechanics` -- every
    historical `data_color()`/`heatmap()` call -- instead of `_effective_
    mechanics_units` (the last-effective-entry-per-column collapse
    already applied to `check_color_mechanics`/`check_sequential_vs_
    diverging`/`check_domain_computation`). An override pattern (an
    early, wrong `data_color(palette="Blues", domain=[0,100])` on a
    column corrected by a LATER `data_color(palette="RdYlGn", domain=
    [-50,50])` on the SAME column) had both the overridden and the
    effective entry counted as two DIFFERENT distinct measures (different
    palette/domain), inflating the apparent measure count and comparing
    hue-collision/band-harmonization against a palette that was never
    actually rendered.
    """
    visible = _visible_columns(fp)
    units = _effective_mechanics_units(mechanics, fp)

    def _visible_cols(m: dict) -> tuple:
        return tuple(sorted(set(_mechanics_columns(m, fp)) & visible))

    seen: dict[tuple, dict] = {}
    for m in units:
        cols = _visible_cols(m)
        if not cols:
            continue
        key = (m.get("palette"), m.get("domain"), cols)
        seen.setdefault(key, m)
    return sorted(
        seen.values(),
        key=lambda m: ((m.get("palette") or ""), (m.get("domain") or ""), _visible_cols(m)),
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


def _round_points_covered(covered: int, total: int, possible: int) -> int:
    """Like `_round_points(covered/total, possible)`, but caps the result
    at `possible - 1` whenever coverage is genuinely INCOMPLETE (`covered
    < total`) -- ordinary rounding can otherwise turn a real, required-
    but-missing item into full credit.

    Codex round-13 finding: covering 10 of 11 canonical colored measures
    (`check_colored_measure_selection`) used to compute `round((10/11)*4)
    == 4` -- a perfect score despite one required measure being visibly
    uncolored. This check's own point pool for that call is now 6, not 4
    (its old ceiling-plus-coverage split was removed in favor of scoring
    coverage over the full weight); recomputed at that pool, `round((10/
    11)*6) == 5` -- no longer a perfect score at this specific ratio, but
    the identical overshoot shape (ordinary rounding reaching `possible`
    while `covered < total`) is still confirmed ALREADY LIVE (not just
    theoretical) in this corpus for `check_sequential_vs_diverging`/
    `check_domain_computation` (both now weighted per-column via
    `_effective_mechanics_units`, easily reaching a denominator of 10+
    for a real table) and plausible for `check_fmt_semantic_type` (a
    ground truth with 13 semantic-typed columns already exists in this
    corpus) -- applied consistently across every "N of M required items
    covered" check
    rather than leaving the identical gap in checks that simply hadn't
    hit an unlucky total yet. Coverage that's ACTUALLY complete (`covered
    == total`) still earns the full `possible` points, unaffected -- this
    only ever COSTS a point ordinary rounding would have wrongly
    granted, never adds one.
    """
    if total <= 0:
        return possible
    pts = _round_points(covered / total, possible)
    if covered < total:
        pts = min(pts, possible - 1)
    return pts


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
    # (there are dozens) needs no change -- only the 1 moved check and 5
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
    """Shared body for every judge-backed check (the 1 moved check + 5 new
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
# Data-compliance checks (§8, 53 pts)
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
    instead of that function's own bare-SET fallback, whenever grouping
    ISN'T usable on both sides at once and at least one side's row ids
    contain duplicates.

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

    Codex round-9 finding: round 7's fix only triggered when grouping was
    genuinely ASYMMETRIC (one side grouped, one not) -- but the identical
    duplicate-row-dodging problem exists whenever grouping ISN'T usable
    on BOTH sides, including the plain case where NEITHER side groups at
    all (e.g. `islands_sizes`/`gtcars_hp_price`, which have no `row_count`
    instruction to catch it separately) -- a candidate could simply
    duplicate an existing row and still report a false `exact=True`
    against `execution_tier.row_set_identity`'s bare-set fallback.
    Triggers whenever `use_groups` is False (not just when it's False
    AND grouping is asymmetric) and either side has a genuine duplicate.

    `runner/execution_tier.py` is a hard non-goal for this slice, so this
    wraps it rather than editing it: delegate straight through for every
    case that function already gets right (either side `None`, both-
    grouped, or ungrouped-on-at-least-one-side but with no actual
    duplicate row ids to lose), and only take over the comparison
    directly -- via `Counter` multisets, ignoring group labels on the
    grouped side too when only one side has them to compare against --
    for the case its own set-based fallback mishandles.
    Codex round-12 finding: this only ever took over the comparison for
    `use_groups=False` (asymmetric grouping, or neither side grouped) --
    when BOTH sides are grouped, it always delegated straight to
    `execution_tier.row_set_identity`, which keys by `(group_id, row_id)`
    but STILL as a bare Python `set`, collapsing repeats. A candidate
    that duplicates a row WITHIN one group (two "January" entries in the
    same year, alongside the ground truth's one) has both entries
    collapse to the SAME `(group, row)` set element, silently hiding the
    extra/duplicate row and potentially still reporting a false
    `exact=True`. Generalized to key by `(group_id, row_id)` tuples when
    `use_groups` is True and by bare `row_id` otherwise (unchanged), and
    to check for duplicates -- and take over via multiset comparison --
    under EITHER keying scheme, covering all three grouping
    configurations (asymmetric, both-grouped, both-ungrouped) uniformly.
    """
    if candidate_row_ids is None or truth_row_ids is None:
        return execution_tier.row_set_identity(
            candidate_row_ids, truth_row_ids,
            candidate_group_ids=candidate_group_ids, truth_group_ids=truth_group_ids,
        )
    use_groups = bool(candidate_group_ids) and bool(truth_group_ids)
    if use_groups:
        cand_keys = [
            (execution_tier.normalize_id(g), execution_tier.normalize_id(r))
            for r, g in zip(candidate_row_ids, candidate_group_ids)
        ]
        truth_keys = [
            (execution_tier.normalize_id(g), execution_tier.normalize_id(r))
            for r, g in zip(truth_row_ids, truth_group_ids)
        ]
    else:
        cand_keys = [execution_tier.normalize_id(r) for r in candidate_row_ids]
        truth_keys = [execution_tier.normalize_id(r) for r in truth_row_ids]
    has_duplicates = len(cand_keys) != len(set(cand_keys)) or len(truth_keys) != len(set(truth_keys))
    if not has_duplicates:
        return execution_tier.row_set_identity(
            candidate_row_ids, truth_row_ids,
            candidate_group_ids=candidate_group_ids, truth_group_ids=truth_group_ids,
        )
    cand_counts, truth_counts = Counter(cand_keys), Counter(truth_keys)
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


def _requires_candidate_stub_for_value_matching(cand: dict, truth: dict) -> bool:
    """True if per-entity value-matching CAN'T be honestly trusted here:
    the ground truth supplies real row identity (a stub) but the
    candidate doesn't supply its own.

    Codex round-12 finding: `execution_tier.match_measure_by_value`'s
    underlying `_shared_pairs` (off-limits -- see this file's Tier-1/
    Tier-2 compatibility-shim conventions) falls back to an UNORDERED
    "does the same set of values appear somewhere" comparison whenever
    the CANDIDATE has no stub/row ids at all, collapsing per-entity
    identity entirely (deliberately, for the legitimate case where
    NEITHER side has one). But when the ground truth DOES supply real
    per-entity identity and the candidate omits its own, a candidate
    could scramble which entity gets which value (permute horsepower
    numbers across different cars) and still value-match every measure,
    since the same set of numbers appears SOMEWHERE -- passing per-entity
    "computed correctness" that was never actually verified.
    """
    return bool(truth["tier2"].get("row_ids")) and not cand["tier2"].get("row_ids")


def check_computed_value_correctness(cand: dict, truth: dict, meta: dict) -> CheckResult:
    name = "Computed/derived value correctness"
    measures = list(dict.fromkeys(
        meta["CANONICAL_MEASURES"].get("colored", []) + meta["CANONICAL_MEASURES"].get("hero_uncolored", [])
    ))
    if not measures:
        return _na(name, "ground truth declares no CANONICAL_MEASURES to verify")
    if not cand["tier2"].get("ok"):
        return CheckResult(name, 10, 0, False, f"candidate failed to execute: {cand['tier2'].get('error')}")
    if _requires_candidate_stub_for_value_matching(cand, truth):
        return CheckResult(
            name, 10, 0, False,
            "ground truth has per-entity row identity (a stub) but candidate has none -- "
            "value-matching would only prove the same VALUES appear somewhere, not that they're "
            f"attached to the correct entities; all {len(measures)} canonical measures unverifiable",
        )
    matched, missing = [], []
    for m in measures:
        found = _match_measure_by_value(cand, truth, m)
        (matched if found else missing).append(m)
    pts = _round_points_covered(len(matched), len(measures), 10)
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
    colored". Uses `_column_match_fraction` (round-14 relabeling-aware
    wrapper), not `execution_tier.column_match_fraction` directly -- see
    `_relabeled_candidate_tier2`'s own docstring.
    """
    for col in colored_cols:
        frac = _column_match_fraction(cand_tier2, truth_tier2, col, truth_col)
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
    name = "Colored-measure selection (right measure(s) colored)"
    cand_mechanics = cand["tier1"].get("color_mechanics", [])
    canonical_colored = meta["CANONICAL_MEASURES"].get("colored", [])
    if not canonical_colored:
        # Full marks here are intentional, not an oversight: this check
        # only ever measures COVERAGE of the ground truth's own required
        # canonical colored measures, so when none are required there is
        # nothing left for it to check -- even a candidate that rainbow-
        # colors many unrelated columns for no reason still scores 6/6 on
        # THIS check alone. A sibling judge dimension scoring that kind of
        # purposeless/excessive coloring was proposed and implemented
        # (PR #96, `skill-align/judge-color-restraint-dimension`), but the
        # project owner reversed that direction after two independent
        # reviews found the underlying "bold/text-color as a restraint
        # signal" premise empirically false against this corpus: do not
        # evaluate or teach anything about bolding/text-color as a color-
        # restraint mechanic, in any form. PR #96 was closed unmerged as a
        # result. So excessive coloring on a hypothetical zero-required-
        # color ground truth is, by explicit direction, simply not scored
        # anywhere in this comparator -- an accepted, known limitation, not
        # a gap awaiting a sibling PR. None of the current 6 ground truths
        # have an empty canonical-colored-measures list, so this branch is
        # latent today regardless.
        identity_pts = 6
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
        # Codex round-13 finding: plain `_round_points` let incomplete
        # coverage round UP to full credit (e.g. 10/11 covered rounds to
        # 4/4) -- see `_round_points_covered`'s own docstring.
        identity_pts = _round_points_covered(covered, len(canonical_colored), 6)
        identity_detail = f"{covered}/{len(canonical_colored)} canonical colored measures covered by a candidate color call"
    return CheckResult(name, 6, identity_pts, identity_pts == 6, identity_detail)


def check_sequential_vs_diverging(cand: dict, truth: dict, meta: dict) -> CheckResult:
    name = "Sequential-vs-diverging matches data shape"
    mechanics = cand["tier1"].get("color_mechanics", [])
    if not mechanics:
        if _truth_requires_color(meta):
            return CheckResult(name, 5, 0, False, "ground truth requires colored measure(s) but candidate has none")
        return _na(name, "candidate has no colored measures")
    if not cand["tier2"].get("ok"):
        return CheckResult(name, 5, 0, False, f"candidate failed to execute: {cand['tier2'].get('error')}")
    # Codex round-12 finding: this iterated raw `mechanics` -- every
    # historical `data_color()`/`heatmap()` call -- instead of `_effective_
    # mechanics_units` (the round-8 fix that collapses multiple calls
    # targeting the SAME column down to whichever one is actually
    # EFFECTIVE, last-wins). An early, wrong-shape palette overridden by a
    # later, correct one on the same column still counted as a failure
    # (and vice versa), even though only the later call's palette is what
    # actually renders. Same fix already applied to `reverse`/na_color/
    # truncate/autocolor_text in `check_color_mechanics`.
    units = _effective_mechanics_units(mechanics, cand)
    correct, total, notes = 0, 0, []
    for entry in units:
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
    pts = _round_points_covered(correct, total, 5)
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


_GROUP_LABEL_NUMERIC_RE = re.compile(r"\d+")


def _group_label_similarity(a: Any, b: Any) -> float:
    """A small `[0, 1]` TIE-BREAKING signal between two group identifiers'
    OWN text -- used ONLY to break ties in row-CONTENT overlap (see
    `_hungarian_group_assignment`'s docstring), never to override a real
    content-overlap difference.

    Codex round-10 finding (P1): when every group in a table shares
    identical row-content (e.g. every year-group repeats the same 12
    month stub labels), row content alone carries ZERO information
    distinguishing one truth/candidate group pair from another -- this
    is the signal that lets the assignment still resolve sensibly in
    that case.

    Extracts the first run of digits from each side and compares them as
    text when BOTH have one -- `"2010"` vs `"FY2010"` both extract
    `"2010"`, a full match, regardless of the surrounding non-numeric
    text. This keeps the established "group labels are free-wording,
    only the partition matters" philosophy (round 1's relabeling fix)
    fully intact for the legitimate case. Falls back to a case-
    insensitive substring check when either side has no numeric content
    at all (e.g. purely textual group names). Returns `0.0` -- not a
    guess -- when neither signal distinguishes the pair; the caller's
    own ambiguity detection is what actually decides whether that `0.0`
    represents a real "these clearly don't match" or a "there's no
    information to tell them apart at all" tie.
    """
    sa, sb = str(a), str(b)
    ma, mb = _GROUP_LABEL_NUMERIC_RE.search(sa), _GROUP_LABEL_NUMERIC_RE.search(sb)
    if ma and mb:
        return 1.0 if ma.group() == mb.group() else 0.0
    la, lb = sa.strip().lower(), sb.strip().lower()
    if la and lb and (la in lb or lb in la):
        return 1.0
    return 0.0


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
) -> tuple[list, list, list[list[int]], list[int], bool]:
    """Shared setup for `_group_partition_match`/`_relabel_candidate_groups`:
    sorted truth/candidate group-id lists, their pairwise row-content
    overlap matrix (square, zero-padded to the larger side -- a truth/
    candidate group beyond the other side's actual count is a "dummy"
    with zero overlap, contributing nothing), the Hungarian-optimal
    one-to-one assignment (`assignment[i]` is the column index -- into
    `cand_keys` -- assigned to `truth_keys[i]`; an index `>= len(cand_keys)`
    means that truth group has no real candidate counterpart in the
    optimal assignment), and an `ambiguous` flag (see below).

    Codex round-10 finding (P1): when row CONTENT is fully tied across
    every group pair -- e.g. a table grouped by year where every year's
    group repeats the identical 12 month stub labels, so overlap between
    ANY truth year and ANY candidate year is the same 12 regardless of
    whether the years themselves match -- the overlap matrix alone
    carries ZERO information distinguishing "2010" from "2000". The
    Hungarian algorithm still returns SOME valid one-to-one assignment
    (by construction), but WHICH candidate group lands on which truth
    group is then arbitrary, and a caller that trusts it unconditionally
    (`_relabel_candidate_groups`) can relabel an entirely WRONG set of
    candidate groups onto the truth's correct labels, manufacturing a
    false exact match a downstream check has no real basis for.

    Before falling back to an arbitrary tie, the assignment now ALSO
    weighs `_group_label_similarity` (the group identifiers' OWN text) as
    a strictly SECONDARY signal: `combined = overlap * 1000 +
    similarity`, where 1000 is comfortably larger than any plausible
    total similarity swing (bounded by the group count, which is never
    remotely close to 1000 in real tables) -- so this can only ever break
    a tie in total overlap, never sacrifice real overlap for a better
    label match. This resolves the LEGITIMATE relabeling case ("FY2010"
    vs "2010" -- same numeric content, similarity=1 breaks the tie
    cleanly) without weakening the "group labels are free-wording, only
    the partition matters" philosophy established since round 1.

    `ambiguous` is `True` when another complete one-to-one assignment
    achieves the exact same OPTIMAL TOTAL combined score as the one found
    (see `_assignment_is_ambiguous`'s own docstring for why this is
    checked via global-total pairwise swaps, not a per-row local-tie
    check). Callers use this to avoid confidently claiming an exact/
    one-to-one match that's actually built on an arbitrary pick among
    multiple, equally-good global assignments.
    """
    truth_keys = sorted(truth_groups, key=str)
    cand_keys = sorted(cand_groups, key=str)
    n = max(len(truth_keys), len(cand_keys))
    overlap_matrix = [[0] * n for _ in range(n)]
    combined_matrix = [[0.0] * n for _ in range(n)]
    for i, tg in enumerate(truth_keys):
        for j, cg in enumerate(cand_keys):
            overlap_matrix[i][j] = _group_overlap(truth_groups[tg], cand_groups[cg])
            combined_matrix[i][j] = overlap_matrix[i][j] * 1000 + _group_label_similarity(tg, cg)
    cost = [[-combined_matrix[i][j] for j in range(n)] for i in range(n)]  # minimize cost == maximize combined
    assignment = _hungarian_min_cost(cost)
    ambiguous = _assignment_is_ambiguous(combined_matrix, assignment, len(truth_keys), len(cand_keys))
    return truth_keys, cand_keys, overlap_matrix, assignment, ambiguous


def _assignment_is_ambiguous(
    combined_matrix: list[list[float]], assignment: list[int], n_truth: int, n_cand: int,
) -> bool:
    """True if some ALTERNATE complete one-to-one assignment (over the
    REAL truth/candidate rows -- a truth row mapped to a dummy/padding
    column, `>= n_cand`, is excluded) achieves the exact same OPTIMAL
    TOTAL combined score as `assignment` -- checked via every PAIRWISE
    SWAP of two assigned pairs (swap `(i1, j1)`/`(i2, j2)` to `(i1, j2)`/
    `(i2, j1)` and compare the resulting total).

    Codex round-11 finding: round 10's original `ambiguous` check flagged
    ANY truth row whose own best combined score was tied across 2+
    candidate columns -- a LOCAL, per-row test that doesn't actually mean
    the GLOBAL optimum is non-unique. Concrete counter-example: overlap
    `[[12, 1], [1, 1]]` -- row 1 locally ties between its two columns
    (both score 1), but the global optimum (row0->col0 + row1->col1 = 13)
    strictly beats the only alternative (row0->col1 + row1->col0 = 2), so
    it's NOT actually ambiguous; the old per-row check incorrectly
    flagged it anyway, rejecting a legitimately relabeled candidate.

    A pairwise swap directly answers the right question -- "does an
    alternate COMPLETE assignment tie the total" -- without needing full
    alternate-perfect-matching enumeration (which would require building
    the zero-reduced-cost bipartite subgraph from the Hungarian
    algorithm's own dual potentials and checking it for more than one
    perfect matching -- real complexity this file's scope doesn't need).
    This is a bounded, sufficient approximation: it's guaranteed to catch
    the actual real-world threat this check exists for (a UNIFORMLY tied
    submatrix -- e.g. every year-group sharing identical month content,
    where swapping ANY two groups trivially preserves the total, since
    the whole relevant submatrix is constant) while correctly clearing a
    single locally-tied cell whose surrounding context still pins down a
    unique global optimum, as in the counter-example above. It does not
    attempt to detect ambiguity reachable ONLY via a longer alternating
    cycle (3+ rows) with no tied pairwise swap -- not a shape this
    corpus's group counts (a handful of groups per table) are expected to
    produce, and a full cycle search would be genuine scope creep here.
    """
    assigned_real = [(i, assignment[i]) for i in range(n_truth) if assignment[i] < n_cand]
    if len(assigned_real) < 2:
        return False
    total = sum(combined_matrix[i][j] for i, j in assigned_real)
    for a in range(len(assigned_real)):
        i1, j1 = assigned_real[a]
        for b in range(a + 1, len(assigned_real)):
            i2, j2 = assigned_real[b]
            swapped_total = total - combined_matrix[i1][j1] - combined_matrix[i2][j2] + combined_matrix[i1][j2] + combined_matrix[i2][j1]
            if math.isclose(swapped_total, total, rel_tol=1e-9, abs_tol=1e-9):
                return True
    return False


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
    truth_keys, cand_keys, overlap_matrix, assignment, ambiguous = _hungarian_group_assignment(cand_groups, truth_groups)
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
    # Codex round-10 finding (P1): an assignment built on a GENUINE tie in
    # both row-content overlap AND group-label similarity (see
    # `_hungarian_group_assignment`'s own docstring -- e.g. a candidate
    # using entirely the wrong years, where every year-group shares the
    # same month labels and no candidate year's label numerically matches
    # any truth year's) is arbitrary. Reporting `match=True` off the back
    # of an arbitrary pick would be a confident claim this check has no
    # real basis for -- `ambiguous` makes that genuine uncertainty an
    # explicit non-match instead.
    match = one_to_one and not ambiguous and agree / shared_rows >= execution_tier._MATCH_THRESHOLD
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
    shared row content at all between any candidate/truth group pair, OR
    the assignment is genuinely ambiguous -- see below) -- the caller
    falls back to the candidate's own, unrelabeled group ids in that case.

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

    Codex round-10 finding (P1): when row CONTENT is fully tied across
    every group pair (e.g. every year-group repeats the same 12 month
    stub labels) AND the group identifiers' own text carries no
    distinguishing signal either (e.g. a candidate using entirely the
    wrong years -- no candidate year's label numerically matches any
    truth year's, see `_hungarian_group_assignment`/`_group_label_
    similarity`'s own docstrings), relabeling anyway would arbitrarily
    overwrite the candidate's OWN (and possibly entirely WRONG) group
    labels with the truth's, manufacturing a false partition match
    downstream. Returns `None` in that genuinely ambiguous case too --
    the caller then compares the candidate's own, unrelabeled group ids
    directly, which correctly fails a group-aware row-identity comparison
    instead of silently "succeeding" off an arbitrary relabel.
    """
    cand_groups = _group_row_multisets(candidate_row_ids, candidate_group_ids)
    truth_groups = _group_row_multisets(truth_row_ids, truth_group_ids)
    if not cand_groups or not truth_groups:
        return None
    truth_keys, cand_keys, overlap_matrix, assignment, ambiguous = _hungarian_group_assignment(cand_groups, truth_groups)
    if ambiguous:
        return None
    relabel: dict[Any, Any] = {}
    for i, tg in enumerate(truth_keys):
        j = assignment[i]
        if j < len(cand_keys) and overlap_matrix[i][j] > 0:
            relabel[cand_keys[j]] = tg
    if not relabel:
        return None
    return [relabel.get(gid, gid) for gid in candidate_group_ids]


def _relabeled_candidate_tier2(cand_tier2: dict, truth_tier2: dict) -> dict:
    """A shallow copy of `cand_tier2` with `row_group_ids` relabeled to
    their value-matched TRUTH counterparts (via `_relabel_candidate_
    groups`) -- or `cand_tier2` itself, UNCHANGED, when relabeling isn't
    applicable (either side lacks grouping or row identity) or doesn't
    resolve to anything (`_relabel_candidate_groups` returns `None`, e.g.
    a genuinely ambiguous or unrelated grouping).

    Codex round-14 finding (P1): the group-relabeling machinery
    (`_relabel_candidate_groups`/`_group_partition_match`, built across
    rounds 1/7/10/11 specifically so a wording difference like `FY2010`
    vs `2010` doesn't break matching) was only ever applied by `check_
    row_selection_identity` before calling `_row_multiset_identity` --
    NOT propagated to `execution_tier.match_measure_by_value`/`column_
    match_fraction` (off-limits), which are used PERVASIVELY throughout
    this file (computed-value correctness, colored-measure identity,
    hero-column matching, semantic-type/column-set/summary-column/sort
    resolution by rename, and more) via raw, un-relabeled `(group_id,
    row_id)` key comparison internally. A candidate with a legitimately
    relabeled grouping passed the row-selection check but could fail
    nearly every OTHER value-matched check across the file. This is the
    shared low-level piece `_match_measure_by_value`/`_column_match_
    fraction` (both just below) build on -- callers needing value-based
    matching should go through one of THOSE, not `execution_tier`'s
    functions directly.
    """
    cand_group_ids = cand_tier2.get("row_group_ids")
    truth_group_ids = truth_tier2.get("row_group_ids")
    cand_row_ids = cand_tier2.get("row_ids")
    truth_row_ids = truth_tier2.get("row_ids")
    if not (cand_group_ids and truth_group_ids and cand_row_ids and truth_row_ids):
        return cand_tier2
    relabeled = _relabel_candidate_groups(cand_row_ids, cand_group_ids, truth_row_ids, truth_group_ids)
    if relabeled is None:
        return cand_tier2
    return {**cand_tier2, "row_group_ids": relabeled}


def _match_measure_by_value(cand: dict, truth: dict, truth_col: str) -> str | None:
    """Drop-in, relabeling-aware replacement for `execution_tier.match_
    measure_by_value(cand["tier2"], truth["tier2"], truth_col)` -- every
    check in this file that needs to resolve a ground-truth column to its
    value-matched CANDIDATE column should call this instead of the raw
    `execution_tier` function directly, so a legitimately relabeled
    grouping doesn't break the match. See `_relabeled_candidate_tier2`'s
    own docstring for the full round-14 (P1) story.
    """
    cand_tier2 = _relabeled_candidate_tier2(cand["tier2"], truth["tier2"])
    return execution_tier.match_measure_by_value(cand_tier2, truth["tier2"], truth_col)


def _column_match_fraction(cand_tier2: dict, truth_tier2: dict, cand_col: str, truth_col: str) -> float | None:
    """Drop-in, relabeling-aware replacement for `execution_tier.column_
    match_fraction(cand_tier2, truth_tier2, cand_col, truth_col)` -- for
    callers (like `_any_colored_column_matches`) that already work with
    raw Tier-2 dicts instead of the wrapping fingerprint dicts `_match_
    measure_by_value` takes. See `_relabeled_candidate_tier2`'s own
    docstring for the full round-14 (P1) story.
    """
    relabeled_cand_tier2 = _relabeled_candidate_tier2(cand_tier2, truth_tier2)
    return execution_tier.column_match_fraction(relabeled_cand_tier2, truth_tier2, cand_col, truth_col)


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
                matched_col = _match_measure_by_value(cand, truth, col)
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
    #
    # Codex round-13 finding: `used_cand_cols` started EMPTY, so a
    # candidate column ALREADY correctly satisfying a SAME-NAMED truth
    # column (never entering the rename-search loop below at all, since
    # it's excluded from `truth_cols - cand_cols`) wasn't reserved before
    # rename-resolution ran -- a DIFFERENT, genuinely-missing truth column
    # with the SAME underlying values (e.g. two truth columns that are
    # honest duplicates of each other) could still value-match and
    # "steal" that same candidate column, hiding the real gap. Seeding
    # with the name-matched set (`truth_cols & cand_cols`) up front
    # reserves those first.
    renamed_truth_to_cand: dict[str, str] = {}
    used_cand_cols: set[str] = set(truth_cols & cand_cols)
    if cand["tier2"].get("ok") and truth["tier2"].get("ok"):
        for tc in sorted(truth_cols - cand_cols):
            matched_col = _match_measure_by_value(cand, truth, tc)
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
    # Same distinct-(palette, domain, columns) dedup used to count
    # distinct colored measures elsewhere -- the same conceptual measure
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
                matched_col = _match_measure_by_value(cand, truth, k)
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
# Formatting-compliance checks (§9, 55 pts as of the 2026-08-12 rewrite)
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
    # Codex round-9 finding: `domain=[-1e309, 1e309]` parses to Python
    # floats `-inf`/`inf` (both magnitudes exceed float max ~1.8e308) --
    # `flo < 0 < fhi` and `math.isclose(flo, -fhi, ...)` (which special-
    # cases equal infinities as "close") both pass as if genuinely
    # symmetric, and the coverage check below (`flo <= actual_lo and fhi
    # >= actual_hi`) is trivially satisfied by ANY finite data range too
    # -- but an infinite domain collapses ALL real data to the palette
    # midpoint, defeating the entire point of data-driven coloring. A
    # resolved-but-non-finite literal is a real, provable failure, not
    # benefit-of-the-doubt territory (contrast with the `ValueError`
    # branch above, which is for genuinely UNRESOLVABLE expressions).
    if not (math.isfinite(flo) and math.isfinite(fhi)):
        return False
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
    # Codex round-13 finding: this iterated raw `mechanics` -- every
    # historical `data_color()`/`heatmap()` call -- instead of `_effective_
    # mechanics_units` (the last-effective-entry-per-column collapse
    # already applied to `check_sequential_vs_diverging`/`check_color_
    # mechanics`). An early, WRONG domain overridden by a later, correct
    # one on the same column still counted as a failure (and vice versa),
    # even though only the later call's domain is what actually renders.
    units = _effective_mechanics_units(mechanics, cand)
    correct, total, notes = 0, 0, []
    for i, entry in enumerate(units):
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
            #
            # Codex round-11 finding: that's too broad -- for a SEQUENTIAL
            # (non-diverging) SINGLE column with genuinely varying data,
            # great_tables' auto-inferred domain IS exactly `[min, max]`
            # of that column's own real values: legitimately full-range
            # and data-driven, with no cross-column facet-consistency
            # concern to fail at all (that concern is specifically about
            # a domain meant to be SHARED/comparable across MULTIPLE
            # columns colored together, which auto-inference doesn't
            # guarantee -- it doesn't apply when there's only one column).
            # A diverging shape still needs an explicit domain (auto-
            # inference isn't guaranteed symmetric around zero), a
            # multi-column literal call still needs one too (auto-
            # inference isn't guaranteed consistent across columns), and
            # a CONSTANT single column (`value_range[0] == value_range[1]`
            # -- auto-inference would degenerate to a zero-width domain)
            # still doesn't qualify either.
            cols = _mechanics_columns(entry, cand)
            if shape == "sequential" and len(cols) == 1:
                value_range = _actual_value_range(cand, cols)
                if value_range is not None and value_range[0] < value_range[1]:
                    correct += 1
                    continue
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
                    # Codex round-9 finding: same non-finite-domain gap as
                    # `_domain_element_symmetric`'s diverging branch --
                    # `[-1e309, 1e309]` parses to `-inf`/`inf`, and
                    # `flo < fhi and flo <= actual_lo and fhi >= actual_hi`
                    # is trivially true for ANY finite data range despite
                    # an infinite domain collapsing every real value to
                    # the palette midpoint. Require both endpoints finite
                    # before any other validation runs.
                    if not (math.isfinite(flo) and math.isfinite(fhi)):
                        ok = False
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
    pts = _round_points_covered(correct, total, 8)
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
    # round-4 #10's striping-gate fix): gating purely on the CANDIDATE's
    # own `spanner_present` let a candidate that omits BOTH required
    # spanners AND their dividers
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
    # 2026-08-12 rewrite: every ground truth in this project stripes by
    # DEFAULT now, regardless of row count -- `airquality_monthly_summary`
    # (5 rows) and `towny_growth_trends` (11 of 13 body columns already
    # heatmapped) both stripe anyway, by explicit author direction, which
    # directly contradicted the old "n_rows >= 10 AND body not ~80%
    # color-covered" formula. `islands_sizes` (a single, fully-colored body
    # column) is the one case that doesn't stripe -- not because of row
    # count, but because there's no plain cell left for a stripe to ever
    # show through on. The new rule: expected=True always, UNLESS the
    # visible body is COMPLETELY (100%, not ~80%) covered by color, in
    # which case either choice is acceptable.
    #
    # The old "a bold hero column counts toward fully_filled" branch is
    # gone: the newer universal rule is that a `CANONICAL_MEASURES.
    # hero_uncolored` column is NEVER bold (see `check_hero_not_bold`), so
    # crediting bold text here would now reward exactly the thing the other
    # check penalizes.
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
    # as a "measure" -- counting them in the denominator dilutes a
    # genuinely fully-covered body (e.g. 3 colored columns + 1 stub would
    # read as 3/4 = 0.75, under a naive threshold, even though every real
    # data column IS accounted for).
    tier2 = cand["tier2"]
    visible = _visible_columns(cand) - {tier2.get("stub_column"), tier2.get("group_column")}
    accounted_for: set[str] = set()
    for e in mechanics:
        accounted_for |= set(_mechanics_columns(e, cand))
    fully_colored = bool(visible) and (accounted_for & visible) == visible
    actual = bool(t1.get("striping_present"))
    if fully_colored:
        return CheckResult(
            name, 5, 5, True,
            f"n_rows={n}, body is 100% color-covered -> striping optional (islands_sizes-style case), actual={actual}",
        )
    ok = actual is True
    return CheckResult(name, 5, 5 if ok else 0, ok, f"n_rows={n}, body not fully color-covered -> expected striping=True, actual={actual}")


_SEQ_PALETTE_TO_DA_FAMILY = {"blues": "navy", "greens": "forest", "reds": "oxblood", "oranges": "oxblood"}


def check_band_hue_harmonization(cand: dict, truth: dict, meta: dict) -> CheckResult:
    # 2026-08-12 rewrite: this used to expect a LIGHT accent_tint band
    # whenever any measure was colored, and a hue matching that measure's
    # own palette family -- reserving a solid, branded "dark" band for a
    # pure-categorical table with no heatmap at all. That's now backwards:
    # every one of the 6 ground truths uses the SAME deep navy (#08306B),
    # bold, white-text header, regardless of whether (or what) the body
    # heatmaps -- gtcars_top10_by_country's Blues heatmap, airquality's
    # Reds+Blues pair, and sp500's RdYlGn/Greens/Reds trio all get the
    # identical navy header. The header is now a fixed branding surface,
    # decoupled from each table's own measure hue -- see `check_header_
    # branding` below, which replaces the old hue-harmonization logic
    # entirely with a flat, universal hex/weight/text-color check.
    name = "Heading band hue harmonization"
    return _na(name, "superseded by check_header_branding (2026-08-12 -- header is now a fixed universal navy, not hue-matched per table)")


_HEADER_BRANDING_HEX = "#08306B"


def check_header_branding(cand: dict, truth: dict, meta: dict) -> CheckResult:
    """Header/stub branding: deep navy, bold, white text -- a fixed,
    table-independent rule now (see the module note on the retired
    `check_band_hue_harmonization` just above), not something derived from
    which measure the table happens to color. All 6 ground truths agree
    on the exact same hex for both the header background and the stub
    tint; this check reads that literal value directly rather than
    deriving an "expected" one per table.
    """
    name = "Header branding (deep navy, bold, white text)"
    t1 = cand["tier1"]
    hex_ok = _normalize_css_color(t1.get("heading_band_hex")) == _HEADER_BRANDING_HEX
    weight_ok = (t1.get("column_labels_font_weight") or "").lower() == "bold"
    text_color_ok = _normalize_css_color(t1.get("column_labels_text_color")) == _normalize_css_color("white")
    pts = (2 if hex_ok else 0) + (1 if weight_ok else 0) + (2 if text_color_ok else 0)
    detail = (
        f"header background: expected {_HEADER_BRANDING_HEX}, got {t1.get('heading_band_hex')!r} "
        f"({'OK' if hex_ok else 'MISMATCH'}); "
        f"column_labels_font_weight: expected bold, got {t1.get('column_labels_font_weight')!r} "
        f"({'OK' if weight_ok else 'MISMATCH'}); "
        f"column-label text color: expected white, got {t1.get('column_labels_text_color')!r} "
        f"({'OK' if text_color_ok else 'MISMATCH'})"
    )
    return CheckResult(name, 5, pts, pts == 5, detail)


def check_stub_tint(cand: dict, truth: dict, meta: dict) -> CheckResult:
    """Stub tint: washed navy (#EAF0F6), whenever a stub exists -- fixed,
    universal, same reasoning as `check_header_branding`."""
    name = "Stub tint (washed navy)"
    t1 = cand["tier1"]
    if not t1.get("stub_present"):
        return _na(name, "candidate has no stub")
    ok = _normalize_css_color(t1.get("stub_fill_hex")) == "#EAF0F6"
    return CheckResult(name, 2, 2 if ok else 0, ok, f"expected #EAF0F6, got {t1.get('stub_fill_hex')!r}")


def check_stripe_color(cand: dict, truth: dict, meta: dict) -> CheckResult:
    """Row-stripe color: flat neutral grey (#F6F6F6), whenever striping is
    present -- fixed, universal, same reasoning as `check_header_
    branding`. N/A when the candidate doesn't stripe at all (that absence
    is `check_striping_gate`'s job to penalize, not this check's)."""
    name = "Stripe color (neutral grey)"
    t1 = cand["tier1"]
    if not t1.get("striping_present"):
        return _na(name, "candidate has no row striping")
    ok = _normalize_css_color(t1.get("stripe_hex")) == "#F6F6F6"
    return CheckResult(name, 2, 2 if ok else 0, ok, f"expected #F6F6F6, got {t1.get('stripe_hex')!r}")


def check_hero_not_bold(cand: dict, truth: dict, meta: dict) -> CheckResult:
    """A `CANONICAL_MEASURES.hero_uncolored` measure is never bold -- every
    current ground truth with one (gtcars_hp_price's horsepower,
    airquality's wind speed, towny's rank/total growth, sp500's
    open/close) renders it as plain text, explicitly by author direction
    (each ground truth's own docstring says so). Bolding a hero measure
    used to be credited as an alternative to a 3rd color fill
    (`check_striping_gate`'s old "fully filled" exemption); that credit is
    gone now that plain-text heroes are the universal rule, so this check
    makes the rule itself count, positively, instead.
    """
    name = "Hero-uncolored measures stay plain (not bold)"
    hero_measures = meta["CANONICAL_MEASURES"].get("hero_uncolored", [])
    if not hero_measures:
        return _na(name, "ground truth declares no hero_uncolored measures")
    if not cand["tier2"].get("ok") or not truth["tier2"].get("ok"):
        return CheckResult(name, 2, 0, False, f"candidate failed to execute: {cand['tier2'].get('error')}")
    bold_cols = set(cand["tier1"].get("bold_columns") or [])
    total, ok_count, bolded = 0, 0, []
    for hm in hero_measures:
        matched_col = _match_measure_by_value(cand, truth, hm)
        if matched_col is None:
            continue
        total += 1
        if matched_col in bold_cols:
            bolded.append(matched_col)
        else:
            ok_count += 1
    if total == 0:
        return _na(name, "no hero_uncolored measure value-matched a candidate column")
    pts = _round_points_covered(ok_count, total, 2)
    detail = f"{ok_count}/{total} hero-uncolored measures are plain text"
    if bolded:
        detail += f"; incorrectly bolded: {bolded}"
    return CheckResult(name, 2, pts, ok_count == total, detail)


def check_force_sign(cand: dict, truth: dict, meta: dict) -> CheckResult:
    """A percent-semantic column whose TRUTH data genuinely crosses zero
    (a real gain-or-loss measure -- pct_change, growth %, best/worst day)
    uses `force_sign=True`, in every current ground truth, so a reader can
    tell +3.8% from -3.8% at a glance. An always-positive percent has no
    real "sign" to force, so this only applies where the truth's own data
    is signed -- not to every percent column unconditionally.
    """
    name = "Signed-percent force_sign correctness"
    semantic_types = meta["SEMANTIC_TYPES"]
    percent_cols = [c for c, t in semantic_types.items() if t == "percent"]
    if not percent_cols:
        return _na(name, "ground truth declares no percent-semantic columns")
    if not cand["tier2"].get("ok") or not truth["tier2"].get("ok"):
        return CheckResult(name, 2, 0, False, f"candidate failed to execute: {cand['tier2'].get('error')}")
    force_sign_map = cand["tier1"].get("fmt_percent_force_sign_map", {})
    total, ok_count, uncovered = 0, 0, []
    for c in percent_cols:
        if _measure_signedness(truth, [c]) != "diverging":
            continue
        matched_col = _match_measure_by_value(cand, truth, c)
        if matched_col is None:
            total += 1
            uncovered.append(c)
            continue
        val = force_sign_map.get(matched_col, force_sign_map.get(convergence._ALL_COLUMNS))
        if val is _UNRESOLVED_FORCE_SIGN:
            continue
        total += 1
        if val == "True":
            ok_count += 1
        else:
            uncovered.append(c)
    if total == 0:
        return _na(name, "no signed (crosses-zero) percent-semantic column to check")
    pts = _round_points_covered(ok_count, total, 2)
    detail = f"{ok_count}/{total} signed percent columns use force_sign=True"
    if uncovered:
        detail += f"; missing/wrong on: {uncovered}"
    return CheckResult(name, 2, pts, ok_count == total, detail)


def check_caption_keywords(cand: dict, truth: dict, meta: dict) -> CheckResult:
    """`CAPTION_KEYWORDS` mechanical substring check, revived 2026-08-12
    now that ground-truth captions are a single short sentence each (a
    long, multi-sentence caption made a keyword-presence check either
    trivially satisfiable or unfairly brittle; a one-sentence caption
    makes it a real, cheap signal). `caption_should_mention`: every
    keyword must appear (case-insensitive substring) somewhere across the
    candidate's own source-note text. `subtitle_should_not_duplicate`:
    none of those keywords may appear in the candidate's subtitle -- the
    insight belongs to the caption, not a restated subtitle.
    """
    name = "Caption keyword coverage"
    kw = meta.get("CAPTION_KEYWORDS") or {}
    should_mention = kw.get("caption_should_mention") or []
    should_not_duplicate = kw.get("subtitle_should_not_duplicate") or []
    if not should_mention and not should_not_duplicate:
        return _na(name, "ground truth declares no CAPTION_KEYWORDS")
    # Pure source-text extraction (title/subtitle/source_note are literal
    # strings, independent of whether the script's DATA execution
    # succeeds) -- not gated on tier2.ok, unlike the value-based checks.
    caption_text = " ".join(cand["tier1"].get("source_note_texts") or []).lower()
    subtitle_text = (cand["tier1"].get("subtitle_text") or "").lower()
    total = len(should_mention) + len(should_not_duplicate)
    ok_count = 0
    missing = [k for k in should_mention if k.lower() not in caption_text]
    ok_count += len(should_mention) - len(missing)
    leaked = [k for k in should_not_duplicate if k.lower() in subtitle_text]
    ok_count += len(should_not_duplicate) - len(leaked)
    pts = _round_points_covered(ok_count, total, 3) if total else 3
    detail = f"{ok_count}/{total} caption-keyword rules satisfied"
    if missing:
        detail += f"; caption missing: {missing}"
    if leaked:
        detail += f"; subtitle wrongly duplicates: {leaked}"
    return CheckResult(name, 3, pts, ok_count == total, detail)


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
    one measure) let a candidate
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
            matched_col = _match_measure_by_value(cand, truth, m)
            if matched_col is None:
                continue
            cand_entry = _mechanics_entry_for_column(mechanics, cand, matched_col)
            if cand_entry is None:
                continue
            reverse_total += 1
            if cand_entry.get("reverse") == truth_entry.get("reverse"):
                reverse_ok += 1
    # Codex round-10 finding: pooling `reverse` into the SAME averaged
    # fraction as na_color/truncate/autocolor_text let a single wrong
    # reverse value get diluted away by rounding once there were enough
    # OTHER (correct) sub-checks in the pool -- Codex's concrete example
    # on towny_growth_trends: 39/44 correct sub-checks (with a genuine
    # reverse-orientation mismatch among them) still rounds to a full
    # 4/4, fully erasing a provable polarity error that should never wash
    # out. `reverse` is now its own SEPARATE, independently-rounded
    # 1-point component (whenever there's a real reverse check to make),
    # not folded into the base na_color/truncate/autocolor_text pool --
    # a mismatch there always costs a visible amount of this check's
    # total, regardless of how many OTHER properties happen to be
    # correct. This deliberately does NOT make the whole check binary-
    # fail on a reverse mismatch (too harsh -- reverse is only checked
    # for canonical measures with a declared truth mechanics entry, so
    # it's often not applicable at all): when there's nothing to check
    # (`reverse_total == 0`), the full 4 points stay with the base pool
    # exactly as before this fix.
    base_total = 3 * n
    base_ok = na_ok + trunc_ok + autocolor_ok
    if reverse_total:
        base_pts = _round_points(base_ok / base_total, 3) if base_total else 3
        # Codex round-14 finding: plain `_round_points` still rounded a
        # real reverse mismatch away when only a minority of checked
        # measures were wrong (`round(4/5) == 1` -- full credit for this
        # 1-point component despite one visibly-reversed measure).
        # `_round_points_covered` (round 13) caps incomplete coverage
        # below full credit -- reused here for the same reason it was
        # built for the other "N of M covered" checks.
        reverse_pts = _round_points_covered(reverse_ok, reverse_total, 1)
        pts = base_pts + reverse_pts
    else:
        pts = _round_points(base_ok / base_total, 4) if base_total else 4
    return CheckResult(
        name, 4, pts, pts == 4,
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
    scale_map = cand["tier1"].get("fmt_percent_scale_values_map", {})
    decimals_map = cand["tier1"].get("fmt_number_decimals_map", {})
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
                matched_col = _match_measure_by_value(cand, truth, c)
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
                #
                # Codex round-11 finding: also validate a "percent"
                # aggregate's `scale_values` against this single summary
                # value's own scale -- see `_fmt_covers_semantic_type`'s
                # docstring.
                #
                # Codex round-14 finding: also validate an "integer"
                # aggregate's `fmt_number(decimals=...)` actually renders
                # a clean whole number -- see `_fmt_number_decimals_map`'s
                # docstring.
                if _fmt_covers_semantic_type(
                    semantic_type, effective_fmt, all_integral=_is_integral_value(cand_values.get(matched_col)),
                    scale_shape=_value_scale_shape(cand_values.get(matched_col)),
                    scale_values=scale_map.get(matched_col, scale_map.get(convergence._ALL_COLUMNS)),
                    decimals=decimals_map.get(matched_col, decimals_map.get(convergence._ALL_COLUMNS)),
                ):
                    covered_pairs += 1
            else:
                covered_pairs += 1
    if required_pairs == 0:
        return _na(name, "grand-summary row(s) have no numeric values to check")
    pts = _round_points_covered(covered_pairs, required_pairs, 4)
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


def _fmt_covers_semantic_type(
    sem_type: str,
    effective_fmt: Any,
    *,
    all_integral: bool,
    scale_shape: str | None = None,
    scale_values: object = None,
    decimals: object = None,
) -> bool:
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

    Codex round-11 finding: for `"percent"`, only the METHOD NAME
    (`fmt_percent`) was ever checked -- but `fmt_percent`'s `scale_values`
    kwarg controls whether great_tables multiplies the raw value by 100
    before appending "%" (`scale_values=True`, its own default -- correct
    for genuinely FRACTIONAL data, e.g. `0.05` meaning 5%) or renders it
    AS-IS (`scale_values=False` -- correct only when the value ALREADY IS
    the percentage number, e.g. `5` meaning 5%). Getting this backwards
    is a real, meaningful data-fidelity bug (values render 100x too small
    or too large), not a cosmetic one. `scale_shape` (see `_scale_shape_
    from_values`/`_values_scale_shape`/`_value_scale_shape`) classifies
    the matched column/value's ACTUAL numeric shape; `scale_values` is
    the resolved literal `scale_values=` text from `_fmt_percent_scale_
    values_map` (`None` when NO overlapping `fmt_percent(...)` call ever
    touched this column at all, which really does resolve to great_
    tables' own `True` default with total confidence; `_UNRESOLVED_
    SCALE_VALUES` when a call DID target it but the argument itself is
    unresolvable). This only ever COSTS credit when both signals are
    confidently known and they actively DISAGREE -- an ambiguous data
    shape keeps the benefit of the doubt, same as everywhere else in this
    file.

    Codex round-12 finding: `None` (never touched) and `_UNRESOLVED_
    SCALE_VALUES` (touched, but unresolvable) both used to default to
    `"True"` here -- correct benefit-of-the-doubt for the former (it's
    genuinely, confidently `True`), but an active WRONG-answer assumption
    for the latter whenever `scale_shape == "percentage_scale"` (where
    the correct choice is `False`): an unresolvable expression could
    resolve to either value at runtime, so defaulting it to `"True"`
    actively penalized a candidate whose real (unknowable-from-source)
    value might well have been the correct `False`. The sentinel now
    skips this validation ENTIRELY rather than guessing.

    Codex round-14 finding: `_SEMANTIC_TO_FMT["integer"]` accepts
    `fmt_number` as well as `fmt_integer` -- reasonable IF `fmt_number`
    is actually configured to render a clean whole number, but great_
    tables' own `fmt_number` defaults `decimals=2` (verified against the
    installed `great_tables` signature), NOT `0` -- so `.fmt_number(
    columns="hp", decimals=2)` (or simply omitting `decimals=` entirely)
    renders `"200.00"` for what should be a clean integer count, yet
    still earned full credit purely from the method name. `decimals` is
    the resolved literal `decimals=` text from `_fmt_number_decimals_map`
    (`None` when no overlapping `fmt_number(...)` call ever touched this
    column, which really does resolve to great_tables' own `2` default
    with total confidence; `_UNRESOLVED_FMT_NUMBER_DECIMALS` when a call
    DID target it but the argument itself is unresolvable, e.g. a
    variable -- kept as benefit-of-the-doubt, same reasoning as `scale_
    values`' identical sentinel just above).
    """
    if effective_fmt not in _SEMANTIC_TO_FMT.get(sem_type, set()):
        return False
    if sem_type == "number" and effective_fmt == "fmt_integer" and not all_integral:
        return False
    if sem_type == "percent" and effective_fmt == "fmt_percent" and scale_values is not _UNRESOLVED_SCALE_VALUES:
        effective_scale_values = scale_values if scale_values is not None else "True"
        if scale_shape == "fractional" and effective_scale_values == "False":
            return False
        if scale_shape == "percentage_scale" and effective_scale_values == "True":
            return False
    if sem_type == "integer" and effective_fmt == "fmt_number" and decimals is not _UNRESOLVED_FMT_NUMBER_DECIMALS:
        effective_decimals = decimals if decimals is not None else "2"
        if effective_decimals != "0":
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
    # selection` already uses elsewhere in this file, rather than assuming
    # the candidate preserved the name.
    #
    # Round-5 proactive sweep finding (same "expected/applicable gated on
    # the CANDIDATE's own state" shape as check_frame_
    # hairlines_dividers's round-5 fix): the denominator here was every
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
    scale_map = cand["tier1"].get("fmt_percent_scale_values_map", {})
    decimals_map = cand["tier1"].get("fmt_number_decimals_map", {})
    ok_count = 0
    uncovered: list[str] = []
    for c, sem_type in semantic_types.items():
        matched_col = _match_measure_by_value(cand, truth, c)
        effective_fmt = fmt_map.get(matched_col, fmt_map.get(convergence._ALL_COLUMNS)) if matched_col else None
        if (
            matched_col is not None
            and matched_col in visible
            and _fmt_covers_semantic_type(
                sem_type, effective_fmt, all_integral=_column_values_are_integral(cand["tier2"], matched_col),
                scale_shape=_values_scale_shape(cand["tier2"], matched_col),
                scale_values=scale_map.get(matched_col, scale_map.get(convergence._ALL_COLUMNS)),
                decimals=decimals_map.get(matched_col, decimals_map.get(convergence._ALL_COLUMNS)),
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
    return CheckResult(name, 4, _round_points_covered(ok_count, total, 4), all_ok, detail)


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
        # Codex round-10 finding: this used to silently substitute the
        # DEFAULT value (5.0) for a non-literal `expand` (e.g. `expand=
        # EXPAND`, a variable) -- treating an unresolvable expression as
        # if it resolved to the exact default is wrong in BOTH
        # directions (a candidate that raised expand via a variable
        # scored as if it hadn't; one that lowered it scored as if it
        # hadn't either), and inconsistent with `zoom`'s own handling
        # just above, which correctly returns N/A for the identical
        # non-literal case. Mirrors that treatment exactly.
        return _na(name, f"non-literal expand value '{params.get('expand')}' -- not verifiable")
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

    Codex round-12 finding (comprehensive sweep): call sites were located
    via `convergence._call_arg_blocks` (a source-wide regex with no
    comment/string stripping) -- the same recurring bug class already
    fixed elsewhere in this file. Switched to `_ast_call_arg_blocks`
    (AST-based).
    """
    for block in _ast_call_arg_blocks(source, "tab_style"):
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


def check_title_quality(cand: dict, truth: dict, meta: dict) -> CheckResult:
    # New per .planning/10-hybrid-comparator.md §3: grades whether the
    # title is clear, accurate, and matches the ground truth's core
    # framing -- a wording judgment, not a fact.
    return _judge_dimension_check(meta, "title_quality", "Title quality", 3)


def check_column_order_quality(cand: dict, truth: dict, meta: dict) -> CheckResult:
    # New: `09` explicitly left column order ungraded ("Doesn't grade...
    # column order", `09` §3) since a sensible left-to-right reading order
    # is one of several valid choices, not a single fixed answer.
    return _judge_dimension_check(meta, "column_order_quality", "Column order quality", 2)


FORMAT_CHECKS: list[CheckFn] = [
    check_domain_computation,
    check_frame_hairlines_dividers,
    check_striping_gate,
    check_band_hue_harmonization,  # retired 2026-08-12 -- always N/A now, see check_header_branding
    check_header_branding,
    check_stub_tint,
    check_stripe_color,
    check_hero_not_bold,
    check_force_sign,
    check_caption_keywords,
    check_color_mechanics,
    check_summary_row_formatting,
    check_fmt_semantic_type,
    check_render_mechanics,
    check_summary_row_visual_distinction,
    check_title_quality,
    check_column_order_quality,
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
    4 dimensions together"), and its single combined result is stashed in
    ``meta["_judge_result"]`` before any check function runs, so every
    judge-backed check (see ``_judge_dimension_check``) reads from the same
    call rather than each triggering its own.

    The ground-truth PNG is derived by the convention this repo already
    uses elsewhere: its `.py` has a checked-in `.png` twin alongside it,
    same stem. The CANDIDATE PNG is NOT derived that way -- it's always
    the harness's own mandated artifact filename, `table.png`, sitting
    next to the candidate script, regardless of what the candidate script
    itself happens to be named.

    Codex round-11 finding: this used to derive `candidate_png` via
    `candidate_path.with_suffix(".png")` -- the candidate SCRIPT's own
    filename stem -- so a candidate invoked as `/tmp/submission.py` that
    correctly writes `/tmp/table.png` (exactly as required) had the judge
    looking for `/tmp/submission.png` instead: either degrading all 4
    judge-backed checks to unavailable for a perfectly correct candidate,
    or worse, silently judging a stale, unrelated PNG that happened to
    already exist at that wrong path. `candidate_path.parent /
    "table.png"` matches the actual mandated-artifact contract (see
    `check_render_mechanics`/`_targets_table_png`, which already enforce
    this same "must be named table.png" requirement mechanically)
    instead of assuming a same-stem naming convention that was never
    actually part of the contract for candidates.

    If either PNG doesn't exist, or the model call itself fails,
    ``judge()`` degrades to its own "unavailable" result (see that
    function's docstring) -- this never raises and never blocks the
    deterministic checks from running.
    """
    cand = build_fingerprint(candidate_path)
    truth = build_fingerprint(ground_truth_path)
    meta = load_ground_truth_metadata(ground_truth_path)

    candidate_png = candidate_path.parent / "table.png"
    truth_png = ground_truth_path.with_suffix(".png")
    # Codex round-5 finding: gate the judge call on the candidate's OWN
    # Tier-2 execution having actually succeeded, as a HARD precondition --
    # more fundamental than the mtime staleness check below. Whatever PNG
    # happens to sit next to a candidate `.py` that fails to even EXECUTE
    # cannot be trusted to reflect that source at all (it could be
    # leftover from any prior, unrelated version), regardless of how
    # recently it was written. This is checked BEFORE the mtime check on
    # purpose: a fresh-looking PNG next to a currently-broken script is
    # just as untrustworthy as a stale one.
    #
    # Codex round-11 finding: this whole execution/freshness gate was only
    # ever applied to the CANDIDATE side -- but a ground truth's `.py` can
    # ALSO change without its checked-in `.png` being regenerated (or, in
    # principle, fail to execute), in which case the deterministic checks
    # already reflect the UPDATED truth source while a stale/untrustworthy
    # truth PNG would still get sent to the judge. Mirrors the identical
    # two-step gate (execution first, then mtime staleness) on `truth`/
    # `truth_png` too.
    if not cand["tier2"].get("ok"):
        judge_unavailable_reason = f"judge unavailable: candidate failed Tier-2 execution ({cand['tier2'].get('error')}); its PNG (if any) can't be trusted to reflect this source"
    elif not truth["tier2"].get("ok"):
        judge_unavailable_reason = f"judge unavailable: ground truth failed Tier-2 execution ({truth['tier2'].get('error')}); its PNG (if any) can't be trusted to reflect this source"
    elif _judge_png_is_stale(candidate_png, candidate_path):
        # Codex round-4 finding: see `_judge_png_is_stale`'s docstring --
        # degrade exactly like `judge()`'s own documented "unavailable"
        # contract (all 4 keys, applicable=False, rationale prefixed with
        # the literal "judge unavailable: " string) rather than scoring a
        # PNG that predates the source it's supposed to represent.
        judge_unavailable_reason = f"judge unavailable: candidate PNG is older than its source .py ({candidate_png} predates {candidate_path})"
    elif _judge_png_is_stale(truth_png, ground_truth_path):
        judge_unavailable_reason = f"judge unavailable: ground-truth PNG is older than its source .py ({truth_png} predates {ground_truth_path})"
    else:
        judge_unavailable_reason = None

    if judge_unavailable_reason is not None:
        meta["_judge_result"] = {
            key: judge_module.JudgeDimension(applicable=False, score=None, rationale=judge_unavailable_reason)
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
