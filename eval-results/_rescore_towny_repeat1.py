#!/usr/bin/env python3
"""One-off: the real re-score behind `scripts/towny_growth_trends/repeat_1`'s
2026-08-11 metrics.json/report.txt update -- kept for auditability, not
meant to be re-run. Re-running it would make a fresh LLM judge API call
and is not guaranteed to reproduce the exact same judge scores (mechanical
checks are deterministic and would match; judge-backed ones are not
byte-reproducible by construction). The values already committed came
from running exactly this script once, on 2026-08-11, then hand-verifying
the printed report against `eval-results/scripts/metrics.json`.

Unlike `_recompute_mechanical_checks.py` (mechanical-only recompute,
judge-backed checks preserved byte-identical from the original stored
run), this invocation needed a REAL re-score: its Tier-2 execution status
genuinely changed, from failing (the `gt = finalize(gt, ...)` /
`GT.gtsave` no-render-stub bug fixed in PR #89) to passing. Its previously
stored judge result was elicited under the old failing-execution context
and is no longer representative, so it had to be re-run through
`comparator.compare()` in full -- mechanical checks AND a fresh judge
call -- rather than patched piecemeal.

Before: 21/81 (25.9%), Tier-2 execution failed.
After:  68/88 (77.3%), Tier-2 execution passed, judge re-run for real.

Mirrors `scripts/gt_compare.py`'s own ground-truth/prompt-text resolution
exactly (see that file's docstring) -- this is that same CLI's logic,
inlined so the candidate path can point at the specific sweep-dir
invocation rather than an arbitrary CLI argument.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVAL_RESULTS = ROOT / "eval-results"

sys.path.insert(0, str(ROOT))
from runner import comparator as c  # noqa: E402

_DIFFICULTIES = ("easy", "medium", "hard")

SKILL = "scripts"
PROMPT_ID = "towny_growth_trends"
VARIANT = "repeat_1"


def _resolve_ground_truth(prompt_id: str) -> Path:
    for d in _DIFFICULTIES:
        p = ROOT / "prompts" / d / "ground_truth" / f"{prompt_id}.py"
        if p.is_file():
            return p
    raise FileNotFoundError(prompt_id)


def _resolve_prompt_text(prompt_id: str) -> str:
    for d in _DIFFICULTIES:
        p = ROOT / "prompts" / d / f"{prompt_id}.json"
        if p.is_file():
            return json.loads(p.read_text()).get("prompt", "") or ""
    return ""


def main() -> None:
    metrics_path = EVAL_RESULTS / SKILL / "metrics.json"
    metrics = json.loads(metrics_path.read_text())
    sweep_dir = Path(metrics["sweep_dir"])
    candidate = sweep_dir / "prompts" / PROMPT_ID / VARIANT / "table.py"
    if not candidate.is_file():
        raise SystemExit(f"candidate not found (sweep_dir may no longer exist on disk): {candidate}")

    ground_truth = _resolve_ground_truth(PROMPT_ID)
    prompt_text = _resolve_prompt_text(PROMPT_ID)
    report = c.compare(candidate, ground_truth, prompt_text)
    report_text = c.format_report(report)
    print(report_text)

    new_score = {
        "report_text": report_text,
        "data_earned": report.data_earned,
        "data_possible": report.data_possible,
        "format_earned": report.format_earned,
        "format_possible": report.format_possible,
        "total_earned": report.total_earned,
        "total_possible": report.total_possible,
        "pct": 100 * report.total_earned / report.total_possible if report.total_possible else None,
        "checks": [
            {
                "name": r.name,
                "points_earned": r.points_earned,
                "points_possible": r.points_possible,
                "passed": r.passed,
                "detail": r.detail,
                "tier": r.tier,
            }
            for r in report.checks
        ],
    }
    metrics["prompts"][PROMPT_ID]["variants"][VARIANT]["score"] = new_score
    metrics_path.write_text(json.dumps(metrics, indent=2))

    report_path = EVAL_RESULTS / SKILL / "samples" / PROMPT_ID / VARIANT / "report.txt"
    if report_path.is_file():
        report_path.write_text(report_text)

    print(f"\nwrote {new_score['total_earned']}/{new_score['total_possible']} ({new_score['pct']:.1f}%)")


if __name__ == "__main__":
    main()
