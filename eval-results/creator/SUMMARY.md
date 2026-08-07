# `creator` skill — eval summary

Sweep: `runs/sweep/20260807_080537_creator_6prompts` — 6 corpus prompts x (3
repeats + 1 auto-baseline), Haiku, scored by `runner.comparator.compare()`
against each prompt's ground truth. Full detail in [`metrics.json`](metrics.json);
regenerate the plots below with `python plots/make_plots.py`.

| Metric (mean across 6 prompts) | `creator` skill | baseline (no skill) |
|---|---|---|
| Comparator total score | **21.7%** | 24.7% |
| Cost per invocation | $0.095 | $0.073 |
| Score spread across 3 repeats | 16.7 points | n/a (1 run) |

See [`plots/cost.png`](plots/cost.png), [`plots/tokens.png`](plots/tokens.png),
[`plots/consistency.png`](plots/consistency.png),
[`plots/comparator_score.png`](plots/comparator_score.png).

**The headline finding: `creator`'s candidate skill scores *below* the
no-skill baseline**, on average, while still costing more per invocation.
`creator` mounts a skill-creator-produced candidate skill verbatim (for A/B
evaluation against the promoted `great-tables`/`great-tables-ci` skills, not
because it's expected to win) — this sweep is evidence it currently isn't
competitive, not just underwhelming. See
[`progressive_disclosure.md`](progressive_disclosure.md) for a concrete,
mechanical difference: the transcript still shows the skill being invoked
and reference files being read, just less systematically (skill invoked
*after* the data, `REFERENCE.md`'s own router read second rather than first,
no follow-through into the archetype-specific rules the same prompt sent
`prose`/`scripts` into) — one plausible, falsifiable explanation for the
score gap, not a full diagnosis.

Curated candidate scripts, renders, and comparator reports for every
invocation are under [`samples/`](samples/), organized `samples/<prompt>/<variant>/`.
