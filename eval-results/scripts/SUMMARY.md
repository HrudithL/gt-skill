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

**Comparator bug fixes (2026-08-11):** two bugs were fixed, both of which
happened to affect this skill more than the others.
1. `check_render_mechanics` was scoring 0/2 for every candidate that
   renders via a bare `finalize(gt, ...)` statement rather than
   `gt = gt.gtsave(...)` — a comparator detection bug (7 of this skill's
   24 invocations used that pattern).
2. Separately, `runner/execution_tier.py`/`convergence.py`'s no-render
   stub for `GT.gtsave`/`GT.save` returned `None` instead of `self`,
   breaking the `gt = gt.gtsave(...)` *reassignment* idiom specifically —
   `towny_growth_trends/repeat_1`'s candidate used exactly that idiom,
   so it failed Tier-2 execution entirely (scored 21/81, 25.9%) even
   though its rendered PNG was completely fine. Fixed; that invocation
   now scores normally.

Numbers below reflect both fixes. See the top-level
[`SUMMARY.md`](../SUMMARY.md) for the full root-cause writeups.

| Metric (mean across 6 prompts) | `scripts` skill | baseline (no skill) |
|---|---|---|
| Comparator total score | **66.2%** | 24.7% |
| Cost per invocation | $0.175 | $0.090 |
| Score spread across 3 repeats | 16.9 points | n/a (1 run) |

See [`plots/cost.png`](plots/cost.png), [`plots/tokens.png`](plots/tokens.png),
[`plots/consistency.png`](plots/consistency.png),
[`plots/comparator_score.png`](plots/comparator_score.png).

`great-tables-ci` is the same 7-step-flowchart skill as `prose` plus a
mechanical checker loop (`gt_check.py`) it runs and fixes against before
finishing. Fixing `towny_growth_trends/repeat_1`'s spurious execution
failure did more than raise this skill's mean — it removed the single
biggest outlier dragging down its own consistency, so `scripts` is no
longer the least consistent of the three real skills (16.9pp spread,
between `prose`'s 10.6pp and `house`'s 18.2pp — see the top-level
[`SUMMARY.md`](../SUMMARY.md)). It remains the **most expensive** of the
three regardless, and still trails `house` on mean score by a narrow,
sweep-dependent margin. See
[`progressive_disclosure.md`](progressive_disclosure.md) for a transcript
excerpt showing both halves: reference reads before writing code, then a
targeted checker-driven fix pass after.

Curated candidate scripts, renders, and comparator reports for every
invocation are under [`samples/`](samples/), organized `samples/<prompt>/<variant>/`.
