# `scripts` skill — eval summary

Sweep: `runs/sweep/20260809_124542_scripts_6prompts` — 6 corpus prompts x (3
repeats + 1 auto-baseline), Haiku, scored by `runner.comparator.compare()`
against each prompt's ground truth. Full detail in [`metrics.json`](metrics.json);
regenerate the plots below with `python plots/make_plots.py`.

**Comparator methodology (2026-08-09):** 3 checks (hero-column formatting,
stub tint/grey-budget, caption-not-restating-subtitle) were removed from
`runner/comparator.py` — field data across house/prose/scripts showed
every skill variant scoring near-zero on them regardless of quality (7.5%,
14.8%, 24.1% average), meaning they measured something no current skill
achieves rather than a real quality gap between skills. Scores below are
**not comparable** to this file's pre-2026-08-09 numbers (denominator
shrank 114 -> 106 pts).

| Metric (mean across 6 prompts) | `scripts` skill | baseline (no skill) |
|---|---|---|
| Comparator total score | **63.2%** | 27.3% |
| Cost per invocation | $0.175 | $0.090 |
| Score spread across 3 repeats | 22.8 points | n/a (1 run) |

See [`plots/cost.png`](plots/cost.png), [`plots/tokens.png`](plots/tokens.png),
[`plots/consistency.png`](plots/consistency.png),
[`plots/comparator_score.png`](plots/comparator_score.png).

`great-tables-ci` is the same 7-step-flowchart skill as `prose` plus a
mechanical checker loop (`gt_check.py`) it runs and fixes against before
finishing. Under the old comparator that loop pushed the mean score above
`house`'s; under the consensus-tuned comparator it no longer does —
`scripts` now trails `house` (see the top-level [`SUMMARY.md`](../SUMMARY.md)) —
while remaining the **most expensive and least consistent** of the three
real skills: the checker loop itself is a source of run-to-run variance
(how many issues it happens to catch, how many fix attempts it takes). See
[`progressive_disclosure.md`](progressive_disclosure.md) for a transcript
excerpt showing both halves: reference reads before writing code, then a
targeted checker-driven fix pass after.

Curated candidate scripts, renders, and comparator reports for every
invocation are under [`samples/`](samples/), organized `samples/<prompt>/<variant>/`.
