# `house` skill — eval summary

Sweep: `runs/sweep/20260807_080527_house_6prompts` — 6 corpus prompts x (3
repeats + 1 auto-baseline), Haiku, scored by `runner.comparator.compare()`
against each prompt's ground truth. Full detail in [`metrics.json`](metrics.json).

**Comparator methodology (2026-08-09):** 3 checks (hero-column formatting,
stub tint/grey-budget, caption-not-restating-subtitle) were removed from
`runner/comparator.py` — field data across house/prose/scripts showed
every skill variant scoring near-zero on them regardless of quality,
meaning they measured something no current skill achieves rather than a
real quality gap between skills. The candidate set here is **unchanged**
(same sweep, same 24 invocations) — only the scoring rubric changed; see
the top-level [`SUMMARY.md`](../SUMMARY.md) for the full removal rationale
and cross-skill comparison. Scores below are **not comparable** to this
file's pre-2026-08-09 numbers (denominator shrank 114 -> 106 pts).

| Metric (mean across 6 prompts) | `house` skill | baseline (no skill) |
|---|---|---|
| Comparator total score | **60.4%** | 23.2% |
| Cost per invocation | $0.110 | $0.060 |
| Score spread across 3 repeats | 16.4 points | n/a (1 run) |

See [`plots/cost.png`](plots/cost.png), [`plots/tokens.png`](plots/tokens.png),
[`plots/consistency.png`](plots/consistency.png),
[`plots/comparator_score.png`](plots/comparator_score.png).

The skill scores roughly **2.6x** the baseline's comparator score for about
1.8x the cost — the cheapest of the three real skills (no flowchart, no
checker loop; one worked reference script + a rules file). It still trails
`scripts` under the consensus-tuned comparator (see the top-level
[`SUMMARY.md`](../SUMMARY.md) — the ranking is unchanged from before this
pass). See [`progressive_disclosure.md`](progressive_disclosure.md) for a
real transcript excerpt of the skill being read one layer at a time (data
-> worked example -> rules file) before any code is written.

Curated candidate scripts, renders, and comparator reports for every
invocation are under [`samples/`](samples/), organized `samples/<prompt>/<variant>/`.
