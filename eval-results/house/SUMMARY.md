# `house` skill — eval summary

Sweep: `runs/sweep/20260807_080527_house_6prompts` — 6 corpus prompts x (3
repeats + 1 auto-baseline), Haiku, scored by `runner.comparator.compare()`
against each prompt's ground truth. Full detail in [`metrics.json`](metrics.json);
regenerate the plots below with `python plots/make_plots.py`.

| Metric (mean across 6 prompts) | `house` skill | baseline (no skill) |
|---|---|---|
| Comparator total score | **57.7%** | 21.3% |
| Cost per invocation | $0.110 | $0.060 |
| Score spread across 3 repeats | 15.8 points | n/a (1 run) |

See [`plots/cost.png`](plots/cost.png), [`plots/tokens.png`](plots/tokens.png),
[`plots/consistency.png`](plots/consistency.png),
[`plots/comparator_score.png`](plots/comparator_score.png).

The skill roughly **triples** the baseline's comparator score for about
1.8x the cost — the cheapest of the three real skills (no flowchart, no
checker loop; one worked reference script + a rules file). See
[`progressive_disclosure.md`](progressive_disclosure.md) for a real
transcript excerpt of the skill being read one layer at a time (data ->
worked example -> rules file) before any code is written.

Curated candidate scripts, renders, and comparator reports for every
invocation are under [`samples/`](samples/), organized `samples/<prompt>/<variant>/`.
