# `creator` skill — eval summary

Sweep: `runs/sweep/20260807_080537_creator_6prompts` (the ephemeral worktree
that produced this sweep's raw run data has since been deleted post-merge;
scores were recomputed directly against the already-curated
`samples/<prompt>/<variant>/table.py` files below, and cost/token figures
are carried over unchanged from the original sweep since that data can no
longer be re-derived) — 6 corpus prompts x (3 repeats + 1 auto-baseline),
Haiku, scored by `runner.comparator.compare()` against each prompt's ground
truth. Full detail in [`metrics.json`](metrics.json).

**Comparator methodology (2026-08-09):** 3 checks (hero-column formatting,
stub tint/grey-budget, caption-not-restating-subtitle) were removed from
`runner/comparator.py` — field data across house/prose/scripts showed
every skill variant scoring near-zero on them regardless of quality (7.5%,
14.8%, 24.1% average), meaning they measured something no current skill
achieves rather than a real quality gap between skills. Scores below are
**not comparable** to this file's pre-2026-08-09 numbers (denominator
shrank 114 -> 106 pts).

| Metric (mean across 6 prompts) | `creator` skill | baseline (no skill) |
|---|---|---|
| Comparator total score | **18.3%** | 16.7% |
| Cost per invocation | $0.095 | $0.073 |
| Score spread across 3 repeats | 3.3 points | n/a (1 run) |

See [`plots/cost.png`](plots/cost.png), [`plots/tokens.png`](plots/tokens.png),
[`plots/consistency.png`](plots/consistency.png),
[`plots/comparator_score.png`](plots/comparator_score.png).

**The headline finding still holds, even after removing the 3 checks
everyone struggled with: `creator` doesn't meaningfully beat the no-skill
baseline** (+1.6pp on average, versus `house`/`prose`/`scripts`' +36 to
+47pp) — a margin well inside the noise of a 3-repeat sample, while still
costing more per invocation than baseline. `creator` mounts a
skill-creator-produced candidate skill verbatim (for A/B evaluation against
the promoted `great-tables`/`great-tables-ci` skills, not because it's
expected to win) — this sweep is evidence it currently isn't competitive,
not just underwhelming. See
[`progressive_disclosure.md`](progressive_disclosure.md) for a concrete,
mechanical difference: the transcript still shows the skill being invoked
and reference files being read, just less systematically (skill invoked
*after* the data, `REFERENCE.md`'s own router read second rather than first,
no follow-through into the archetype-specific rules the same prompt sent
`prose`/`scripts` into) — one plausible, falsifiable explanation for the
score gap, not a full diagnosis.

Curated candidate scripts, renders, and comparator reports for every
invocation are under [`samples/`](samples/), organized `samples/<prompt>/<variant>/`.
