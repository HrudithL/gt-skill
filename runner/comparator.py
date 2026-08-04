#!/usr/bin/env python3
"""The ground-truth comparator — scores a candidate `table.py` against its
prompt's ground truth, deterministically.

Per ``.planning/09-ground-truth-comparator.md``: no LLM anywhere in this
path. Every check is regex/AST parsing (Tier 1, ``runner.convergence``),
execution + value comparison (Tier 2, ``runner.execution_tier``), or a
lookup against the ground truth's own authored metadata (§5). Outcome-only
scoring — a check never penalizes *how* a table reached a compliant result,
only whether the result itself is compliant.

Report shape: a 0–100 total = Data-compliance (0–50) + Formatting-compliance
(0–50), plus one line per check naming what passed/failed, its point value,
and why (§7).
"""

from __future__ import annotations

import ast
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from runner import convergence, execution_tier

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


def build_fingerprint(py_path: Path) -> dict:
    """Tier 1 + Tier 2 fingerprint for one `table.py` (candidate OR ground
    truth — both are built identically, per the spec's "computed the same
    way" instruction).
    """
    source = py_path.read_text()
    tier1 = convergence.parse_design_choices(source)
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
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in _METADATA_DEFAULTS:
                try:
                    found[target.id] = ast.literal_eval(node.value)
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


_DIVERGING_PALETTES = {"rdylgn", "rdbu", "puor"}
_SEQUENTIAL_PALETTES = {"blues", "greens", "reds", "oranges"}


def _palette_kind(palette: str | None) -> str:
    """"diverging"/"sequential" for a RECOGNIZED palette name, else
    "unknown" -- never assumed sequential by default.

    A custom diverging palette expressed as a literal hex-list (e.g. the
    repo's own `corpus/heatmap/good_table.py` red-white-green gradient) is
    not a bare palette NAME at all, so it can't match either known set --
    treating that as "unknown" (which `check_sequential_vs_diverging`
    already gives the benefit of the doubt) rather than defaulting it to
    "sequential" avoids penalizing a genuinely diverging custom palette for
    not being one of the ~7 names this function actually recognizes.
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


CheckFn = Callable[[dict, dict, dict], CheckResult]


def _na(name: str, detail: str) -> CheckResult:
    """A check with nothing to grade this run (e.g. an optional
    REQUIRED_INSTRUCTIONS key the prompt never asked for) — contributes 0 to
    BOTH earned and possible, so the report's denominator shrinks instead of
    silently awarding or docking points for something that was never asked.
    """
    return CheckResult(name, 0, 0, True, detail)


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
        return _na(name, "candidate has no colored measures")
    if not cand["tier2"].get("ok"):
        return CheckResult(name, 5, 0, False, f"candidate failed to execute: {cand['tier2'].get('error')}")
    correct, total, notes = 0, 0, []
    for entry in mechanics:
        shape = _measure_signedness(cand, _mechanics_columns(entry, cand))
        if shape is None:
            continue
        total += 1
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
                result = execution_tier.group_partition_match(
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
    collision = palettes[0] is not None and palettes[0] == palettes[1]
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
    name = "Column-label concept-correctness"
    synonyms = meta["LABEL_SYNONYMS"]
    if not synonyms:
        return _na(name, "ground truth declares no LABEL_SYNONYMS to check")
    cand_labels = _parse_columns_signature_labels(cand["tier1"].get("columns_signature", ""))
    applicable = {col: syns for col, syns in synonyms.items() if col in cand_labels}
    if not applicable:
        return _na(name, "none of the candidate's rendered columns are covered by LABEL_SYNONYMS")
    ok_count = 0
    for col, syns in applicable.items():
        label = cand_labels[col].lower()
        if any(s.lower() in label for s in syns):
            ok_count += 1
    all_ok = ok_count == len(applicable)
    return CheckResult(name, 1, 1 if all_ok else 0, all_ok, f"{ok_count}/{len(applicable)} rendered labels match an acceptable synonym")


DATA_CHECKS: list[CheckFn] = [
    check_row_selection_identity,
    check_computed_value_correctness,
    check_colored_measure_selection,
    check_sequential_vs_diverging,
    check_explicit_instructions,
    check_column_set,
    check_grouping_existence,
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
                # heatmap()'s auto-derived domain is always shape-correct
                # by construction (it computes symmetric-for-diverging /
                # full-range-for-sequential from the real data itself).
                correct += 1
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
        return _na(name, "candidate failed to execute; row count unknown")
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


def check_color_mechanics(cand: dict, truth: dict, meta: dict) -> CheckResult:
    name = "Color mechanics (na_color, truncate, autocolor_text)"
    mechanics = cand["tier1"].get("color_mechanics", [])
    if not mechanics:
        return _na(name, "candidate has no colored measures")
    n = len(mechanics)
    na_ok = sum(1 for e in mechanics if e.get("na_color") == "#808080")
    trunc_ok = sum(1 for e in mechanics if e.get("truncate") == "False")
    autocolor_ok = sum(1 for e in mechanics if e.get("autocolor_text") == "True")
    # A single rounding over all 3*n sub-checks (rather than one
    # _round_points() call per dimension) so a fully-correct candidate
    # always sums to exactly 4, and "autocolor_text=False" (readable text
    # isn't guaranteed over a dark fill) actually costs points -- the name
    # already promised this field was checked; it wasn't.
    total_checks = 3 * n
    total_ok = na_ok + trunc_ok + autocolor_ok
    pts = _round_points(total_ok / total_checks, 4)
    return CheckResult(
        name, 4, pts, total_ok == total_checks,
        f"na_color correct {na_ok}/{n}, truncate=False correct {trunc_ok}/{n}, autocolor_text=True correct {autocolor_ok}/{n}",
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
    numeric_cols = [
        k for k, v in cand_summary[0].get("values", {}).items()
        if isinstance(v, (int, float))
    ]
    if not numeric_cols:
        return _na(name, "grand-summary row has no numeric values to check")
    covered = [c for c in numeric_cols if c in fmt_map]
    pts = _round_points(len(covered) / len(numeric_cols), 4)
    detail = (
        f"{len(covered)}/{len(numeric_cols)} numeric summary columns are covered by a fmt_* call "
        "(great_tables does not auto-apply body formatting to grand_summary_rows -- Defect C)"
    )
    return CheckResult(name, 4, pts, len(covered) == len(numeric_cols), detail)


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
        if fmt_map.get(c) in _SEMANTIC_TO_FMT.get(t, set())
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
    notes = cand["tier1"].get("source_note_texts") or []
    caption_present = len(notes) >= 1 and bool(notes[0])
    source_expected = bool(truth["tier1"].get("source_note_texts")) and len(truth["tier1"]["source_note_texts"]) >= 2
    source_present = len(notes) >= 2 and bool(notes[1])
    footer_ok = (caption_present == caption_expected) and (source_present == source_expected or not source_expected)
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
            if unquoted_color and unquoted_color.strip().lower() in ("transparent", "none", ""):
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
    name = "Caption doesn't just restate the subtitle"
    keywords = meta["CAPTION_KEYWORDS"]
    if not keywords:
        return _na(name, "ground truth declares no CAPTION_KEYWORDS to check")
    n = _n_rows(cand)
    if n is not None and n < 5:
        return _na(name, "fewer than 5 rows; caption is optional")
    notes = cand["tier1"].get("source_note_texts") or []
    caption = (notes[0] or "").lower() if notes else ""
    subtitle = (cand["tier1"].get("subtitle_text") or "").lower()
    should_mention = keywords.get("caption_should_mention", [])
    should_not_duplicate = keywords.get("subtitle_should_not_duplicate", [])
    # ALL declared keywords, not just one -- the §5 schema calls these the
    # terms "the footer's takeaway sentence must include" (plural), and
    # towny's own ground truth treats its 3 keywords as jointly making up
    # "the actual unique insight", not alternatives. A caption mentioning
    # only 1 of 3 required concepts (e.g. just "1996") was previously
    # awarded full credit here.
    mentions_ok = not should_mention or all(k.lower() in caption for k in should_mention)
    no_duplicate = not any(k.lower() in subtitle for k in should_not_duplicate)
    ok = mentions_ok and no_duplicate
    return CheckResult(name, 1, 1 if ok else 0, ok, f"caption mentions required keyword={mentions_ok}, subtitle avoids caption-only keywords={no_duplicate}")


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


def compare(candidate_path: Path, ground_truth_path: Path) -> ComparatorReport:
    """Run every check and roll up the score. Never raises on a candidate
    that fails to execute or parse — every check function is written to
    degrade to a 0-point failure (or an N/A skip) rather than crash, so a
    broken candidate still gets a full, itemized report.
    """
    cand = build_fingerprint(candidate_path)
    truth = build_fingerprint(ground_truth_path)
    meta = load_ground_truth_metadata(ground_truth_path)

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
        mark = "PASS" if r.passed else "FAIL"
        lines.append(f"[{mark}] {r.name}: {r.points_earned}/{r.points_possible} -- {r.detail}")
    return "\n".join(lines)
