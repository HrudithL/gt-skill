#!/usr/bin/env python3
"""Tier 2 — execution-level extraction + value-based matching.

Per ``.planning/09-ground-truth-comparator.md`` §6: row/entity selection
identity, computed-value correctness, colored-measure identity-by-*value*,
and summary-row values can't be read off source text — a value computed
three lines earlier and passed by variable name is invisible to
``runner.convergence``'s regex parsing (Tier 1). This module execs a
``table.py`` (candidate OR ground truth — both are parsed the same way) in a
hard-timed-out subprocess, pulls the module's top-level ``gt`` object (the
convention already established for the CI checker, see
``CONSISTENCY_FAILURES.md`` R3) plus the ``DataFrame`` that built it, and
returns a JSON-safe fingerprint of the ACTUAL rendered values. Matching
functions below then diff those fingerprints by value, never by column name
or label.

Version pin (open risk in the spec §13): extraction reads ``GT`` private
attributes (``_tbl_data``, ``_stub``, ``_boxhead``, ``_summary_rows_grand``).
Verified against ``great_tables==0.22.0`` — if that package is upgraded and
this stops working, this is the first place to check.
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

# Bump this (and the duplicate literal inside _EXEC_RUNNER, which runs in a
# fresh subprocess and can't import this module) if `great_tables` is
# upgraded and extraction needs re-verifying against its new internals (see
# module docstring). `exec_table()`'s result carries `gt_version` and
# `gt_version_pin_mismatch` so a silent extraction failure after an
# unpinned-version upgrade is attributable rather than a mystery — this
# warns rather than hard-blocks, since a version bump may not actually
# touch the attributes this module reads.
_GT_VERSION_PINNED = "0.22.0"

# Subprocess payload: exec's the target script in a fresh interpreter (hard
# killable on timeout), neutralizes the harness's Chrome shims so importing
# them never launches a browser, stubs `gtsave` to a no-op, then reads the
# top-level `gt` GT instance and JSON-dumps a fingerprint of it on the last
# stdout line. Mirrors runner.convergence._DATA_HASH_RUNNER's safety pattern
# (fresh subprocess, redirected stdout, exceptions never escape) but returns
# full row/column values instead of a single hash.
_EXEC_RUNNER = r'''
import sys, types, io, json, contextlib, math

path = sys.argv[1]
_PINNED_GT_VERSION = "0.22.0"

for name in ("gtskill_chrome", "_gtskill_sidecar"):
    sys.modules[name] = types.ModuleType(name)

_installed_gt_version = None
try:
    import great_tables as _gt
    _gt.GT.gtsave = lambda *a, **k: None
    _installed_gt_version = getattr(_gt, "__version__", None)
except Exception:
    pass


def _json_safe(v):
    if v is None:
        return None
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        # +/-inf (e.g. a percent-change divide-by-zero) is not valid JSON --
        # json.dumps would emit the non-standard Infinity/-Infinity token.
        # Normalized to None like NaN: both mean "not a usable number".
        return None
    if isinstance(v, (bool, int, float, str)):
        return v
    try:
        import numpy as _np
        if isinstance(v, _np.generic):
            v = v.item()
            return _json_safe(v)
    except Exception:
        pass
    try:
        import pandas as _pd
        if _pd.isna(v):
            return None
    except Exception:
        pass
    return str(v)


def main():
    with open(path) as fh:
        src = fh.read()
    ns = {"__name__": "__main__", "__file__": path}
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(compile(src, path, "exec"), ns)

    gt = ns.get("gt")
    if gt is None or type(gt).__name__ != "GT":
        return {"ok": False, "error": "no top-level `gt` GT instance in table.py"}

    tbl = gt._tbl_data

    def _series_to_list(series):
        # pandas Series has .tolist(); a Polars Series has .to_list() instead
        # (great_tables supports both backends per SPEC.md/api.md) -- fall
        # back to plain iteration for anything else.
        if hasattr(series, "tolist"):
            return series.tolist()
        if hasattr(series, "to_list"):
            return series.to_list()
        return list(series)

    columns = {col: [_json_safe(v) for v in _series_to_list(tbl[col])] for col in tbl.columns}

    stub_column = None
    group_column = None
    hidden_columns = []
    for c in gt._boxhead:
        tname = c.type.name if hasattr(c.type, "name") else str(c.type)
        if tname == "stub":
            stub_column = c.var
        elif tname == "row_group":
            group_column = c.var
        elif tname == "hidden":
            hidden_columns.append(c.var)

    rows = list(gt._stub.rows)
    row_ids = [_json_safe(r.rowname) for r in rows] if stub_column else None
    row_group_ids = [_json_safe(r.group_id) for r in rows] if group_column else None
    row_order = [r.rownum_i for r in rows]

    summary_rows = []
    try:
        grand = gt._summary_rows_grand
        if grand is not None:
            for info in grand._d.get("grand", []):
                summary_rows.append({
                    "label": _json_safe(getattr(info, "label", None)),
                    "values": {k: _json_safe(v) for k, v in getattr(info, "values", {}).items()},
                })
    except Exception:
        pass

    return {
        "ok": True,
        "error": None,
        "n_rows": len(row_order),
        "row_order": row_order,
        "row_ids": row_ids,
        "row_group_ids": row_group_ids,
        "stub_column": stub_column,
        "group_column": group_column,
        "hidden_columns": hidden_columns,
        "columns": columns,
        "summary_rows": summary_rows,
        "gt_version": _installed_gt_version,
        "gt_version_pin_mismatch": (
            _installed_gt_version is not None and _installed_gt_version != _PINNED_GT_VERSION
        ),
    }


try:
    _fp = main()
except Exception as e:
    _fp = {"ok": False, "error": f"{type(e).__name__}: {e}"}

sys.stdout.write("EXECFP:" + json.dumps(_fp) + "\n")
'''


def exec_table(py_path: Path, timeout: float = 30.0) -> dict:
    """Exec ``py_path`` in a subprocess and return its execution fingerprint.

    Always returns a dict with at least ``{"ok": bool, "error": str|None}`` —
    never raises. ``ok=False`` covers a missing/non-``GT`` top-level ``gt``,
    a script exception, or a hard timeout (this never hangs; the subprocess
    is killed). Callers that need row/column data should check ``ok`` first
    — every other key is only present when ``ok`` is True.
    """
    if not py_path.is_file():
        return {"ok": False, "error": f"no such file: {py_path}"}
    # Resolve to an absolute path BEFORE spawning: the subprocess runs with
    # cwd=py_path.parent, so a relative path like "runs/x/table.py" would
    # resolve inside the child as "runs/x/runs/x/table.py" once cwd has
    # already moved into "runs/x".
    abs_path = py_path.resolve()
    try:
        proc = subprocess.run(
            [sys.executable, "-c", _EXEC_RUNNER, str(abs_path)],
            cwd=str(abs_path.parent),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"timed out after {timeout}s"}
    except Exception as e:
        return {"ok": False, "error": f"subprocess failed to start: {e}"}

    for line in proc.stdout.splitlines():
        if line.startswith("EXECFP:"):
            try:
                return json.loads(line[len("EXECFP:"):])
            except Exception as e:
                return {"ok": False, "error": f"unparseable fingerprint: {e}"}
    detail = proc.stderr.strip()[-2000:] if proc.stderr else "(no stderr)"
    return {"ok": False, "error": f"no fingerprint produced; stderr: {detail}"}


# --------------------------------------------------------------------------- #
# value-based matching primitives (pure, no subprocess) — the ≥95%/leftmost-
# tie-break policy locked 2026-07-31 for Tier 2 value matching.
# --------------------------------------------------------------------------- #
_REL_TOL = 1e-6
_ABS_TOL = 1e-9
_MATCH_THRESHOLD = 0.95


def values_close(a: Any, b: Any, *, rel_tol: float = _REL_TOL, abs_tol: float = _ABS_TOL) -> bool:
    """True if `a` and `b` are "the same value" for matching purposes.

    Both None -> True (both missing/NA agree). Exactly one None -> False.
    Both coercible to float -> `math.isclose(rel_tol=1e-6, abs_tol=1e-9)`
    (effectively exact-match with float-noise headroom — candidate and
    ground truth compute from the identical source CSV, so a genuinely
    different formula differs by far more than this). Otherwise, string
    equality after `str().strip()` (case-sensitive — labels/categories are
    not free-form prose, unlike the caption keyword check).
    """
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    try:
        fa, fb = float(a), float(b)
        return math.isclose(fa, fb, rel_tol=rel_tol, abs_tol=abs_tol)
    except (TypeError, ValueError):
        return str(a).strip() == str(b).strip()


def normalize_id(x: Any) -> str:
    """Canonical form of a row/entity identifier for set comparison."""
    return str(x).strip().casefold()


def row_set_identity(
    candidate_row_ids: list | None,
    truth_row_ids: list | None,
    *,
    candidate_group_ids: list | None = None,
    truth_group_ids: list | None = None,
) -> dict:
    """Set-based (order/count-blind) comparison of two row-identifier lists.

    Returns ``{"matched", "candidate_only", "truth_only", "precision",
    "recall", "exact"}``. `precision`/`recall` are `None` only when a side is
    `None` (no stub at all — genuinely "not comparable"). An empty list
    (`[]`) is NOT the same as `None`: a stub that exists but whose filter
    selected zero rows is a real, and often severe, selection failure — it
    must score `recall=0.0` against a nonempty ground truth, not be treated
    as "not comparable" and skipped.

    `*_group_ids`, when BOTH are supplied, compare `(group_id, row_id)`
    identities rather than bare row ids — a stub label that repeats across
    groups (e.g. "Small"/"Medium" reused in every `groupname_col` group)
    would otherwise dedupe into a single set entry, letting a candidate
    covering just one group falsely report `exact=True` against a
    multi-group ground truth. Group ids are ignored (bare row-id identity)
    when only one side supplies them, per the same both-sides-or-neither
    rule `_row_keys` uses — a grouping difference between candidate and
    truth must not, by itself, make otherwise-identical rows look distinct.
    """
    if candidate_row_ids is None or truth_row_ids is None:
        return {
            "matched": 0, "candidate_only": [], "truth_only": [],
            "precision": None, "recall": None, "exact": False,
        }
    use_groups = bool(candidate_group_ids) and bool(truth_group_ids)
    cand = set(_row_keys(candidate_row_ids, candidate_group_ids if use_groups else None))
    truth = set(_row_keys(truth_row_ids, truth_group_ids if use_groups else None))
    matched = cand & truth
    precision = (len(matched) / len(cand)) if cand else (1.0 if not truth else 0.0)
    recall = (len(matched) / len(truth)) if truth else (1.0 if not cand else 0.0)
    return {
        "matched": len(matched),
        "candidate_only": sorted(cand - truth),
        "truth_only": sorted(truth - cand),
        "precision": precision,
        "recall": recall,
        "exact": cand == truth,
    }


def _row_key(row_id: Any, group_id: Any | None) -> tuple:
    """Alignment key for one row: `(group_id, row_id)`, both normalized.

    Including `group_id` matters whenever stub labels repeat across groups
    (e.g. a "Small"/"Medium" stub reused in every `groupname_col` group) —
    keying by `row_id` alone would collapse every group's "Small" row onto
    a single dict slot, silently keeping only the last group's value and
    aligning it against every other group's "Small" row too.
    """
    return (normalize_id(group_id) if group_id is not None else None, normalize_id(row_id))


def _row_keys(row_ids: list, group_ids: list | None) -> list[tuple]:
    """`_row_key` for every row, gated on `group_ids` genuinely being present.

    A caller-supplied `group_ids=None`/`[]` (that side has no grouping)
    must NOT be silently defaulted to a list of `None`s and combined
    key-wise with the OTHER side's real group ids — `(None, "Small")` would
    never equal `("g1", "Small")` even though the stub id matches and the
    only real difference is which side happens to report grouping. Bare
    row-id keys (`group_id=None` on both sides uniformly) are used whenever
    grouping isn't usable on this side.
    """
    if not group_ids:
        return [_row_key(rid, None) for rid in row_ids]
    return [_row_key(rid, gid) for rid, gid in zip(row_ids, group_ids)]


def _shared_pairs(
    candidate_fp: dict, truth_fp: dict, candidate_col: str, truth_col: str,
) -> list[tuple[Any, Any]]:
    """Value pairs for `candidate_col`/`truth_col`, aligned by stub row id
    (and row-group id, when BOTH sides provide one — see `_row_keys`).

    Falls back to positional alignment (by `row_order` index) when either
    side has no stub — the best available alignment without a named key.
    """
    cand_cols = candidate_fp.get("columns", {})
    truth_cols = truth_fp.get("columns", {})
    if candidate_col not in cand_cols or truth_col not in truth_cols:
        return []
    cand_ids = candidate_fp.get("row_ids")
    truth_ids = truth_fp.get("row_ids")
    if cand_ids and truth_ids:
        # Group-aware keys only when BOTH sides report grouping -- otherwise
        # bare row-id keys on both sides (see _row_keys).
        use_groups = bool(candidate_fp.get("row_group_ids")) and bool(truth_fp.get("row_group_ids"))
        cand_keys = _row_keys(cand_ids, candidate_fp.get("row_group_ids") if use_groups else None)
        truth_keys = _row_keys(truth_ids, truth_fp.get("row_group_ids") if use_groups else None)
        truth_by_key = {key: i for i, key in enumerate(truth_keys)}
        pairs = []
        for i, key in enumerate(cand_keys):
            j = truth_by_key.get(key)
            if j is not None and i < len(cand_cols[candidate_col]) and j < len(truth_cols[truth_col]):
                pairs.append((cand_cols[candidate_col][i], truth_cols[truth_col][j]))
        return pairs
    n = min(len(cand_cols[candidate_col]), len(truth_cols[truth_col]))
    return list(zip(cand_cols[candidate_col][:n], truth_cols[truth_col][:n]))


def column_match_fraction(candidate_fp: dict, truth_fp: dict, candidate_col: str, truth_col: str) -> float | None:
    """Fraction of shared (by row id) values that match within tolerance.

    None when there is nothing to compare (column missing on either side,
    or zero shared rows) — never fabricated as 0.0, so a "no data" case is
    distinguishable from "compared and disagreed."
    """
    pairs = _shared_pairs(candidate_fp, truth_fp, candidate_col, truth_col)
    if not pairs:
        return None
    matches = sum(1 for a, b in pairs if values_close(a, b))
    return matches / len(pairs)


def match_measure_by_value(
    candidate_fp: dict, truth_fp: dict, truth_col: str, *, threshold: float = _MATCH_THRESHOLD,
) -> str | None:
    """Which candidate column is "the same measure" as `truth_col`, by value.

    Scores every VISIBLE, non-structural candidate column against
    `truth_col` via `column_match_fraction` and returns the first (leftmost,
    by the candidate DataFrame's own column order — the same tie-break
    `palettes.md` uses for primary/secondary measure assignment) column
    clearing `threshold`. None if no candidate column clears it.

    The stub column, the group column, and every `cols_hide(...)`-hidden
    column are excluded from the search: a candidate that hides a raw copy
    of a measure while displaying a derived/rounded version under a
    different name would otherwise match on the hidden column (identical
    values) instead of the actual rendered, colored one — attributing the
    color to the wrong column.
    """
    excluded = {candidate_fp.get("stub_column"), candidate_fp.get("group_column")}
    excluded |= set(candidate_fp.get("hidden_columns") or [])
    best_col: str | None = None
    for col in candidate_fp.get("columns", {}):
        if col in excluded:
            continue
        frac = column_match_fraction(candidate_fp, truth_fp, col, truth_col)
        if frac is not None and frac >= threshold:
            best_col = col
            break
    return best_col


def computed_value_correctness(candidate_fp: dict, truth_fp: dict, column: str, *, threshold: float = _MATCH_THRESHOLD) -> dict:
    """Same-named column on both sides: fraction of shared rows matching.

    Returns ``{"fraction": float|None, "passed": bool}`` — `passed` is
    `fraction is not None and fraction >= threshold`. Used when the
    candidate is expected to keep the ground truth's own column name
    (e.g. a derived column the ground truth's metadata names directly),
    as opposed to `match_measure_by_value`'s name-blind search.
    """
    frac = column_match_fraction(candidate_fp, truth_fp, column, column)
    return {"fraction": frac, "passed": frac is not None and frac >= threshold}
