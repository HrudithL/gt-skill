#!/usr/bin/env python3
"""One-off: the transform that produced both consensus-tuning passes'
`eval-results/**` data (2026-08-09) -- kept for auditability, not meant to
be re-run (it's already applied; running it again on the current
`metrics.json` would be a no-op since all 6 checks it removes are already
gone from every check list). Run against `main`'s ORIGINAL, pre-either-pass
`metrics.json` (not incrementally on top of a partially-transformed one).

Removing a check from the comparator is provably a pure subtraction of
that check's fixed points from whichever bucket it belonged to -- confirmed
by grep that none of the 6 removed checks' underlying fields/helpers are
read by any other still-live check (see `eval-results/SUMMARY.md`'s
methodology note). Re-running the comparator fresh against each candidate
instead would (a) require a live, correctly-populated execution environment
(`creator`'s no longer exists -- its raw sweep dir lived only in a deleted
ephemeral worktree) and (b) if run against a DIFFERENT sweep than the one
already scored, conflates "the comparator changed" with "the candidates
changed" into one number -- both mistakes an internal review caught in an
earlier draft of the first pass. Pure subtraction on the already-scored,
already-committed `metrics.json` avoids both problems and works identically
for all 4 skills.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVAL_RESULTS = ROOT / "eval-results"

# Pass 1 (2026-08-09): uniformly near-zero across every skill.
# Pass 2 (2026-08-09): flat/non-discriminating across every skill (moderate
# score, but the same moderate score regardless of which skill produced the
# candidate) -- see eval-results/SUMMARY.md for both passes' full rationale.
REMOVED = [
    "Hero-column formatting when nothing is colored",
    "Stub tint + grey-budget correctness",
    "Caption doesn't just restate the subtitle",
    "Title/subtitle/caption/source presence per gating rules",
    "Subtitle quality",
    "Color theme/palette taste",
]
REMOVED_SET = set(REMOVED)

# All 6 happen to be Formatting-compliance checks -- if a future pass
# removes a Data-compliance check too, this script's bucket handling
# (format_earned/possible only) would need to branch per-check.


def transform_score(score: dict) -> dict:
    checks = [c for c in score["checks"] if c["name"] not in REMOVED_SET]
    removed_checks = [c for c in score["checks"] if c["name"] in REMOVED_SET]
    removed_earned = sum(c["points_earned"] for c in removed_checks)
    removed_possible = sum(c["points_possible"] for c in removed_checks)

    new_format_earned = score["format_earned"] - removed_earned
    new_format_possible = score["format_possible"] - removed_possible
    new_total_earned = score["total_earned"] - removed_earned
    new_total_possible = score["total_possible"] - removed_possible

    return {
        "report_text": None,  # filled in by rewrite_report_text against the ORIGINAL text
        "data_earned": score["data_earned"],
        "data_possible": score["data_possible"],
        "format_earned": new_format_earned,
        "format_possible": new_format_possible,
        "total_earned": new_total_earned,
        "total_possible": new_total_possible,
        "pct": 100 * new_total_earned / new_total_possible if new_total_possible else None,
        "checks": checks,
    }


_CHECK_LINE_RE = re.compile(r"^\[(PASS|FAIL|N/A)\] \[(MECHANICAL|JUDGE)\] (.+?): (\d+)/(\d+) -- ")
_TOTAL_RE = re.compile(r"^TOTAL: (\d+)/(\d+) \(([\d.]+)%\)$")
_DATA_RE = re.compile(r"^  Data-compliance:\s+(\d+)/(\d+)$")
_FORMAT_RE = re.compile(r"^  Formatting-compliance:\s+(\d+)/(\d+)$")


def rewrite_report_text(old_text: str, new_score: dict) -> str:
    lines = old_text.splitlines()
    out = []
    for line in lines:
        m = _CHECK_LINE_RE.match(line)
        if m and m.group(3) in REMOVED_SET:
            continue
        if _TOTAL_RE.match(line):
            pct = new_score["pct"] if new_score["pct"] is not None else 0.0
            out.append(f"TOTAL: {new_score['total_earned']}/{new_score['total_possible']} ({pct:.1f}%)")
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
    for skill in ["house", "prose", "scripts", "creator"]:
        skill_dir = EVAL_RESULTS / skill
        metrics_path = skill_dir / "metrics.json"
        metrics = json.loads(metrics_path.read_text())
        n_transformed = 0
        for pid, entry in metrics["prompts"].items():
            for variant, v in entry["variants"].items():
                score = v.get("score")
                if not score:
                    continue
                new_score = transform_score(score)
                report_path = skill_dir / "samples" / pid / variant / "report.txt"
                if report_path.is_file():
                    new_score["report_text"] = rewrite_report_text(report_path.read_text(), new_score)
                    report_path.write_text(new_score["report_text"])
                else:
                    new_score["report_text"] = score.get("report_text")
                v["score"] = new_score
                n_transformed += 1
        metrics_path.write_text(json.dumps(metrics, indent=2))
        print(f"{skill}: transformed {n_transformed} scored variants")


if __name__ == "__main__":
    main()
