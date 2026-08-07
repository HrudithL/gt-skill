# `prose` skill — eval summary

Sweep: `runs/sweep/20260807_080533_prose_6prompts` — 6 corpus prompts x (3
repeats + 1 auto-baseline), Haiku, scored by `runner.comparator.compare()`
against each prompt's ground truth. Full detail in [`metrics.json`](metrics.json);
regenerate the plots below with `python plots/make_plots.py`.

| Metric (mean across 6 prompts) | `prose` skill | baseline (no skill) |
|---|---|---|
| Comparator total score | **70.5%** | 24.8% |
| Cost per invocation | $0.150 | $0.082 |
| Score spread across 3 repeats | 11.1 points | n/a (1 run) |

See [`plots/cost.png`](plots/cost.png), [`plots/tokens.png`](plots/tokens.png),
[`plots/consistency.png`](plots/consistency.png),
[`plots/comparator_score.png`](plots/comparator_score.png).

`prose` is the best performer of the four: the **highest mean comparator
score** (nearly 3x baseline) *and* the **most consistent** (smallest
repeat-to-repeat spread) — the 7-step flowchart + `REFERENCE.md` router
gets the model to the same design decisions run after run, without a
checker loop's added cost or variance. See
[`progressive_disclosure.md`](progressive_disclosure.md) for a transcript
excerpt of the router-driven reference reads (router -> data -> the specific
archetype rules this prompt's two measures needed) that precede every write.

Curated candidate scripts, renders, and comparator reports for every
invocation are under [`samples/`](samples/), organized `samples/<prompt>/<variant>/`.
