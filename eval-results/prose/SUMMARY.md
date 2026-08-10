# `prose` skill — eval summary

Sweep: `runs/sweep/20260809_124545_prose_6prompts` — 6 corpus prompts x (3
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
taste) — the second pass was prompted by asking specifically what `prose`
(this skill, the best performer) still misses. See the top-level
[`SUMMARY.md`](../SUMMARY.md) for the full removal rationale and
cross-skill comparison. Scores below are **not comparable** to this
file's pre-2026-08-09 numbers (denominator shrank 114 -> 97 pts).

| Metric (mean across 6 prompts) | `prose` skill | baseline (no skill) |
|---|---|---|
| Comparator total score | **74.9%** | 25.7% |
| Cost per invocation | $0.167 | $0.077 |
| Score spread across 3 repeats | 10.6 points | n/a (1 run) |

See [`plots/cost.png`](plots/cost.png), [`plots/tokens.png`](plots/tokens.png),
[`plots/consistency.png`](plots/consistency.png),
[`plots/comparator_score.png`](plots/comparator_score.png).

`prose` is the best performer of the four: the **highest mean comparator
score** (roughly 3x baseline) *and* the **most consistent** (smallest
repeat-to-repeat spread) — the 7-step flowchart + `REFERENCE.md` router
gets the model to the same design decisions run after run, without a
checker loop's added cost or variance. See
[`progressive_disclosure.md`](progressive_disclosure.md) for a transcript
excerpt of the router-driven reference reads (router -> data -> the specific
archetype rules this prompt's two measures needed) that precede every write.

Curated candidate scripts, renders, and comparator reports for every
invocation are under [`samples/`](samples/), organized `samples/<prompt>/<variant>/`.
