#!/usr/bin/env python3
"""One-off: the transform that recomputed eval-results/** after the
2026-08-11 bare-`finalize(gt, ...)` comparator fix -- kept for
auditability, not meant to be re-run (it's already applied; running it
again would be a no-op since every mechanical check already reflects the
fixed logic).

Recomputes every MECHANICAL check fresh (via the fixed
`_stmt_targets_name`) against each already-committed candidate table.py,
while preserving the 4 judge-backed checks' stored values byte-identical
(no fresh judge API calls -- this bug fix doesn't touch judge logic at
all, so re-invoking the judge would only add cost and noise, not
correctness). Mirrors `_apply_check_removal.py`'s discipline (no
re-execution beyond what's needed, no candidate-set change) but
recomputes a check's value instead of removing it.

Resolves each prompt's ground truth the same way scripts/gt_compare.py
does (search prompts/<difficulty>/ground_truth/<prompt_id>.py across the
three difficulty tiers). Scores candidates from each skill's ORIGINAL
sweep directory (`metrics.json`'s own `sweep_dir` field) -- not the
curated `eval-results/*/samples/` copies, which only ever contain
table.py/table.png/report.txt and have no CSV data siblings, so they
can't actually execute.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVAL_RESULTS = ROOT / "eval-results"

sys.path.insert(0, str(ROOT))
from runner import comparator as c  # noqa: E402

JUDGE_CHECK_NAMES = {
    "Grouping-choice quality",
    "Column-label concept-correctness",
    "Title quality",
    "Column order quality",
}

_DIFFICULTIES = ("easy", "medium", "hard")


def _resolve_ground_truth(prompt_id: str) -> Path:
    for d in _DIFFICULTIES:
        p = ROOT / "prompts" / d / "ground_truth" / f"{prompt_id}.py"
        if p.is_file():
            return p
    raise FileNotFoundError(prompt_id)


def recompute_checks(candidate_path: Path, ground_truth_path: Path) -> list[c.CheckResult]:
    cand = c.build_fingerprint(candidate_path)
    truth = c.build_fingerprint(ground_truth_path)
    meta = c.load_ground_truth_metadata(ground_truth_path)
    results = []
    for fn in c.DATA_CHECKS + c.FORMAT_CHECKS:
        if fn.__name__ in {
            "check_grouping_choice_quality",
            "check_label_concept_correctness",
            "check_title_quality",
            "check_column_order_quality",
        }:
            continue  # judge-backed -- preserved from stored data, not recomputed
        results.append(fn(cand, truth, meta))
    return results


_CHECK_LINE_RE = re.compile(r"^\[(PASS|FAIL|N/A)\] \[(MECHANICAL|JUDGE)\] (.+?): (\d+)/(\d+) -- (.*)$")
_TOTAL_RE = re.compile(r"^TOTAL: (\d+)/(\d+) \(([\d.]+)%\)$")
_DATA_RE = re.compile(r"^  Data-compliance:\s+(\d+)/(\d+)$")
_FORMAT_RE = re.compile(r"^  Formatting-compliance:\s+(\d+)/(\d+)$")


def rewrite_report_text(old_text: str, new_checks_by_name: dict, new_score: dict) -> str:
    lines = old_text.splitlines()
    out = []
    for line in lines:
        m = _CHECK_LINE_RE.match(line)
        if m and m.group(3) not in JUDGE_CHECK_NAMES:
            nc = new_checks_by_name[m.group(3)]
            # Matches comparator.format_report's own precedence exactly (comparator.py's
            # `mark = "N/A" if r.points_possible == 0 else (...)`) -- N/A must be checked
            # FIRST: `_na()` results have `passed=True` (see its own docstring), so
            # checking `passed` before `points_possible == 0` mislabels every N/A check
            # as PASS, falsely claiming a condition was verified when it wasn't graded
            # at all. (Internal review finding, 2026-08-11: this inversion originally
            # shipped here and corrupted 72 of 96 regenerated report.txt files.)
            status = "N/A" if nc["points_possible"] == 0 else ("PASS" if nc["passed"] else "FAIL")
            out.append(f"[{status}] [{nc['tier'].upper()}] {nc['name']}: {nc['points_earned']}/{nc['points_possible']} -- {nc['detail']}")
            continue
        if _TOTAL_RE.match(line):
            out.append(f"TOTAL: {new_score['total_earned']}/{new_score['total_possible']} ({new_score['pct']:.1f}%)")
            continue
        if _DATA_RE.match(line):
            out.append(f"  Data-compliance:        {new_score['data_earned']}/{new_score['data_possible']}")
            continue
        if _FORMAT_RE.match(line):
            out.append(f"  Formatting-compliance:  {new_score['format_earned']}/{new_score['format_possible']}")
            continue
        out.append(line)
    return "\n".join(out) + ("\n" if old_text.endswith("\n") else "")


def main():
    changed_summary = []
    for skill in ["house", "prose", "scripts", "creator"]:
        skill_dir = EVAL_RESULTS / skill
        metrics_path = skill_dir / "metrics.json"
        metrics = json.loads(metrics_path.read_text())
        sweep_dir = Path(metrics["sweep_dir"])
        sweep_dir_exists = sweep_dir.is_dir()
        if not sweep_dir_exists:
            print(f"{skill}: sweep_dir {sweep_dir} no longer exists -- cannot re-execute; leaving mechanical checks unchanged")
        n_diff = 0
        for pid, entry in metrics["prompts"].items():
            gt_path = _resolve_ground_truth(pid)
            for variant, v in entry["variants"].items():
                score = v.get("score")
                if not score:
                    continue
                if not sweep_dir_exists:
                    continue  # e.g. creator -- no execution environment left, can't safely recompute
                # Score from the ORIGINAL sweep dir (has the CSV data files as
                # siblings, copied there by the harness at invocation time) --
                # NOT the curated eval-results/*/samples/ copy, which only ever
                # has table.py/table.png/report.txt and would fail to execute.
                candidate = sweep_dir / "prompts" / pid / variant / "table.py"
                if not candidate.is_file():
                    continue
                fresh_mechanical = recompute_checks(candidate, gt_path)
                fresh_by_name = {r.name: r for r in fresh_mechanical}

                new_checks = []
                # score["checks"] is stored in exactly DATA_CHECKS + FORMAT_CHECKS order
                # (ComparatorReport.checks = data_results + format_results) -- walk it in
                # that same order, substituting freshly-recomputed mechanical checks in place.
                for old in score["checks"]:
                    name = old["name"]
                    if name in JUDGE_CHECK_NAMES:
                        new = dict(old)
                    else:
                        fresh = fresh_by_name[name]
                        if (fresh.points_earned, fresh.points_possible, fresh.passed) != (old["points_earned"], old["points_possible"], old["passed"]):
                            n_diff += 1
                            changed_summary.append((skill, pid, variant, name, old["points_earned"], fresh.points_earned))
                        new = {
                            "name": fresh.name,
                            "points_earned": fresh.points_earned,
                            "points_possible": fresh.points_possible,
                            "passed": fresh.passed,
                            "detail": fresh.detail,
                            "tier": fresh.tier,
                        }
                    new_checks.append(new)

                # Recompute bucket totals by position: first len(DATA_CHECKS) stored
                # checks are data, rest are format (matches compare()'s own
                # data_results + format_results concatenation order).
                n_data = len(c.DATA_CHECKS)
                data_checks_new = new_checks[:n_data]
                format_checks_new = new_checks[n_data:]
                data_earned = sum(x["points_earned"] for x in data_checks_new)
                data_possible = sum(x["points_possible"] for x in data_checks_new)
                format_earned = sum(x["points_earned"] for x in format_checks_new)
                format_possible = sum(x["points_possible"] for x in format_checks_new)
                total_earned = data_earned + format_earned
                total_possible = data_possible + format_possible

                new_score = {
                    "report_text": None,
                    "data_earned": data_earned,
                    "data_possible": data_possible,
                    "format_earned": format_earned,
                    "format_possible": format_possible,
                    "total_earned": total_earned,
                    "total_possible": total_possible,
                    "pct": 100 * total_earned / total_possible if total_possible else None,
                    "checks": new_checks,
                }
                report_path = skill_dir / "samples" / pid / variant / "report.txt"
                if report_path.is_file():
                    new_checks_by_name = {ch["name"]: ch for ch in new_checks}
                    new_score["report_text"] = rewrite_report_text(report_path.read_text(), new_checks_by_name, new_score)
                    report_path.write_text(new_score["report_text"])
                else:
                    new_score["report_text"] = score.get("report_text")
                v["score"] = new_score
        metrics_path.write_text(json.dumps(metrics, indent=2))
        print(f"{skill}: {n_diff} check-value changes")

    print("\n--- changed checks ---")
    for skill, pid, variant, name, old_pts, new_pts in changed_summary:
        print(f"{skill}/{pid}/{variant}: {name}: {old_pts} -> {new_pts}")


if __name__ == "__main__":
    main()
