# `house` skill — eval summary

Sweep: `runs/sweep/20260812_212028_house_6prompts` — 6 corpus prompts x (3
repeats + 1 auto-baseline), Haiku, scored by `runner.comparator.compare()`
against each prompt's ground truth. Full detail in [`metrics.json`](metrics.json).

**This is the third and final sweep round, run after three landed fixes,
in order:** (1) the skill-realignment + comparator-generalization effort
(PRs #93–#101 — redesigned ground truths, removed the ≤2-measure cap on
colored-measure credit, made the header band/stub tint fixed-and-universal,
made striping apply by default); (2) the `runner/convergence.py`
Header-branding/Stub-tint parsing fix (PR #102 — fixed misreading comments
as calls, taking the first matching call instead of the last, and a
hue-defaulting bug that made a correctly-styled header score as missing);
and (3) the `hairlines`/`finalize` helper-detection fix (PR #103 — see
below). All three landed on `main` before this sweep ran. **This
supersedes round 2's numbers for the same reason round 2 superseded round
1: a real scoring bug got fixed, not a skill change** — there is no valid
"before → after %" to compute across rounds in general (see the top-level
[`SUMMARY.md`](../SUMMARY.md)), except for the two specific checks PR #103
fixed, where a same-candidate-same-comparator-otherwise comparison IS
meaningful — see the callout immediately below.

## The two round-2 comparator gaps are now fixed (PR #103) — verified directly

Round 2 found, but did not fix, two comparator false negatives specific to
`house`'s "opaque imported helper" idiom (`from house_table import frame,
hairlines, finalize, ...`, called as pre-written helpers the comparator
can't see inside): `_hairlines_present` didn't recognize a bare
`hairlines(gt)` call at all (scoring it as missing regardless), and the
render-target check didn't know `finalize(gt, path="table.png", ...)`'s own
default `path` argument (scoring a bare `finalize(gt)` as not rendering
`table.png`). Both are fixed in `runner/comparator.py` as of PR #103, and
this sweep's own data confirms it directly (same skill, same worked-example
idiom, different comparator):

| Check | Round 2 (pre-fix) | Round 3 (post-fix) |
|---|---|---|
| Frame + hairlines + dividers | 18/18 (100%) fail/partial, mean 53.7% | **7/18 (39%) fail/partial, mean 85.2%** |
| Render mechanics (zoom/expand fit-order rule) | 10/18 (56%) fail, mean 44.4% | **1/18 (6%) fail, mean 94.4%** |

Every one of the remaining 7 `Frame + hairlines + dividers` failures now
reads `hairlines=OK` — the sole exception is one invocation with a
separate, already-known cause (see below). 6 of those 7 fail only on
`dividers=expected=True (gated on spanners), got=False`, a distinct,
narrower rule (divider placement gated on column-group spanners) unrelated
to the two fixed bugs. The one remaining `Render mechanics` failure is
`airquality_monthly_summary/repeat_1`, whose entire table-building pipeline
is wrapped in a `def build_table():` only called under
`if __name__ == "__main__":` — the comparator's static exported-scope walk
doesn't trace into it (the exact same shape as round 2's
`towny_growth_trends/repeat_1` outlier, already documented as a distinct,
narrower parsing gap, out of scope here). The candidate's own `table.png`
rendered fine when the harness actually ran it as a script; this is a
comparator-side false negative on this one repeat, not a real render
failure.

| Metric (mean across 18 scored invocations) | `house` skill | baseline (no skill) |
|---|---|---|
| Comparator total score | **79.4%** | 14.0% |
| Data-compliance split | 74.7% (614/822 pts) | — |
| Formatting-compliance split | 84.8% (668/788 pts) | — |
| Cost per invocation | $0.134 | $0.080 |
| Repeat-to-repeat spread (mean across 6 prompts) | 18.1 points | n/a (1 run) |

See [`plots/usage.png`](plots/usage.png),
[`plots/consistency.png`](plots/consistency.png),
[`plots/comparator_score.png`](plots/comparator_score.png).

`house` remains the cheapest of the three real skills by a wide margin
($0.134/invocation vs. $0.182 for `prose` and $0.184 for `scripts` — no
flowchart, no checker loop) — and, with its two comparator gaps now fixed,
its 79.4% mean actually edges out `prose`'s 79.0% on this sweep (see the
top-level `SUMMARY.md`), matching what round 2's estimate expected once
the gaps were closed.

**`sp500_monthly_performance` is `house`'s hardest prompt once one known
outlier is set aside.** Raw per-prompt means: `gtcars_top10_by_country`
97.2%, `islands_sizes` 94.0%, `gtcars_hp_price` 92.9%, `towny_growth_trends`
78.3%, `sp500_monthly_performance` 60.1%, `airquality_monthly_summary`
53.9%. Taken at face value, `airquality_monthly_summary` is lowest — but
that's entirely driven by the one `repeat_1` function-wrapping false
negative described above (18.2% for that single repeat); its other two
repeats average 71.8%. Excluding that one known-gap repeat,
`sp500_monthly_performance` (60.1%) is `house`'s hardest prompt, consistent
with `prose`, `scripts`, and every round of this corpus so far.

## What the comparator still fails `house` on

Computed across the 18 scored (non-baseline) invocations, sorted by how
often each check fails or partially fails (checks with 0 possible points
for a given invocation, e.g. gated-off color checks, are excluded from that
check's denominator):

1. **Title quality (judge)** — 5/6 (83%) fail or partially fail, mean
   72.2%, on `islands_sizes` only (the one prompt with no colored measure to
   otherwise differentiate).
   - `[islands_sizes/repeat_2]` "judge score 3/5 -- The candidate's title
     'Island Sizes' is accurate but generic, whereas the ground truth's
     'Islands of the World, by Size' more explicitly establishes the
     comprehensive scope and framing."
2. **Caption keyword coverage** — 15/18 (83%) fail or partially fail, mean
   66.7%.
   - `[gtcars_hp_price/repeat_1]` "3/6 caption-keyword rules satisfied;
     caption missing: ['bentley', 'corvette', "don't move together"]" —
     the same specific-outlier-naming gap seen across all three skills on
     this exact prompt (see top-level `SUMMARY.md`).
3. **Signed-percent force_sign correctness** — 5/6 (83%) fail, mean 16.7%,
   always a full miss.
   - `[sp500_monthly_performance/repeat_1]` "0/1 signed percent columns use
     force_sign=True; missing/wrong on: ['pct_change']" — a
     diverging (crosses-zero) percent column rendered without an explicit
     `+` sign on positive values.
4. **Column set shown vs. hidden** — 12/18 (67%) fail or partially fail,
   mean 54.2%.
   - `[airquality_monthly_summary/repeat_2]` "visible-column overlap 0.14
     (candidate-only=['ozone', 'temp', 'wind'], missing=['avg_ozone',
     'avg_temp', 'avg_wind'])" — a rename the matcher can't reconcile.
5. **Column order quality (judge)** — 3/5 (60%) fail or partially fail,
   mean 60.0%.
   - `[islands_sizes/repeat_1]` "judge score 1/5 -- The candidate presents
     columns in an essentially arbitrary alphabetical order ... whereas the
     ground truth orders by descending size ... This alphabetical ordering
     directly contradicts the analytical goal."
6. **Colored-measure selection** — 10/18 (56%) fail or partially fail, mean
   49.1%.
   - `[gtcars_hp_price/repeat_1]` "0/1 canonical colored measures covered by
     a candidate color call" — the hero measure never gets `heatmap(gt,
     ...)` applied at all.
7. **fmt_\* per column semantic type** — 9/18 (50%) fail or partially fail,
   mean 59.7%, and **Computed/derived value correctness** — 9/18 (50%),
   mean 63.3% — both concentrated on the same `airquality_monthly_summary`
   repeats, where the candidates' aggregate columns don't value-match the
   ground truth's canonical measures.
8. **Stub tint (washed navy)** — 6/18 (33%) fail or partially fail, mean
   66.7%.
   - `[airquality_monthly_summary/repeat_1]` "expected #EAF0F6, got None" —
     one of several misses concentrated on invocations that also drop the
     stub column or fail Tier-2 execution.

`Header branding` (6% fail, mean 94.4%) and `Striping gate correctness`
(6% fail, mean 94.4%) both continue to score well — the mandatory
`band(...)`/`stripe(...)` helpers are correctly detected by name, and
`hairlines(...)` now joins them at a comparably high pass rate (see the
before/after table above), confirming both the `convergence.py` parsing fix
(PR #102) and the helper-detection fix (PR #103) are working as intended.

See [`progressive_disclosure.md`](progressive_disclosure.md) for a real
transcript excerpt of the skill being read one layer at a time (data ->
worked example -> rules file) before any code is written. (That excerpt
predates this sweep — it illustrates the reading pattern, not this round's
scores.)

Curated candidate scripts, renders, and comparator reports for every
invocation are under [`samples/`](samples/), organized `samples/<prompt>/<variant>/`.

## Round 4 (2026-08-13) — dtype footgun + comparator blind spots fixed

Fresh sweep (`runs/sweep/20260813_080322_house_6prompts`), run after `main` had all
five rounds of fixes merged: `RULES.md`'s `np.where(...)` baseline-guard snippet used
`None` instead of `np.nan` (forced `object` dtype, broke `.nlargest()` — caused a real
2x token blowup in an earlier sweep); the comparator's static AND execution-tier
extractors now both recognize a `def build_table(): ... if __name__=="__main__":`-wrapped
script as inlined top-level code (previously invisible to either).

| Metric | This round | Round 3 |
|---|---|---|
| Mean score | **82.4%** | 79.4% |
| Mean repeat spread | 16.0pp | 18.1pp |
| Mean cost | $0.131 | $0.134 |

Per-prompt means: `gtcars_hp_price` 94.1%, `islands_sizes` 94.4%, `gtcars_top10_by_country`
89.3%, `sp500_monthly_performance` 73.6%, `airquality_monthly_summary` 71.7%,
`towny_growth_trends` 71.4%. Two individual repeats scored far below their siblings
this round, both traced to the same one-off mistake, not a bug: `towny_growth_trends/
repeat_1` (38.4% vs. 85–90% siblings) used `.set_index('Town')` instead of passing
`rowname_col="Town"` to `GT(...)`, so no stub was ever created; `sp500_monthly_
performance` also runs into the known month-label-format ambiguity (see top-level
`SUMMARY.md`). Both are places `RULES.md`/the worked example already teach the correct
pattern and the other 2 of 3 repeats on the same prompt did it right — haiku-tier
sampling variance on a small sample, not a skill or comparator gap. (A doc fix for
this exact `set_index()`-vs-`rowname_col=` confusion has since landed, PR #107.)
