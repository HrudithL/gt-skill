# `scripts` skill — eval summary

Sweep: `runs/sweep/20260807_080530_scripts_6prompts` — 6 corpus prompts x (3
repeats + 1 auto-baseline), Haiku, scored by `runner.comparator.compare()`
against each prompt's ground truth. Full detail in [`metrics.json`](metrics.json);
regenerate the plots below with `python plots/make_plots.py`.

| Metric (mean across 6 prompts) | `scripts` skill | baseline (no skill) |
|---|---|---|
| Comparator total score | **65.0%** | 22.9% |
| Cost per invocation | $0.188 | $0.089 |
| Score spread across 3 repeats | 22.1 points | n/a (1 run) |

See [`plots/cost.png`](plots/cost.png), [`plots/tokens.png`](plots/tokens.png),
[`plots/consistency.png`](plots/consistency.png),
[`plots/comparator_score.png`](plots/comparator_score.png).

`great-tables-ci` is the same 7-step-flowchart skill as `prose` plus a
mechanical checker loop (`gt_check.py`) it runs and fixes against before
finishing. That loop pushes the mean score above `prose`... but also makes
this the **most expensive and least consistent** of the three real skills —
the checker loop itself is a source of run-to-run variance (how many issues
it happens to catch, how many fix attempts it takes). See
[`progressive_disclosure.md`](progressive_disclosure.md) for a transcript
excerpt showing both halves: reference reads before writing code, then a
targeted checker-driven fix pass after.

Curated candidate scripts, renders, and comparator reports for every
invocation are under [`samples/`](samples/), organized `samples/<prompt>/<variant>/`.
