# `prose` skill — eval summary

Sweep: `runs/sweep/20260809_124545_prose_6prompts` — 6 corpus prompts x (3
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

| Metric (mean across 6 prompts) | `prose` skill | baseline (no skill) |
|---|---|---|
| Comparator total score | **74.8%** | 27.9% |
| Cost per invocation | $0.167 | $0.077 |
| Score spread across 3 repeats | 10.4 points | n/a (1 run) |

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
