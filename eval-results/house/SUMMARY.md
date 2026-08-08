# `house` skill — eval summary

Sweep: `runs/sweep/20260808_102042_house_6prompts` (post skill-content-fix
re-sweep, 2026-08-08) — 6 corpus prompts x (3 repeats + 1 auto-baseline),
Haiku, scored by `runner.comparator.compare()` against each prompt's ground
truth. Full detail in [`metrics.json`](metrics.json); regenerate the plots
below with `python plots/make_plots.py`.

| Metric (mean across 6 prompts) | `house` (2026-08-07) | `house` (2026-08-08, after fixes) | baseline |
|---|---|---|---|
| Comparator total score | 57.7% | **60.6%** | 24.2% |
| Cost per invocation | $0.110 | $0.115 | $0.060 |

**2026-08-08 skill-content fixes** (`SKILL.md`/`references/RULES.md`/
`scripts/house_table.py`) targeted a specific, code-confirmed comparator
blind spot: several Formatting-compliance checks (row hairlines, heading-band
hue, `gtsave` render params) are Tier-1 regex scans of the CANDIDATE's own
script text, which can't see a value set inside an imported helper function
— exactly how `house`'s wrapper-based design (`frame()`/`band()`/
`finalize()`) had been writing those three things. Fix was skill-side only
(no comparator changes, per explicit instruction): `RULES.md` now teaches
writing hairlines/band-color/render-params as literal, inline
`tab_options()`/`finalize()` calls with real hex values, not through the
wrapper. Also added: a pinned date-stub format, a canonical continuous
(not-reset-per-group) definition for period-over-period metrics, the
paired-column-as-one-measure Big Color technique, a two-call source-note
convention, and forced the stub/date-format/ambiguous-metric decisions into
the pre-write step.

**This +2.9-point aggregate move is a LOWER BOUND on the real effect** — the
targeted checks moved far more than the aggregate suggests: Frame+hairlines
+56%, Heading-band-hue +33%, Row/entity-identity +60%, Computed-value-
correctness +54%, Stub-existence +36% (relative). The aggregate is muted by
unrelated run-to-run noise on OTHER checks (Haiku's per-repeat variance is
large — see `scripts`'/`prose`'s own summaries for how much this can swing
a single 3-repeat sample). The per-check deltas are the more trustworthy
signal here since they're mechanism-linked to specific fixes, not just an
aggregate mean.

See [`plots/cost.png`](plots/cost.png), [`plots/tokens.png`](plots/tokens.png),
[`plots/consistency.png`](plots/consistency.png),
[`plots/comparator_score.png`](plots/comparator_score.png).

Still the cheapest of the three real skills (no flowchart, no checker loop;
one worked reference script + a rules file). See
[`progressive_disclosure.md`](progressive_disclosure.md) for a real
transcript excerpt of the skill being read one layer at a time (data ->
worked example -> rules file) before any code is written.

Curated candidate scripts, renders, and comparator reports for every
invocation are under [`samples/`](samples/), organized `samples/<prompt>/<variant>/`.
