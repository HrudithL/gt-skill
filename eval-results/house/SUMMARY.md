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

See [`plots/usage.png`](plots/usage.png) and
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
| Mean score | **83.3%** | 79.4% |
| Mean repeat spread | 16.4pp | 18.1pp |
| Mean cost | $0.131 | $0.134 |

**RESOLVED (2026-08-13, `chore/recompute-eval-results-post-fixes`):** the
figures above (83.3% / 16.4pp) are the final, fully-recomputed numbers,
after the deferred `normalize_id` date-matching fix and the
`check_caption_not_generic` redesign were both applied to this round's
actual committed candidates. They supersede an earlier, briefly-committed
82.4% / 16.0pp reading of this same sweep that predated that recompute.
`house`'s number moved the least of the three skills (+0.9pp) because its
`sp500_monthly_performance` candidates already rendered month labels in
the ground truth's date format, so only the broader caption-check fix
touched it — see the top-level `SUMMARY.md` for the full three-skill
picture and the ranking this settles.

Per-prompt means: `gtcars_hp_price` 95.3%, `islands_sizes` 94.0%, `gtcars_top10_by_country`
89.3%, `sp500_monthly_performance` 75.8%, `airquality_monthly_summary` 72.8%,
`towny_growth_trends` 72.5%. Two individual repeats scored far below their siblings
this round, both traced to the same one-off mistake, not a bug: `towny_growth_trends/
repeat_1` (39.5% vs. 86–91% siblings) used `.set_index('Town')` instead of passing
`rowname_col="Town"` to `GT(...)`, so no stub was ever created; `sp500_monthly_
performance` also runs into the known month-label-format ambiguity (see top-level
`SUMMARY.md`). Both are places `RULES.md`/the worked example already teach the correct
pattern and the other 2 of 3 repeats on the same prompt did it right — haiku-tier
sampling variance on a small sample, not a skill or comparator gap. (A doc fix for
this exact `set_index()`-vs-`rowname_col=` confusion has since landed, PR #107.)

## Round 5 (2026-08-13) — verification sweep, no new code changes

A second, independent 6-prompt sweep (`runs/sweep/20260813_161436_house_6prompts`)
against the exact same commit round 4's numbers above were computed from — checking
whether round 4's results (and its one catastrophic single-repeat outlier) hold up
under a fresh random draw. No code changed between round 4 and this round.

| Metric | This round | Round 4 |
|---|---|---|
| Mean score | 83.5% | 83.3% |
| Mean repeat spread | **8.9pp** | 16.4pp |
| Mean cost | $0.133 | $0.131 |

**Note:** round 4 and round 5 are not scored on an identical basis — 12 of
round 4's 18 invocations had all judge-tier checks marked N/A, vs. 0 of 18
this round; see the top-level [`SUMMARY.md`](../SUMMARY.md) for the full
disclosure and a confound-free, mechanical-only recomputation.

Mean score is flat (+0.2pp, within noise for an 18-invocation haiku sample). Mean
repeat spread improved substantially, driven almost entirely by
`towny_growth_trends` no longer producing a catastrophic outlier (see below).

Per-prompt means: `gtcars_hp_price` 97.4%, `gtcars_top10_by_country` 95.1%,
`islands_sizes` 85.4%, `sp500_monthly_performance` 77.7%, `towny_growth_trends`
73.4%, `airquality_monthly_summary` 72.2%.

**`towny_growth_trends`'s catastrophic outlier does not recur, but the fix is
narrower than it first looks, and the specific colored-measure check this table
was designed to exercise is actually worse this round, not better.** Round 4's
`repeat_1` scored 39.5%, and re-reading its actual stored report shows the
dominant cause was a *different*, already-separately-fixed bug: it built
`GT(gt_data.set_index('Town'))` instead of `rowname_col="Town"`, so no stub
existed at all, zeroing the three strictly stub-gated checks — row/entity
selection identity, computed/derived value correctness, and stub existence
(22 of the 52 total points lost, ~42%, a **minority** of the loss). Column
set shown vs. hidden, striping, and header branding were **not** stub
cascades: the report attributes them directly to separate candidate
omissions (e.g. "header background: expected #08306B, got None"), and
reading the candidate's actual `table.py` confirms it has no
`opt_row_striping` call and no `#08306B` anywhere in the script — these are
independent misses the candidate also made, not a consequence of the
missing stub. (PR #107 fixed the `set_index()`-vs-`rowname_col=` confusion
itself.)

This round's three fresh repeats score `[71.1%, 70.6%, 78.4%]` — clustered, no
catastrophic outlier. Reading all three `table.py` files confirms all three now
build the stub with `rowname_col=` (not `.set_index()`), so that specific,
previously-primary bug is confirmed fixed. But on the "Colored-measure selection"
check itself — 11 canonical colored measures: 6 `density_*` (sequential) + 5
`pop_change_*_pct` (diverging) — coverage regressed, it did not improve:

| | repeat_1 | repeat_2 | repeat_3 |
|---|---|---|---|
| Round 4 | 0/11 (FAIL) | **11/11 (PASS)** | 5/11 (FAIL) |
| Round 5 | 0/11 (FAIL) | 0/11 (FAIL) | 6/11 (FAIL) |

Round 4 had one repeat (`repeat_2`) earn full credit on this check. Round 5's best
repeat (`repeat_3`, 6/11) still fails it outright, and — critically — **all 6 of
its covered measures are the `density_*` columns; none of the 5 canonical
`pop_change_*_pct` measures are covered.** Its own "Computed/derived value
correctness" sub-score confirms this directly: 5/10, listing all five
`pop_change_1996_2001_pct`..`pop_change_2016_2021_pct` measures as unmatched.
`repeat_3` does color both a sequential and a diverging group visually
(`Greens` and `RdYlGn`, per its report), but it is coloring the wrong second
group — density-derived percent-change columns of its own invention, not the
ground truth's `pop_change_*_pct` measures — so it does **not** match the ground
truth's two-colored-measure design, despite superficially looking like it does.
`repeat_1` and `repeat_2` cover zero canonical colored measures each, having
heatmapped only their own density-derived change columns instead.

Across all 3 round-5 repeats, **zero** of the 5 canonical `pop_change_*_pct`
measures were covered by any repeat, versus round 4's one full-credit repeat. So
on this specific mechanical check — the one this prompt was designed to exercise
most directly — round 5 is worse than round 4, not merely "milder" or
"incomplete." The `rowname_col=` stub bug is fixed; the measure-coverage
regression is a separate, unresolved gap this sweep surfaces fresh.

**A second, honest limitation this round: `islands_sizes` also regressed.**
Round 4's `islands_sizes` scored `[91.0%, 92.1%, 98.9%]` (94.0% mean, 7.9pp
spread); this round it scores `[94.4%, 69.7%, 92.1%]` (85.4% mean, 24.7pp
spread) — `repeat_2`'s 69.7% vs. ~92–94% siblings makes this `house`'s
**largest** single-prompt mean-change this round (−8.6pp), not
`towny_growth_trends`'s, which is actually near the bottom of the six
prompts and essentially flat (+0.9pp) despite the narrative attention it
gets above. By mean-change this round vs. round 4: `islands_sizes` −8.6pp
(largest), `gtcars_top10_by_country` +5.8pp, `gtcars_hp_price` +2.2pp,
`sp500_monthly_performance` +1.9pp, `towny_growth_trends` +0.9pp,
`airquality_monthly_summary` −0.6pp (smallest). Not investigated further
here — out of scope for a verification pass that focused on the **three**
round-4 outlier prompts (`house/towny_growth_trends`,
`scripts/gtcars_hp_price`, `scripts/airquality_monthly_summary`) — the
last of which recurred this round under a different cause rather than
newly appearing (see top-level `SUMMARY.md`).

Execution: 24/24 successful (no crashes), consistent with `prose` and `scripts`
this round — see the top-level `SUMMARY.md` for the caveat on why this isn't
claimed as a rigorously-proven improvement over any pre-fix baseline.
