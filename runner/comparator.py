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

import importlib.util
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
    """Import a ground-truth module and read its §5 metadata literals.

    Missing names default per `_METADATA_DEFAULTS` — a ground truth that
    doesn't need `REQUIRED_INSTRUCTIONS` (say) simply omits it, and that
    must read as "no instructions to check," not as a loader error.
    """
    spec = importlib.util.spec_from_file_location(f"_gt_{gt_path.stem}", gt_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # the module IS the ground truth script
    return {name: getattr(module, name, default) for name, default in _METADATA_DEFAULTS.items()}


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
            if v is None or isinstance(v, str):
                continue
            try:
                vals.append(float(v))
            except (TypeError, ValueError):
                continue
    if not vals:
        return None
    has_pos = any(v > 0 for v in vals)
    has_neg = any(v < 0 for v in vals)
    return "diverging" if has_pos and has_neg else "sequential"


_DIVERGING_PALETTES = {"rdylgn", "rdbu", "puor"}


def _palette_kind(palette: str | None) -> str:
    """"diverging", "sequential", or "unknown" for a palette/hue name."""
    if not palette:
        return "unknown"
    return "diverging" if palette.strip().lower() in _DIVERGING_PALETTES else "sequential"


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


def check_colored_measure_selection(cand: dict, truth: dict, meta: dict) -> CheckResult:
    name = "Colored-measure selection (≤2 ceiling + right measure(s))"
    cand_mechanics = cand["tier1"].get("color_mechanics", [])
    ceiling_ok = len(cand_mechanics) <= 2
    ceiling_pts = 2 if ceiling_ok else 0
    canonical_colored = meta["CANONICAL_MEASURES"].get("colored", [])
    if not canonical_colored:
        identity_pts = 4
        identity_detail = "ground truth declares no canonical colored measures"
    elif not cand["tier2"].get("ok"):
        identity_pts = 0
        identity_detail = f"candidate failed to execute: {cand['tier2'].get('error')}"
    else:
        covered = 0
        for m in canonical_colored:
            if execution_tier.match_measure_by_value(cand["tier2"], truth["tier2"], m):
                covered += 1
        identity_pts = _round_points(covered / len(canonical_colored), 4)
        identity_detail = f"{covered}/{len(canonical_colored)} canonical colored measures covered by a candidate color call"
    pts = ceiling_pts + identity_pts
    detail = f"{'≤2 measures OK' if ceiling_ok else f'{len(cand_mechanics)} colored measures exceeds the ceiling of 2'}; {identity_detail}"
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
        shape = _measure_signedness(cand, entry.get("columns", []))
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
            ok = bool(cand["tier1"].get("grouping_present"))
        elif key == "row_count":
            n = _n_rows(cand)
            ok = n == expected
        elif key == "sort":
            col, direction = expected
            vals = cand["tier2"].get("columns", {}).get(col) if cand["tier2"].get("ok") else None
            if vals is None:
                ok = False
            else:
                nums = [v for v in vals if isinstance(v, (int, float))]
                ok = len(nums) == len(vals) and (
                    all(a >= b for a, b in zip(nums, nums[1:])) if direction == "desc"
                    else all(a <= b for a, b in zip(nums, nums[1:]))
                )
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
    if len(mechanics) < 2:
        return _na(name, "fewer than 2 colored measures; no collision possible")
    palettes = [e.get("palette") for e in mechanics[:2]]
    collision = palettes[0] is not None and palettes[0] == palettes[1]
    return CheckResult(name, 1, 0 if collision else 1, not collision, f"colored-measure palettes: {palettes}")


def check_summary_row_existence(cand: dict, truth: dict, meta: dict) -> CheckResult:
    name = "Summary-row existence + correct aggregation values"
    truth_summary = truth["tier2"].get("summary_rows") or []
    if not truth_summary:
        return _na(name, "ground truth has no grand-summary row")
    if not cand["tier2"].get("ok"):
        return CheckResult(name, 1, 0, False, f"candidate failed to execute: {cand['tier2'].get('error')}")
    cand_summary = cand["tier2"].get("summary_rows") or []
    if not cand_summary:
        return CheckResult(name, 1, 0, False, "candidate has no grand-summary row")
    truth_values = truth_summary[0].get("values", {})
    cand_values = cand_summary[0].get("values", {})
    shared = [k for k in truth_values if k in cand_values]
    if not shared:
        return CheckResult(name, 1, 0, False, "summary rows share no comparable columns")
    all_close = all(execution_tier.values_close(cand_values[k], truth_values[k]) for k in shared)
    return CheckResult(name, 1, 1 if all_close else 0, all_close, f"summary values compared on {shared}")


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

def _domain_element_symmetric(lo: str, hi: str) -> bool:
    try:
        return math.isclose(float(lo), -float(hi), rel_tol=1e-6, abs_tol=1e-9)
    except ValueError:
        pass
    a, b = lo.strip().lstrip("-").strip(), hi.strip().lstrip("-").strip()
    return a == b and lo.strip() != hi.strip()


def check_domain_computation(cand: dict, truth: dict, meta: dict) -> CheckResult:
    name = "Domain computation (symmetric / full-range / data-driven)"
    mechanics = cand["tier1"].get("color_mechanics", [])
    if not mechanics:
        return _na(name, "candidate has no colored measures")
    correct, total, notes = 0, 0, []
    for i, entry in enumerate(mechanics):
        shape = _measure_signedness(cand, entry.get("columns", []))
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
            # heatmap()'s auto-derived domain is always shape-correct by
            # construction (it computes symmetric-for-diverging /
            # full-range-for-sequential from the real data itself).
            correct += 1
            continue
        m = re.match(r"^\[(.+?),(.+)\]$", dom, re.S) if dom.startswith("[") else None
        if shape == "diverging":
            ok = bool(m) and _domain_element_symmetric(m.group(1), m.group(2))
        else:
            # Sequential: accept any literal bracketed domain as a
            # deliberate choice (verifying it covers the ACTUAL full data
            # range would need re-deriving the exact min/max the author
            # intended, which isn't recoverable from a variable-named
            # domain like `[dens_lo, dens_hi]`).
            ok = bool(m)
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
    visible = _visible_columns(cand)
    # "Essentially fully filled" counts a bold, uncolored HERO column as
    # accounted-for too, not just an actually-colored one — Step 3's rule
    # is that the hero gets bold text specifically AS THE ALTERNATIVE to a
    # third color fill, so it occupies the same "this column carries
    # meaning" role a colored measure would for this gate's purposes.
    accounted_for: set[str] = set(t1.get("bold_columns") or [])
    for e in mechanics:
        accounted_for |= set(e.get("columns", []))
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
    # clear sequential palette to harmonize with -- a diverging-only table,
    # multiple measures, or "no color" all resolve to the DA default
    # (usually navy) per palettes.md's own fallback, which is not a
    # verifiable violation, so it's given the benefit of the doubt.
    palettes = [e.get("palette", "").lower() for e in t1.get("color_mechanics", [])]
    seq_palettes = [p for p in palettes if p in _SEQ_PALETTE_TO_DA_FAMILY]
    if has_color and len(seq_palettes) == 1:
        expected_family = _SEQ_PALETTE_TO_DA_FAMILY[seq_palettes[0]]
        hue_ok = t1.get("heading_band_hue") == expected_family
        hue_detail = f"expected hue family '{expected_family}' for palette '{seq_palettes[0]}', got '{t1.get('heading_band_hue')}'"
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
    na_ok = sum(1 for e in mechanics if e.get("na_color") == "#808080")
    trunc_ok = sum(1 for e in mechanics if e.get("truncate") == "False")
    pts = _round_points(na_ok / len(mechanics), 2) + _round_points(trunc_ok / len(mechanics), 2)
    return CheckResult(name, 4, pts, pts == 4, f"na_color correct {na_ok}/{len(mechanics)}, truncate=False correct {trunc_ok}/{len(mechanics)}")


def check_summary_row_formatting(cand: dict, truth: dict, meta: dict) -> CheckResult:
    name = "Summary-row formatting matches body"
    cand_summary = cand["tier2"].get("summary_rows") or [] if cand["tier2"].get("ok") else []
    if not cand_summary:
        return _na(name, "candidate has no grand-summary row to check")
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
    fmt_map = cand["tier1"].get("fmt_column_map", {})
    applicable = {c: t for c, t in semantic_types.items() if c in fmt_map}
    if not applicable:
        return _na(name, "none of the candidate's formatted columns are covered by SEMANTIC_TYPES")
    ok_count = sum(
        1 for c, t in applicable.items()
        if fmt_map[c] in _SEMANTIC_TO_FMT.get(t, set())
    )
    all_ok = ok_count == len(applicable)
    return CheckResult(name, 4, _round_points(ok_count / len(applicable), 4), all_ok, f"{ok_count}/{len(applicable)} columns formatted per their semantic type")


def check_title_subtitle_caption_source(cand: dict, truth: dict, meta: dict) -> CheckResult:
    name = "Title/subtitle/caption/source presence per gating rules"
    t1 = cand["tier1"]
    title_pts = 1 if t1.get("title_text") else 0
    subtitle_pts = 1 if t1.get("subtitle_text") else 0
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
    bolded = bool(cand["tier1"].get("bold_columns"))
    return CheckResult(name, 2, 2 if bolded else 0, bolded, f"bold_columns={cand['tier1'].get('bold_columns')}")


def check_render_mechanics(cand: dict, truth: dict, meta: dict) -> CheckResult:
    name = "Render mechanics (zoom/expand fit-order rule)"
    params = cand["tier1"].get("render_params") or {}
    if not params:
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
    if expand > 5.0:
        return CheckResult(name, 2, 1, False, f"zoom={zoom} < 2.0, but expand={expand} was raised first (partial credit per the fit-order rule)")
    return CheckResult(name, 2, 0, False, f"zoom={zoom} < default 2.0 without raising expand/vwidth/vheight first")


def check_summary_row_visual_distinction(cand: dict, truth: dict, meta: dict) -> CheckResult:
    name = "Summary-row visual distinction from body"
    cand_summary = cand["tier2"].get("summary_rows") or [] if cand["tier2"].get("ok") else []
    if not cand_summary:
        return _na(name, "candidate has no grand-summary row")
    distinct = bool(re.search(r"#BDBDBD", cand["source"], re.I)) or bool(
        re.search(r"loc\s*\.\s*(?:grand_)?summary_rows\s*\(", cand["source"])
    )
    return CheckResult(name, 1, 1 if distinct else 0, distinct, "checked for the summary/group structural rule color (#BDBDBD) or a summary-row-scoped tab_style")


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
    mentions_ok = not should_mention or any(k.lower() in caption for k in should_mention)
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
