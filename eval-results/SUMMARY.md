# Full comparator sweep — cross-skill summary

All four skill variants (`house`, `scripts`, `prose`, `creator`), the same 6
corpus prompts, 3 repeats + an auto-baseline each (96 harness invocations
total), scored by the hybrid deterministic + LLM-judge comparator
(`runner/comparator.py` + `runner/judge.py`).
Per-skill detail, plots, and curated runs are in `house/`, `scripts/`,
`prose/`, `creator/` — see each skill's own `SUMMARY.md`.

**Everything below predates the 2026-08-12 round-3 refresh** (see "Data
refresh (2026-08-12, round 3)" near the end for the current, trustworthy
numbers) **except this sentence and that final section.** It's kept in
place because the methodology history (why checks were removed, what got
fixed and when) is still accurate as a record of what happened — just not
as a source of current `house`/`scripts`/`prose` numbers, all three of
which changed twice more since the sections immediately below were
written (once for the `convergence.py` parsing fix, PR #102, covered
further down as "round 2"; once more for the `hairlines`/`finalize`
helper-detection fix, PR #103, covered in the final "round 3" section).
`creator` was not re-swept in either round (its own raw sweep directory is
gone, per "Data refresh (2026-08-09)" below) and its numbers below remain
the only ones this file has for it.

## Comparator methodology (2026-08-09 — two consensus-tuning passes)

The comparator was originally scored against an idealized standard rather
than against what current skill-guided LLM output actually achieves. Two
passes removed 6 checks total, for two related but distinct reasons.

**Pass 1 — uniformly near-zero across every skill.** Checking per-check
pass rates across `house`/`prose`/`scripts`'s 18 non-baseline invocations
each found 3 checks scoring near-zero for *every* skill, not just weak for
one — a true consensus miss, not a quality differentiator:

| Check (removed) | n (non-N/A) | Avg | house | prose | scripts |
|---|---|---|---|---|---|
| Hero-column formatting when nothing is colored | 39/54 | 0.0% | 0.0% | 0.0% | 0.0% |
| Caption doesn't just restate the subtitle (judge) | 52/54 | 3.9% | 0.0% | 11.8% | 0.0% |
| Stub tint + grey-budget correctness | 54/54 | 27.8% | 33.3% | 33.3% | 16.7% |

Two of these three are a genuine near-universal 0 (hero-column, caption).
**Stub tint's real rationale is more specific** — it has real skill-to-skill
spread (16.7%–33.3%) and 15/96 invocations passed it outright; it was
removed because its zeros decompose into two non-discriminating failure
modes: 49/96 are `"ground truth requires a stub but candidate has none"` —
a missing stub, which `check_stub_existence` (kept, unchanged) already
penalizes separately, so failing this check too was double-counting the
same defect; the other 28/96 are a literal grey-budget-violation pattern
(`stub=True, striped=True -> expected tint=False, actual=True`), not really
a tasteful-tinting-choice question.

**Pass 2 — flat/non-discriminating regardless of skill.** Considering
`prose` (the best-performing skill)'s own remaining weakest checks
surfaced a second, different category: not near-zero, but scored almost
*identically* across every skill regardless of which one produced the
candidate — meaning the check doesn't distinguish skill quality at all,
whatever its absolute level:

| Check (removed) | n (non-N/A) | Avg | house | prose | scripts | Spread |
|---|---|---|---|---|---|---|
| Title/subtitle/caption/source presence per gating rules | 54/54 | 65.4% | 66.7% | 63.0% | 66.7% | 3.7pp |
| Subtitle quality (judge) | 53/54 | 61.7% | 61.1% | 61.1% | 62.7% | 1.6pp |
| Color theme/palette taste (judge) | 53/54 | 62.2% | 64.8% | 61.1% | 60.8% | 4.0pp |

(The title/subtitle/caption/source check's flatness is driven almost
entirely by its caption/source-note component — title and subtitle
presence themselves are satisfied in 17/18 `prose` invocations; caption
*quality*, as opposed to presence, was already handled by pass 1's
caption removal.)

**Explicitly NOT removed in pass 2**, despite `prose` also scoring
relatively low on them (numbers below are as computed on the 2026-08-07
sweep the removal decision was actually made on — **not** reproducible
from the refreshed `metrics.json` further down this file, which reflects
a different, later sweep for these same skills; see "Data refresh"
below): `Column-label concept-correctness` (house 55.6%, prose 38.9%,
scripts 41.2% — 16.7pp spread) and `Striping gate correctness` (house
27.8%, prose 38.9%, scripts 55.6% — 27.8pp spread). These showed real
cross-skill variation on that sweep — removing them would have erased
evidence that other skills handled these differently/better than
`prose`, not evidence the check is unreasonable for everyone. Likewise
`Computed/derived value correctness` (house 22.8%, prose 63.3%, scripts
50.6% — 40.6pp spread, the largest of any check on that sweep) stayed:
it was, on that data, exactly the kind of signal this comparator exists
to surface. (On the fresher 2026-08-09 sweep this file's own numbers now
report, this specific check's spread shrinks to 12.8pp and `house` is no
longer the worst performer on it — a reminder that these are per-sweep
snapshots, not fixed properties of a skill, which is also why the
`house`/`scripts` ordering below is called noisy rather than settled.)

Both passes' exact checks and mechanism (full deletion) were confirmed
with the user via AskUserQuestion before any code changed.

**Combined effect**: Formatting-compliance ceiling 61 → 53 → 44 pts.
Data-compliance unaffected throughout. Combined: 114 → 106 → 97 pts.

## Data refresh (2026-08-09, after both passes above)

`house`, `prose`, and `scripts` below are each that skill's most recent
6-prompt sweep — a genuinely fresh harness run (new LLM generation, new
render, new real judge calls), not a re-score of the candidates the two
passes above were validated against. This is a deliberate, separate step
(explicit user request) from the consensus-tuning passes themselves — it
is **not** a re-run of the "hold candidates fixed, change only the
comparator" methodology those passes used to isolate their own effect; it
simply reflects each skill's current state, scored by the current
(24-check, 97-pt) comparator. `creator` is the one exception: its raw
sweep directory no longer exists on disk (the ephemeral worktree it lived
in was deleted after merge), so there is no fresher run available — its
numbers here are still the pure point-subtraction transform (filter the 6
removed checks' points out of each already-scored invocation and re-sum,
no re-execution) applied to `main`'s original 2026-08-07 data, committed
at [`_apply_check_removal.py`](_apply_check_removal.py) for auditability.
One more asymmetry this introduces: `creator`'s 4 surviving judge-backed
checks were scored by the judge's *original* 7-dimension prompt (the
transform only filters which of the 7 stored scores count, it can't
retroactively re-elicit them under the current 4-dimension prompt), while
`house`/`prose`/`scripts`' fresh judge calls this section used the
current 4-dimension prompt directly — `creator`'s numbers are the least
directly comparable to the other three of anything in this file.

| Skill | Mean comparator score | vs. baseline | Score spread (3 repeats) | Mean cost/invocation |
|---|---|---|---|---|
| `prose` | **74.9%** | +49.2pp | **10.6pp** (most consistent) | $0.167 |
| `house` | 69.3% | +42.7pp | 18.2pp (least consistent) | $0.117 |
| `scripts` | 66.1% | +41.4pp | 16.9pp | **$0.175** (most expensive) |
| `creator` | 21.7%\*\* | **-3.2pp** | 18.1pp | **$0.095** (cheapest) |
| baseline (no skill) | 24.7-26.6%\* | — | n/a (1 run) | $0.065-$0.090\* |

\*baseline varies slightly per skill's sweep because each sweep's baseline
run is a separate invocation (same prompts, no skill mounted, different
sampling); `prose`'s and `scripts`' baseline numbers are each additionally
pulled down by one baseline invocation that failed Tier-2 execution (a
`gt_table`-vs-`gt` variable-naming miss, same shape as `creator`'s own
execution failures described in its `SUMMARY.md`) — excluding those,
`prose`'s baseline would read ~28.1% and `scripts`' ~27.8%. See each
skill's `plots/cost.png` / `comparator_score.png` for the per-skill
baseline actually used in that comparison.
\*\*`creator` is on 2026-08-07 data (see above); the other three rows are
the 2026-08-09 sweep as corrected by the 2026-08-11 bug fixes below. Its
cost figure is the only one here that's cheaper than a real skill by
construction of its A/B design, not evidence of efficiency — it's a
candidate skill under evaluation, not a promoted one.

## Comparator and execution-tier bug fixes (2026-08-11)

Two bugs were found and fixed after the data refresh above, both via
internal Opus-tier PR review. Neither changed which candidates were
generated — both are re-scoring fixes against the same 2026-08-09 sweep,
applied by recomputing affected checks (mechanically, or via a fresh
judge call where the underlying execution status genuinely changed) and
substituting the corrected values in place. `house`'s and `scripts`'
numbers above already reflect both fixes; `prose` had zero affected
checks; `creator` is unreachable (see "Data refresh" above) and unaffected
by construction (fixed today, `creator`'s frozen data predates both bugs
either way).

1. **`check_render_mechanics` false negative on bare `finalize(gt, ...)`.**
   The check only recognized `gt = gt.gtsave(...)`-style assignment as
   "rendering the exported table"; a bare `finalize(gt, ...)` statement
   (no assignment) scored 0/2 even though it's a valid, common render
   idiom — `house`'s own worked example teaches exactly this pattern.
   Fixed in `_stmt_targets_name` (`runner/comparator.py`), narrowly: only
   a bare call whose callee is literally `finalize` is treated as
   targeting its first argument — not bare calls generally, which would
   reopen a different false-positive class (e.g. `print(gt)` wrongly
   counting as a render). Affected 16 of `house`'s 18 skill invocations
   and 7 of `scripts`' 18 (its worked example leans on the assignment form
   more often); 0 for `prose` (its worked example uses the assignment form
   exclusively). See
   [`tests/test_render_mechanics_bare_finalize.py`](../tests/test_render_mechanics_bare_finalize.py).
2. **`GT.gtsave`/`GT.save` no-render stubs returned `None` instead of
   `self`.** `runner/execution_tier.py` and `runner/convergence.py` each
   stub these methods out during no-render Tier-1/data-hash execution
   (to avoid actually launching a headless-Chrome render on every
   candidate). The stub returned `None`, breaking the equally-common
   `gt = gt.gtsave(...)` *reassignment* idiom specifically — any
   candidate using it lost its exported `gt` object entirely partway
   through execution. `scripts/towny_growth_trends/repeat_1` hit exactly
   this: it failed Tier-2 execution outright (21/81, 25.9%) despite a
   completely fine rendered PNG. Fixed to `lambda self, *a, **k: self`
   in both files; see
   [`tests/test_gtsave_stub_return_value.py`](../tests/test_gtsave_stub_return_value.py).
   Because this invocation's execution *status* genuinely changed (not
   just a mechanical check's value), it was re-scored with a real,
   fresh `comparator.compare()` call — including a new judge API call,
   since the previous judge result was never elicited under the old
   failing-execution path — rather than the mechanical-only recompute
   used everywhere else. It now scores 68/88 (77.3%).

`eval-results/_recompute_mechanical_checks.py` (mechanical recompute) and
[`eval-results/_rescore_towny_repeat1.py`](_rescore_towny_repeat1.py) (the
single real re-score above) are both committed for auditability; see each
skill's own `SUMMARY.md` for its exact before/after numbers.

## Findings (2026-08-09 sweep — superseded by 2026-08-12 below, kept for history)

- **`prose` wins, on replication rather than this sweep's margin alone.**
  Its 5.6pp lead over the runner-up here is *smaller* than the runner-up's
  own 18.2pp repeat-to-repeat spread — by this file's own "gap smaller
  than either skill's own spread means don't call it settled" standard
  (applied to `house`/`scripts` just below), a single sweep's 5.6pp isn't
  decisive on its own either. What makes `prose` the confident pick isn't
  this one number, it's that it led `house` specifically by a comfortable
  margin on *both* sweeps (15.6pp on 2026-08-07, 5.6pp here) — two
  independent sweeps agreeing, even at different margins, is real signal
  in a way one sweep's raw gap over whichever skill happens to be
  runner-up that week isn't.
- **`house` and `scripts` swap places relative to the 2026-08-07 sweep
  this file previously reported (`scripts` had led).** On the bug-fixed
  2026-08-09 runs, `house` edges out `scripts` (69.3% vs. 66.1%, a 3.2pp
  gap) — but both skills' own repeat-to-repeat spread (18.2pp and 16.9pp)
  is *larger* than that gap, so treat this specific ordering as noisy, not
  settled. Note this gap is now the *real*, fully-corrected one: an
  earlier draft of this file attributed most of it to a single outlier
  invocation (`scripts/towny_growth_trends/repeat_1`, which had scored
  25.9% due to a `gt = finalize(gt, ...)` reassignment tripping a
  since-fixed execution-tier bug) and suggested excluding it narrowed the
  gap to 2.1pp — that framing no longer applies now that the bug itself
  is fixed and the invocation is scored for real (77.3%) and included
  above, not excluded. What's consistent across both the 08-07 and 08-09
  data: `scripts`' checker loop is the **most expensive** of the three
  real skills every time it's been measured, for a mean score that's
  sometimes ahead of `house`'s and sometimes behind it — the loop's cost
  is certain, its benefit isn't. (Its consistency ranking is less stable
  than its cost ranking: it was least consistent on the pre-fix numbers,
  but with the outlier invocation now scored correctly instead of
  crashing to 25.9%, `house` has the wider spread of the two on this
  sweep.)
- **`house` remains the cheap, decent option** regardless of its exact
  rank versus `scripts` this sweep — no flowchart, no checker loop, a real
  and now-competitive quality gain over baseline for the lowest cost of
  the three real skills.
- **`creator` still loses to no skill at all.** -3.2pp behind baseline,
  unchanged in direction from every prior measurement of it. See
  `creator/SUMMARY.md` and `creator/progressive_disclosure.md` for one
  concrete, falsifiable partial explanation (shallower, less-routed
  reference reading), not a full diagnosis.

## Which skill is best overall (2026-08-09 sweep — superseded by 2026-08-12 below, kept for history)

**`prose`** — highest mean score and most consistent on every sweep this
file has ever reported, under every version of the comparator, and its
lead over `house` specifically replicates across both the 2026-08-07 and
2026-08-09 sweeps (not just a single measurement). `house` vs. `scripts` is
genuinely close and
sweep-dependent — pick `house` when cost and consistency matter, `scripts`
only if its checker loop's occasional extra points are worth its
reliably-higher cost and reliably-lower consistency to you. `creator` is
not yet a real contender.

## Skill realignment, comparator generalization, and a parsing fix (2026-08-12)

Two changes landed on `main` after everything above and before the sweep
this section (and "Data refresh (2026-08-12)" below) reports on:

1. **Skill realignment + comparator generalization** (PRs #93–#101). A
   large effort redesigned all 6 ground truths to match author-specified
   table conventions and generalized the comparator to match: removed the
   ≤2-measure cap on colored-measure credit (`check_colored_measure_
   selection`), made the heading band and stub tint fixed-and-universal
   rules (previously house-specific taste checks) rather than
   conditionally-scored ones, and made row striping apply by default. This
   changed both the ground truths every skill is scored against and which
   checks exist/how they're weighted — not a re-scoring of old data, a
   genuinely different rubric.
2. **`runner/convergence.py` band/stub-tint parsing fix** (PR #102). The
   helper-call parser behind the Header-branding and Stub-tint checks (a)
   misread Python comments as real calls in some cases, (b) took the
   FIRST matching call in a chain instead of the LAST, and (c) had a
   hue-defaulting bug that made a correctly-styled header score as
   `None`/missing. All three were bugs in the checker, not in any
   candidate — a candidate that was actually styled correctly could still
   lose Header-branding/Stub-tint credit under the old parser.

Because the rubric changed twice (#1) and a mechanical parsing bug that
directly affects two specific checks was fixed (#2), a fresh sweep was
necessary — re-scoring the old 2026-08-09 candidates against the new
rubric wouldn't isolate anything meaningful, since the candidates
themselves predate the realigned skills too.

**A third thing was found, not fixed, during this refresh's own
regeneration** (out of scope to fix — touches `runner/`): `check_caption_
keywords` (added the same day as #1) crashes with `TypeError` on a
candidate whose caption text isn't a static string literal (exactly one
invocation, `prose/sp500_monthly_performance/repeat_2`, hit this). Separately,
inspecting why `house`'s numbers looked low despite the fixes above
surfaced two more suspected (not yet fixed) comparator gaps specific to
`house`'s "opaque imported helper" idiom — see `house/SUMMARY.md`'s own
writeup for detail; they're believed to understate `house`'s true score by
roughly 3pp on this sweep.

## Data refresh (2026-08-12)

`house`, `prose`, and `scripts` below are each that skill's fresh
`runs/sweep/20260812_1936xx_<skill>_6prompts` sweep — a new harness run,
new LLM generations, scored by the current (post-realignment,
post-generalization, post-PR-#102) comparator via `eval-results/<skill>/
plots/make_plots.py`. `creator` was **not** re-swept (its raw sweep
directory still doesn't exist on disk, unchanged from the 2026-08-09
refresh above) — its row below is carried forward unchanged from that
section and is not affected by, or evidence about, either 2026-08-12
change; treat it as out of scope for this update.

| Skill | Mean comparator score | vs. baseline | Score spread (3 repeats) | Mean cost/invocation |
|---|---|---|---|---|
| `scripts` | **82.0%** | +64.9pp | 11.8pp (most consistent) | **$0.192** (most expensive) |
| `prose` | 76.8%\* | +56.2pp | 29.8pp (least consistent) | $0.181 |
| `house` | 75.8%\*\* | +57.1pp | 24.8pp | **$0.134** (cheapest) |
| `creator` | 21.7%\*\*\* | -3.2pp | 18.1pp | $0.095 |
| baseline (no skill) | 17.1–20.6% | — | n/a (1 run) | $0.073–$0.078 |

\*`prose`'s mean is over 17 (not 18) scored invocations —
`sp500_monthly_performance/repeat_2` has no score due to the
`check_caption_keywords` crash described above.
\*\*`house`'s 75.8% is the raw, unmodified-comparator number; see
`house/SUMMARY.md` for why it's very likely an understatement (two
suspected comparator gaps specific to its helper-import idiom, estimated
~3pp combined impact) rather than a real quality gap versus `prose`.
\*\*\*`creator` is unchanged 2026-08-09 data (see above), not part of this
refresh.

No valid "before → after %" comparison exists against this file's
pre-2026-08-12 numbers above — the rubric changed twice and a parsing bug
was fixed in between, so a direct percentage delta would be comparing
different measuring sticks, not real movement. Data-compliance and
formatting-compliance splits, and full per-check failure breakdowns, are
in each skill's own `SUMMARY.md`.

## Findings (2026-08-12, round 2 — superseded by round 3 further down)

- **All three real skills land within a similar band** (75.8%–82.0%,
  mid-to-upper-70s to low-80s) — closer together than the 2026-08-09
  numbers suggested, and the ranking among them should be read with the
  `house` caveat above firmly in mind: its raw number is the lowest of the
  three here, but the two suspected comparator gaps found this round
  (hairlines-recognition, `finalize()` default-path) are large enough
  (~3pp estimated combined) to plausibly put it ahead of `prose` once
  fixed, matching the "house at or near the top" pattern a prior analysis
  pass expected. Nothing here should be read as `house` having gotten
  worse — it's the same skill, scored by a comparator with a specific,
  identified blind spot for its own worked-example idiom.
- **`sp500_monthly_performance` is the hardest prompt for every skill**,
  by a wide margin (59.4% for `prose`, 51.1% for `scripts`, 58.6% for
  `house`, vs. 62–97% for every other prompt) — a genuine corpus-difficulty
  signal, not a skill-specific weakness. Six computed/derived measures
  (`pct_change`, `avg_volume`, `best_day_gain`, `worst_day_loss`,
  `monthly_open`, `monthly_close`) and a signed-percent formatting rule
  make it the corpus's most demanding prompt regardless of which skill
  attempts it.
- **`scripts` is the highest raw scorer this round** (82.0%), reversing
  its 2026-08-09 position relative to `house` — but `scripts` is also
  still the **most expensive** skill every time it's been measured, a
  pattern that has held across every sweep this file has reported.
- **`Caption keyword coverage` fails at a near-identical rate for every
  skill** (82–83%), on the same missing keywords, on the same prompt
  (`gtcars_hp_price`'s "bentley"/"corvette"/"don't move together" trio) —
  the same "flat/non-discriminating across every skill" shape the
  2026-08-09 consensus-tuning passes used to justify removing checks
  (see above). Not acted on here (out of scope — this task doesn't touch
  the comparator), but worth flagging for a future tuning pass.
- **`creator` is unmeasured this round** and its 2026-08-09 numbers (still
  losing to baseline) remain this file's only data on it.

## Which skill is best overall (2026-08-12, round 2 — superseded by round 3 further down)

**No longer a clean single pick, unlike the 2026-08-09 sweep.** `scripts`
has the highest raw score (82.0%) but is also the most expensive and,
historically, the least reliably ahead. `prose` (76.8%) is once again the
least consistent repeat-to-repeat of the three (29.8pp spread — even
wider than its own 2026-08-09 number). `house` (75.8% raw, likely ~79%
once the two suspected comparator gaps above are fixed) remains the
cheapest by a wide margin and — on the corrected estimate — competitive
with `prose`. Given the `house` caveat, this sweep doesn't support as
confident a single-skill recommendation as the 2026-08-09 write-up gave;
fixing the two suspected `house`-specific comparator gaps (out of scope
here) is the natural next step before re-litigating the ranking. `creator`
remains not a real contender.

## Comparator bug fix (PR #103, landed after round 2 above)

Round 2's own writeup (immediately above) flagged two suspected, still-open
comparator gaps specific to `house`'s "opaque imported helper" idiom
(`from house_table import frame, hairlines, finalize, ...`): a
`_hairlines_present` check that never recognized a bare `hairlines(gt)`
call (scoring all 18/18 `house` invocations as missing hairlines
regardless), and a render-target check that didn't know `finalize(gt,
path="table.png", ...)`'s own default `path` argument (scoring 9/18 bare
`finalize(gt)` calls as not rendering `table.png`). Both are fixed in
`runner/comparator.py` as of PR #103. This is the third bug found and
fixed across this effort's three sweep rounds, after: the skill-realignment
+ comparator-generalization effort (PRs #93–#101, round 1 → round 2), and
the `convergence.py` Header-branding/Stub-tint parsing fix (PR #102, also
round 1 → round 2). PR #103 is what separates round 2 (above) from round 3
(below) — no skill or ground truth changed between them, only this one
comparator fix.

## Data refresh (2026-08-12, round 3 — current, trustworthy numbers)

`house`, `prose`, and `scripts` below are each that skill's fresh
`runs/sweep/20260812_2120xx_<skill>_6prompts` sweep — a new harness run,
new LLM generations, scored by the comparator as it stands after all three
fixes above (realignment/generalization, PR #102, PR #103). `creator` was
**not** re-swept (its raw sweep directory still doesn't exist on disk,
unchanged since the 2026-08-09 refresh) — its row is carried forward
unchanged and out of scope for this update.

| Skill | Mean comparator score | vs. baseline | Score spread (3 repeats) | Mean cost/invocation |
|---|---|---|---|---|
| `scripts` | **82.3%** (n=17) | +60.1pp | 20.2pp | **$0.184** (most expensive) |
| `house` | 79.4% | +65.4pp | **18.1pp** (most consistent) | **$0.134** (cheapest) |
| `prose` | 79.0% | +61.4pp | 23.5pp | $0.182 |
| `creator` | 21.7%\* | -3.2pp | 18.1pp | $0.095 |
| baseline (no skill) | 14.0–22.2% | — | n/a (1 run) | $0.068–$0.080 |

\*`creator` is unchanged 2026-08-09 data (see above), not part of any
refresh since.

**Because round 2 → round 3 is purely a comparator bug fix (PR #103) with
the same candidates re-scored — not a skill change and not a new sweep of
different ground truths — a direct before/after comparison IS meaningful
here for the two checks that bug affected**, unlike the round-1 → round-2
transition (which also changed the ground truths and check set, making
that comparison invalid). See each skill's own `SUMMARY.md`, and
particularly `house/SUMMARY.md`'s "two round-2 comparator gaps are now
fixed" section, for the specific before/after numbers:

| Check | Round 2 (pre-PR-#103) | Round 3 (post-PR-#103) |
|---|---|---|
| `house` — Frame + hairlines + dividers | 18/18 (100%) fail/partial, mean 53.7% | 7/18 (39%) fail/partial, mean 85.2% |
| `house` — Render mechanics | 10/18 (56%) fail, mean 44.4% | 1/18 (6%) fail, mean 94.4% |
| `scripts` — Frame + hairlines + dividers | 7/18 (33%) fail/partial, mean 87.0% | 7/17 (41%) fail/partial, mean 84.3% |
| `scripts` — Render mechanics | 2/18 (11%) fail, mean 88.9% | 0/17 (0%) fail, mean 100% |

`prose` had zero invocations affected by PR #103 in either round (its
worked example never relies on the `hairlines`/`finalize` helper forms the
bug touched).

No valid "before → after %" exists for the *overall* per-skill mean score
across round 2 → round 3 despite the above — `prose`'s and `scripts`'
overall means moved too, but for reasons other than PR #103 (different
LLM generations this round, not a re-score of the same candidates) — only
`house`'s two specific checks above are a genuine same-candidate,
comparator-only before/after.

## Findings (round 3, current)

- **The round-2 hypothesis is confirmed, not just estimated.** Round 2's
  writeup estimated that fixing `house`'s two comparator gaps would move it
  to roughly 79% and let it edge out `prose`. With PR #103 landed and a
  fresh sweep run, `house` scores **79.4%**, edging out `prose`'s 79.0% by
  a real (if narrow — 0.4pp, well inside both skills' own repeat-to-repeat
  spread) margin, directly, with no adjustment needed.
- **All three real skills land in a tight band** (79.0%–82.3%) — tighter
  than round 2's already-tight 75.8%–82.0% range. `scripts` remains the
  highest raw scorer, and remains the most expensive every time it's been
  measured across all three rounds — the same tradeoff noted in every
  prior round's findings.
- **`house` is now unambiguously the cheapest and among the best-scoring**
  of the three real skills — $0.134/invocation (vs. $0.182 `prose`, $0.184
  `scripts`) for a score that's no longer the lowest of the three, now that
  its comparator-side blind spot is closed.
- **`sp500_monthly_performance` remains the hardest prompt for every
  skill** — `prose` 62.1%, `scripts` 59.8%, `house` 60.1% (excluding one
  `house` repeat that hit a separate, already-documented, narrower
  comparator gap — see `house/SUMMARY.md` — its raw per-prompt mean is
  60.1% either way once that one outlier repeat is set aside). This is the
  third consecutive round this exact pattern has held — a genuine
  corpus-difficulty signal (six computed/derived measures plus a
  signed-percent formatting rule), not a skill- or comparator-specific
  artifact.
- **`Caption keyword coverage` continues to fail at a near-identical rate
  for every skill** (82–83%, mean 61–67%), on the same missing keywords
  (`gtcars_hp_price`'s "bentley"/"corvette"/"don't move together" trio) —
  the same "flat/non-discriminating across every skill" shape the
  2026-08-09 consensus-tuning passes used to justify removing checks (see
  above). Still not acted on (out of scope — this task doesn't touch the
  comparator), and now confirmed stable across three rounds.
- **The `check_caption_keywords` crash (first flagged in round 2) is
  confirmed real but candidate-text-dependent, not skill- or
  prompt-specific.** Round 2 hit it once, on
  `prose/sp500_monthly_performance/repeat_2`; that exact invocation does
  NOT crash under round 3's `prose` candidates. Round 3 instead hit it once
  on a different skill/prompt entirely,
  `scripts/airquality_monthly_summary/repeat_1`. Still unfixed, still out
  of scope (touches `runner/`).
- **`creator` remains unmeasured this round** (its 2026-08-09 numbers,
  still losing to baseline, are this file's only data on it).

## Which skill is best overall (round 3, current)

**Closer to a clean pick than round 2, but still tight.** `scripts`
(82.3%) has the highest raw score, as it has on every round since 2026-08-09,
but remains the most expensive of the three and its own 20.2pp
repeat-to-repeat spread is not small either. `house` (79.4%) and `prose`
(79.0%) are now separated by less than half a point — `house` costs
roughly 26% less than `prose`'s per-invocation price ($0.134 vs. $0.182)
for a statistically indistinguishable score, and is now the most
consistent of the three
(18.1pp spread, vs. `prose`'s 23.5pp) — a real case for `house` as the
default pick when cost and consistency matter, with `scripts` as the
higher-ceiling but pricier alternative when its checker loop's extra
points are worth paying for. `prose` no longer has a clear edge over
`house` the way it did as of the 2026-08-09 sweep. `creator` remains not a
real contender.

## Layout

```
eval-results/
  _lib.py                     shared metrics-extraction helpers (see its docstring)
  _apply_check_removal.py     the one-off transform behind both consensus-tuning passes; post-refresh,
                               the only skill whose committed numbers still come from it is `creator`
  SUMMARY.md                  this file
  <skill>/
    metrics.json              full per-invocation cost/tokens/comparator-score data
    SUMMARY.md                this skill's numbers + findings
    progressive_disclosure.md real transcript excerpt showing the skill being read progressively
    plots/
      make_plots.py           re-scores the LATEST local runs/sweep/*_<skill>_6prompts and regenerates
                               the 4 PNGs below -- see the warning below before running this
      cost.png                 skill cost vs. baseline, per prompt (bar)
      tokens.png                token usage per invocation, per prompt (scatter/strip)
      consistency.png           min-mean-max comparator score across 3 repeats (range/dumbbell)
      comparator_score.png      comparator score distribution: 3 repeats vs. baseline (box)
    samples/<prompt>/<variant>/  curated table.py + table.png + comparator report.txt
```

**Warning:** `python eval-results/<skill>/plots/make_plots.py` does NOT
just re-derive the numbers already committed here — `_lib.find_latest_
sweep_dir()` globs `runs/sweep/*_<skill>_6prompts` and takes the
*most recent* match on your local disk, which may be a completely
different (fresher) sweep than the one `metrics.json` currently reports
on. Running it would silently swap in a different candidate set — exactly
the confound an internal review caught during pass 1. It will also
hard-fail for `creator`, whose original sweep directory has been deleted.
If you need to re-apply a comparator change to the data already committed
here without changing candidates, use `_apply_check_removal.py` as a
template (point-subtraction on the existing `metrics.json`, not a live
re-run) rather than `make_plots.py`. Only use `make_plots.py` when you
deliberately want to score a fresh sweep from scratch (needs
`ANTHROPIC_API_KEY` in `.env` for the judge calls) — this is exactly how
`house`/`prose`/`scripts`' current numbers were produced (see "Data
refresh" above); it was a deliberate choice made once, not something to
casually re-run expecting the same numbers back.

## Data refresh (2026-08-13, round 4 — current, trustworthy numbers)

Fresh 6-prompt sweeps for `house`/`prose`/`scripts` (`--repeat 3 --model
haiku`), run AFTER merging all five rounds of fixes to `main`: a house
`RULES.md` dtype footgun, a missing `hairlines()` helper + checker rule in
`great-tables-ci`, a Top-N/Ordered-magnitude routing ambiguity, the
comparator's static AND execution-tier extractors both learning to recognize
a `def build_table(): ...` / `if __name__ == "__main__":` wrapped script as
inlined top-level code (previously invisible to both, scoring real
candidates ~18–35% purely from the blind spot), a `check_caption_keywords`
crash on non-literal caption text, and (round 5, defensive-only — 0/949 real
candidates ever hit either shape) a decorated or class/assignment-shadowed
guard target no longer being wrongly inlined. `creator` not re-swept
(unchanged from 2026-08-09, still losing to baseline).

| Skill | Mean score | Mean spread (was, round 3) | Max spread (was) | Mean cost |
|---|---|---|---|---|
| `house` | 82.4% | 10.8pp (18.1pp) | 51.7pp | **$0.131** (cheapest) |
| `prose` | 81.7% | 10.3pp (23.5pp) | 28.9pp | $0.190 |
| `scripts` | 81.5% | 16.2pp (20.2pp) | 40.4pp | $0.189 |

All three land in a tight band, similar to round 3's own "tight band"
finding. Several single-prompt spreads are WIDER than the mid-fix-cycle
sweep reported in an earlier draft of this section — traced individually
(see each skill's own `SUMMARY.md`) to one-off model mistakes in this fresh
batch, not mechanical bugs: forgetting `rowname_col=` entirely, confusing
pandas' `.set_index()` with it, and picking a non-unique `mfr`-only stub
instead of the documented `mfr + model` composite. All three are places the
skills' own reference docs already teach the correct pattern (2/3 sibling
repeats on the same prompt did it right); this is inherent haiku-tier
sampling variance on a 3-repeat sample, not something a further doc/code fix
would eliminate. Combined with the already-known sources (sp500's
ground-truth month-label ambiguity, occasional Big-Color restraint lapses,
towny's spanner/ranking-metric ambiguity), this round's remaining spread has
no fixable mechanical cause left that this effort's deep-dive could find.
