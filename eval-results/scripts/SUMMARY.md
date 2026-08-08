# `scripts` skill — eval summary

Sweep: `runs/sweep/20260808_102053_scripts_6prompts` (post skill-content-fix
re-sweep, 2026-08-08) — 6 corpus prompts x (3 repeats + 1 auto-baseline),
Haiku, scored by `runner.comparator.compare()` against each prompt's ground
truth. Full detail in [`metrics.json`](metrics.json); regenerate the plots
below with `python plots/make_plots.py`.

| Metric (mean across 6 prompts) | `scripts` (2026-08-07) | `scripts` (2026-08-08, after fixes) | baseline |
|---|---|---|---|
| Comparator total score | 65.0% | 52.7% | 21.3% |
| Cost per invocation | $0.188 | $0.164 | $0.083 |

**Read this drop with real skepticism before treating it as a regression.**
The 2026-08-08 re-sweep also caught and fixed a genuine, PRE-EXISTING bug
unrelated to any content change: every one of the 6 worked archetype
examples (`assets/examples/*/*.py`, shared with `prose`) built its final
`GT(...)` chain as a bare, unassigned expression — never `gt = (...)` — so a
candidate that closely copied an archetype's structure produced a script
with no top-level `gt` variable, which fails the comparator's Tier-2
introspection entirely and voided most of the Data-compliance score for
that sample. That's fixed now (all 6 examples assign `gt = (...)`). Beyond that
fix, the SAME prompt+skill combination showed 40-65-point swings across its
own 3 repeats in this one sweep (e.g. `airquality_monthly_summary`: 90.5% /
26.4% / 52.4%) — Haiku's per-repeat variance at this sample size is large
enough to dominate a single 3-repeat mean. The content additions made this
same day (pinned date-stub format, the continuous/not-reset-per-group
canonical metric rule, the paired-column-as-one-measure technique, the
two-call source-note convention, backported ambiguous-measure/ranking
guidance) are correctness improvements verifiable on their own terms (see
`house`'s summary for where the SAME additions produced a clean, mechanism-
confirmed win) — but this single re-sweep's aggregate score is not a
reliable read of their net effect on `scripts` specifically. A confident
before/after aggregate for `scripts`/`prose` would need substantially more
than 3 repeats per prompt to average out Haiku's own sampling variance.

See [`plots/cost.png`](plots/cost.png), [`plots/tokens.png`](plots/tokens.png),
[`plots/consistency.png`](plots/consistency.png),
[`plots/comparator_score.png`](plots/comparator_score.png).

**The paragraph below describes the 2026-08-07 sweep**, where this was
true; it is NOT re-confirmed against the 2026-08-08 numbers above (`scripts`
scored below `prose` in that re-sweep, for the noisy reasons explained
above — not read as a reversal of this mechanism either).

`great-tables-ci` is the same 7-step-flowchart skill as `prose` plus a
mechanical checker loop (`gt_check.py`) it runs and fixes against before
finishing. On 2026-08-07 that loop pushed the mean score above `prose`'s,
but also made this the **most expensive and least consistent** of the three
real skills — the checker loop itself is a source of run-to-run variance
(how many issues it happens to catch, how many fix attempts it takes). See
[`progressive_disclosure.md`](progressive_disclosure.md) for a transcript
excerpt showing both halves: reference reads before writing code, then a
targeted checker-driven fix pass after.

Curated candidate scripts, renders, and comparator reports for every
invocation are under [`samples/`](samples/), organized `samples/<prompt>/<variant>/`.
