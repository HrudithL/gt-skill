# `scripts` skill — eval summary

Sweep: `runs/sweep/20260809_124542_scripts_6prompts` — 6 corpus prompts x (3
repeats + 1 auto-baseline), Haiku, scored by `runner.comparator.compare()`
against each prompt's ground truth. Full detail in [`metrics.json`](metrics.json).
This is a fresh sweep (2026-08-09), not the 2026-08-07 one the consensus-
tuning passes below were validated against — see the top-level
[`SUMMARY.md`](../SUMMARY.md)'s "Data refresh" section.

**Comparator methodology (2026-08-09, 2 passes):** 6 checks were removed
from `runner/comparator.py` — 3 uniformly near-zero across every skill
(hero-column formatting, stub tint/grey-budget, caption-not-restating-
subtitle), then 3 more flat/non-discriminating across every skill (title/
subtitle/caption/source presence, subtitle quality, color theme/palette
taste). See the top-level [`SUMMARY.md`](../SUMMARY.md) for the full
removal rationale and cross-skill comparison. Scores below are **not
comparable** to this file's pre-2026-08-09 numbers (denominator shrank
114 -> 97 pts).

| Metric (mean across 6 prompts) | `scripts` skill | baseline (no skill) |
|---|---|---|
| Comparator total score | **62.4%** | 24.7% |
| Cost per invocation | $0.175 | $0.090 |
| Score spread across 3 repeats | 23.8 points | n/a (1 run) |

See [`plots/cost.png`](plots/cost.png), [`plots/tokens.png`](plots/tokens.png),
[`plots/consistency.png`](plots/consistency.png),
[`plots/comparator_score.png`](plots/comparator_score.png).

`great-tables-ci` is the same 7-step-flowchart skill as `prose` plus a
mechanical checker loop (`gt_check.py`) it runs and fixes against before
finishing. On this sweep `house` edges it out on mean score (see the
top-level [`SUMMARY.md`](../SUMMARY.md) — that ordering is close enough to
the repeat-to-repeat spread that it shouldn't be read as settled either
way), and the checker loop remains the **most expensive and least
consistent** of the three real skills regardless — the loop itself is a
source of run-to-run variance (how many issues it happens to catch, how
many fix attempts it takes) that a higher mean score, on sweeps where it
has one, doesn't offset. See
[`progressive_disclosure.md`](progressive_disclosure.md) for a transcript
excerpt showing both halves: reference reads before writing code, then a
targeted checker-driven fix pass after.

Curated candidate scripts, renders, and comparator reports for every
invocation are under [`samples/`](samples/), organized `samples/<prompt>/<variant>/`.
