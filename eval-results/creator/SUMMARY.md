# `creator` skill — eval summary

Sweep: `runs/sweep/20260807_080537_creator_6prompts` — 6 corpus prompts x (3
repeats + 1 auto-baseline), Haiku, scored by `runner.comparator.compare()`
against each prompt's ground truth. Full detail in [`metrics.json`](metrics.json).
This sweep's raw run directory has since been deleted (it lived only in an
ephemeral worktree), so its candidates can no longer be re-executed — not
a problem for the update below, since removing a check is a pure point
subtraction that never needed re-execution in the first place (see the
top-level [`SUMMARY.md`](../SUMMARY.md)).

**Comparator methodology (2026-08-09):** 3 checks (hero-column formatting,
stub tint/grey-budget, caption-not-restating-subtitle) were removed from
`runner/comparator.py` — field data across house/prose/scripts showed
every skill variant scoring near-zero on them regardless of quality,
meaning they measured something no current skill achieves rather than a
real quality gap between skills. The candidate set here is **unchanged**
(same sweep, same 24 invocations) — only the scoring rubric changed.
Scores below are **not comparable** to this file's pre-2026-08-09 numbers
(denominator shrank 114 -> 106 pts).

| Metric (mean across 6 prompts) | `creator` skill | baseline (no skill) |
|---|---|---|
| Comparator total score | **23.5%** | 26.8% |
| Cost per invocation | $0.095 | $0.073 |
| Score spread across 3 repeats | 18.1 points | n/a (1 run) |

See [`plots/cost.png`](plots/cost.png), [`plots/tokens.png`](plots/tokens.png),
[`plots/consistency.png`](plots/consistency.png),
[`plots/comparator_score.png`](plots/comparator_score.png).

**The headline finding still holds: `creator`'s candidate skill scores
*below* the no-skill baseline**, on average, while still costing more per
invocation. Removing 3 checks nothing could pass moved every skill's score
up somewhat (including baseline's) — `creator` gained the least of the
four (+1.8pp, vs. +2.7 to +4.2pp for `house`/`prose`/`scripts`) and remains
3.3pp behind baseline, essentially unchanged from the 3.0pp gap before this
pass. `creator` mounts a skill-creator-produced candidate skill verbatim
(for A/B evaluation against the promoted `great-tables`/`great-tables-ci`
skills, not because it's expected to win) — this sweep is evidence it
currently isn't competitive, not just underwhelming. See
[`progressive_disclosure.md`](progressive_disclosure.md) for a concrete,
mechanical difference: the transcript still shows the skill being invoked
and reference files being read, just less systematically (skill invoked
*after* the data, `REFERENCE.md`'s own router read second rather than first,
no follow-through into the archetype-specific rules the same prompt sent
`prose`/`scripts` into) — one plausible, falsifiable explanation for the
score gap, not a full diagnosis.

Curated candidate scripts, renders, and comparator reports for every
invocation are under [`samples/`](samples/), organized `samples/<prompt>/<variant>/`.
