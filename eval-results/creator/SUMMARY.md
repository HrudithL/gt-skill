# `creator` skill — eval summary

Sweep: `runs/sweep/20260807_080537_creator_6prompts` — 6 corpus prompts x (3
repeats + 1 auto-baseline), Haiku, scored by `runner.comparator.compare()`
against each prompt's ground truth. Full detail in [`metrics.json`](metrics.json).
This sweep's raw run directory has since been deleted (it lived only in an
ephemeral worktree), so its candidates can no longer be re-executed — not
a problem for either consensus-tuning update below, since removing a
check is a pure point subtraction that never needed re-execution in the
first place (see the top-level [`SUMMARY.md`](../SUMMARY.md)). Unlike
`house`/`prose`/`scripts` (each refreshed to a 2026-08-09 sweep — see the
top-level file's "Data refresh" section), `creator` has no fresher sweep
to refresh to; the numbers below are still on 2026-08-07 data.

**Comparator methodology (2026-08-09, 2 passes):** 6 checks were removed
from `runner/comparator.py` — 3 uniformly near-zero across every skill
(hero-column formatting, stub tint/grey-budget, caption-not-restating-
subtitle), then 3 more flat/non-discriminating across every skill (title/
subtitle/caption/source presence, subtitle quality, color theme/palette
taste). The candidate set here is **unchanged** (same sweep, same 24
invocations) — only the scoring rubric changed. Scores below are **not
comparable** to this file's pre-2026-08-09 numbers (denominator shrank
114 -> 97 pts).

| Metric (mean across 6 prompts) | `creator` skill | baseline (no skill) |
|---|---|---|
| Comparator total score | **21.7%** | 24.9% |
| Cost per invocation | $0.095 | $0.073 |
| Score spread across 3 repeats | 18.1 points | n/a (1 run) |

See [`plots/cost.png`](plots/cost.png), [`plots/tokens.png`](plots/tokens.png),
[`plots/consistency.png`](plots/consistency.png),
[`plots/comparator_score.png`](plots/comparator_score.png).

**The headline finding still holds: `creator`'s candidate skill scores
*below* the no-skill baseline**, on average, while still costing more per
invocation — its margin behind baseline has stayed roughly flat across
both passes (-3.0pp originally, -3.3pp after pass 1, -3.2pp now) while its
own absolute score actually dipped (21.7%→23.5%→21.7%), the only skill of
the four that didn't net-improve. That's because `creator`'s few
relative strengths were concentrated almost entirely in checks pass 2 just
removed for not discriminating skill quality at all (it scored 50-67% on
those three specifically, well above its own ~22% average) — once those
are gone, what's left is disproportionately the checks it's genuinely bad
at. `creator` mounts a skill-creator-produced candidate skill verbatim
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
