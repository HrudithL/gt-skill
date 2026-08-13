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
skill's `plots/usage.png` / `comparator_score.png` for the per-skill
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
                               the 2 PNGs below -- see the warning below before running this
      usage.png                 grouped bar chart: bar height = tokens per prompt (skill vs.
                                 baseline), cost per invocation labeled above each bar
      comparator_score.png      evaluation score: 3 repeats (box, height = consistency) vs. baseline
                                 (point), all 6 prompts in one view, with a computed mean-lift subtitle
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
would eliminate (a doc fix for the specific `set_index()`-vs-`rowname_col=`
confusion has since landed, PR #107). Combined with the already-known
sources (sp500's ground-truth month-label ambiguity, occasional Big-Color
restraint lapses, towny's spanner/ranking-metric ambiguity), this round's
remaining spread has no fixable mechanical cause left that this effort's
deep-dive could find.

**CAVEAT (2026-08-13, added after this round's numbers above were
committed; WIDENED 2026-08-13 after a second review round's independent
recompute — see below):** the "sp500's ground-truth month-label ambiguity"
item cited above as an unfixable source of spread was, in fact, a real
comparator bug in row/date-identity matching — `normalize_id()` in
`runner/execution_tier.py` compared date-like row/stub labels as plain
strings, so semantically identical months rendered in different (equally
legitimate) formats, e.g. ground truth's `"Jan 2010"` vs. a candidate's
`"2010-01"` or `.dt.to_period("M")` output, scored as a complete row-set
mismatch. This has been found and fixed
(`fix/comparator-date-aware-row-matching`, PR #108). As a direct, measured
consequence, `sp500_monthly_performance` scores in this file are
**understated** for `prose` and `scripts`: their sweep candidates commonly
used the `"2010-01"`-style format, while `house`'s candidates already
happened to match the ground truth's `"%b %Y"` format, so `house` is
unaffected.

**Independently re-verified, not just the original disclosure's numbers:**
re-executing the actual committed candidate scripts (from each skill's
original sweep dir) against the ground truth with the now-fixed
`normalize_id`, and recomputing both `normalize_id`-dependent mechanical
checks ("Row/entity selection identity" and "Computed/derived value
correctness") for every `sp500_monthly_performance` invocation:

- **Row identity**: `prose` repeat_1 and repeat_3 flip from 0/10 (FAIL,
  complete row-set mismatch) to 10/10 (PASS); all 3 `scripts` repeats flip
  from 0/10 to 10/10; `prose` repeat_2 and all 3 `house` repeats were
  already 10/10 and are unchanged. Baselines for all three skills stay
  0/10 either way (no stub column in the rendered output — see the
  baseline-reason correction below).
- **Computed/derived value correctness (the "likely further, unquantified
  uplift" the original disclosure flagged but did not check): confirmed
  for `scripts`, only partial for `prose` — not a blanket effect.** For
  `scripts`, all 3 repeats gain additional points once row identity is
  fixed (repeat_1 0/10→3/10, repeat_2 0/10→5/10, repeat_3 0/10→5/10). For
  `prose`, only repeat_1 gains (0/10→5/10); repeat_3's value check stays
  0/10 even though its row identity flips to 10/10 (still 0/6 canonical
  measures value-matched — a real, unrelated computation gap in that
  candidate, not a row-alignment artifact); and `prose/repeat_2` is the
  clean control case — its row identity was **already** 10/10 before this
  fix, and its value-correctness check is **still** 0/10 after it (0/6
  measures matched, same failure both before and after) — proof this
  fix's benefit doesn't propagate automatically and must be checked per
  repeat, not assumed.
- **Net per-skill mean-score impact**, applying only these two checks'
  deltas and leaving every other stored check value as-is: `house`
  unchanged at 82.4% (its candidates already used the matching format, so
  this fix touches nothing for it); `prose` rises from 81.7% to
  **~83.3%** (+1.6pp over the full 18-invocation mean); `scripts` rises
  from 81.5% to **~84.2%** (+2.7pp) — **the largest gainer, and the new
  likely top scorer, overtaking both `prose` and `house`.** All three
  numbers are estimates from a scoped, non-committed recompute (only the
  two `normalize_id`-dependent checks substituted; not a full
  `eval-results/**` regenerate), so treat the ranking as directionally
  reliable but not final.

Since this fix changes the likely ranking among all three skills — not
just `house` vs. `prose` — **the round-4 "`house` edges out `prose` and
`scripts`" framing above should be treated as stale pending a fresh,
full recompute, and `scripts` (not `house` or `prose`) is the current
best guess for the new top scorer.** That recompute (a full
`eval-results/**` regenerate reflecting the fixed `normalize_id`) is
deliberately deferred to a separate, small follow-up PR — not done as
part of #108, to keep that PR's diff focused on the comparator code fix
alone. Until that recompute lands, do not cite this round's `house` vs.
`prose` vs. `scripts` ranking as settled.

**Two description corrections (round-5 review):**
- The baselines are **not** all "no stub column for the same reason."
  `prose`'s and `scripts`' sp500 baselines actually execute successfully
  (they render a real table, just without a `rowname_col=` stub) — e.g.
  `prose`'s baseline report shows `[PASS] Render mechanics` and a
  populated column set, just `Stub existence: 0/2`. `house`'s sp500
  baseline, by contrast, **fails to execute at all** ("candidate failed
  to execute: no top-level `gt` GT instance in table.py") — a strictly
  more severe, different failure mode that only incidentally also shows up
  as "no stub column; row selection unverifiable" on the row-identity
  check line, because that check's message doesn't distinguish "ran fine,
  omitted the stub" from "never produced a `GT` object at all."
- sp500_monthly_performance's total point denominator is **not** a fixed
  88. Per `eval-results/house/metrics.json`, `house`'s repeats score out
  of 89 (repeat_1) or 90 (repeat_2, repeat_3), not 88 — variable
  denominators depending on which checks land N/A for that particular
  candidate. `prose`'s and `scripts`' repeats do use 88, and all three
  skills' baselines use 85.

## `check_caption_not_generic` calibration correction (2026-08-13, PR #116 review round)

PR #116 (which replaced the exact-keyword `check_caption_keywords` with the
deterministic `check_caption_not_generic`) is not yet reflected in any
`eval-results/**` numbers above or in the skill-level `SUMMARY.md`/
`metrics.json` files — that recompute is, like the `normalize_id` fix
above, **deliberately deferred to a separate follow-up**, so this section
is disclosure of a measured before/after, not a claim that the stored
scores already include it.

PR #116's own description compared **raw pass-RATES** on a 54-candidate
corpus (`house`/`prose`/`scripts` only, `creator` omitted): the old
`check_caption_keywords` failed ~82-83% uniformly; the new check passed
50/54 (92.6%). A follow-up review round found this framing **overstates
the actual point-level impact by roughly 3x**, because the old check had
*partial* credit (`_round_points_covered` — e.g. 2/3 keyword rules
matched still earned points) while the new check is *binary* (3 or 0) —
comparing pass-RATE deltas between a partial-credit check and a binary one
isn't an apples-to-apples measure of how many points actually moved. The
same review round also found the new check had its own real bugs (a
`Source:`-prefix regex that zeroed genuine insight written after a
citation, a vacuity floor that was effectively zero, and a handful of
lexical-accident false verdicts) — fixed in this same PR, and the numbers
below are POST-fix.

**Recalibrated across all 72 real committed candidates (all 4 skills,
`house`/`prose`/`scripts`/`creator`, 18 each — the original 54-candidate
calibration omitted `creator` entirely, which is exactly where this check
misbehaves most):**

| Skill | Old (`check_caption_keywords`) mean pts/3 | New (`check_caption_not_generic`, post-fix) mean pts/3 | Mean points delta | Old pass-rate | New pass-rate |
|---|---|---|---|---|---|
| `house` | 1.889 | 2.333 | **+0.444** | 16.7% | 77.8% |
| `prose` | 1.833 | 2.833 | **+1.000** | 16.7% | 94.4% |
| `scripts` | 1.944 | 2.667 | **+0.722** | 16.7% | 88.9% |
| `creator` | 1.778 | 0.333 | **-1.444** | 16.7% | 11.1% |
| **All 72** | **1.861** | **2.042** | **+0.181** | 16.7% | 68.1% |

The headline point-level effect across all 72 candidates is a modest
**+0.181 mean points out of 3** (+6.0% of the check's point pool) — nowhere
near the ~3-5x apparent swing the raw pass-rate framing would suggest for
`house`/`prose`/`scripts`. **`creator` moves in the OPPOSITE direction**,
and by a large margin: its mean score drops from 1.778 to 0.333 (a real,
correctly-deserved penalty, not a bug — `creator`'s committed candidates
overwhelmingly write bare, no-insight source notes like `"Source:
gtcars.csv dataset"` or `"Source: islands.csv"`, which the new check
correctly recognizes as attribution-only; the old check's occasional
partial credit for these came from trivially-satisfiable `CAPTION_KEYWORDS`
rules, e.g. `gtcars_top10_by_country`'s empty `caption_should_mention`
list, not from any real caption substance). This is the accurate
eval-integrity picture: three skills gain a small, real amount of credit
for genuine captions the old exact-keyword mechanism couldn't recognize;
`creator` loses credit it was never substantively earning in the first
place.

As with the `normalize_id` disclosure above, this is a scoped, non-committed
recalibration script's output (reads each candidate's `table.py` via
`convergence.parse_design_choices()` directly, not a full harness re-run) —
directionally reliable, but the actual `eval-results/**` files (per-skill
`metrics.json`/`SUMMARY.md`/plots) still reflect the PRE-#116
`check_caption_keywords` scores until a full regenerate lands.

### Round-4 follow-up (2026-08-13): fixed a recurring "prefix veto instead of strip-and-grade" bug shape

A further review round of `check_caption_not_generic` found 4 more real
bugs on top of the round-3 fixes reflected in the table above. Three of
the four shared the same root shape: **the check treated a prefix pattern
(a citation label, a generic opener) as a verdict on the WHOLE caption
instead of stripping the prefix and grading whatever remains** — the same
class of bug, found and fixed three separate times before the structural
fix below unified them:

- **Generic-opener whole-caption veto (2 bugs):** `_caption_generic_opener_sentence`
  failed the ENTIRE caption if ANY sentence in ANY note matched a generic-
  opener pattern ("the table shows...") — with no check for whether
  distinctive content remained after the matched prefix, and with the veto
  applying even when OTHER sentences in the same caption carried real
  content. Verified real casualty: `house/airquality_monthly_summary/
  repeat_2`'s genuine methodology note ("Data represents monthly averages
  across all observed days in each month.") was zeroed for its four
  opening words alone. **Fixed structurally**: replaced the veto with
  `_strip_generic_opener_sentences`, which strips only the matched prefix
  from each matching sentence (the same treatment `_strip_citation_clause`
  already gave citation labels) and keeps whatever follows; the caption now
  only fails on generic-template grounds if NOTHING distinctive survives
  anywhere, across every note and sentence.
- **Citation-clause boundary insensitivity:** `_CAPTION_SENTENCE_END_RE`
  matched the FIRST `.`/`;`/em-dash occurring anywhere after a citation
  label, with no requirement that it be followed by whitespace/end-of-
  string — so a period embedded in a filename ("`airquality.csv`")
  truncated the clause at the wrong point, leaving a meaningless fragment
  that got graded as real caption content (a false PASS on a pure-
  attribution caption). It also lacked en-dash as a recognized terminator
  even though the corpus uses en-dashes pervasively for ranges/separators,
  so otherwise-identical prose reached different verdicts depending on
  which dash character it used. **Fixed**: the terminator regex now
  requires whitespace-or-end-of-string after the punctuation, and
  recognizes en-dash alongside em-dash/semicolon (bare hyphen deliberately
  still excluded — more often part of a compound word/range than a clause
  boundary).
- **Word-filter/floor undercounting short-but-real insights:** the
  `len(w) > 2` filter dropped short domain abbreviations ("HP") from the
  content-word count, and the stopword filter ran BEFORE stemming (so a
  plural of a stopword, e.g. "displays", leaked through as a counted
  word instead of being excluded like its singular "display"). The
  4-content-word floor also zeroed genuinely substantive 3-word captions
  that no filter tweak could fix (e.g. "The Corvette outguns the Bentley.").
  **Fixed**: loosened the filter to `len(w) >= 2`, fixed the stem-then-
  filter order, and lowered the floor from 4 to 3.

**Isolated before/after impact of just this round's fixes** (same 72
real committed candidates; "before" = the round-3 numbers in the table
above, "after" = post round-4 fix, both measured with the identical
recalibration methodology so the delta reflects only today's changes):

| Skill | Before (round-3) mean pts/3 | After (round-4) mean pts/3 | Mean points delta | Before pass-rate | After pass-rate |
|---|---|---|---|---|---|
| `house` | 2.333 | 2.667 | **+0.333** | 77.8% | 88.9% |
| `prose` | 2.833 | 2.833 | +0.000 | 94.4% | 94.4% |
| `scripts` | 2.667 | 2.833 | **+0.167** | 88.9% | 94.4% |
| `creator` | 0.333 | 0.500 | **+0.167** | 11.1% | 16.7% |
| **All 72** | **2.042** | **2.208** | **+0.167** | 68.1% | 73.6% |

Exactly 4 of the 72 candidates changed verdict, each a direct real-corpus
instance of one of the bugs above flipping from 0/3 to 3/3, with no
regressions elsewhere:

- `house/airquality_monthly_summary/repeat_2` — genuine methodology note,
  previously zeroed by the generic-opener veto (bug 1 above).
- `house/gtcars_hp_price/repeat_3` — `"Price is the MSRP in USD."`,
  previously zeroed by the 4-word floor (bug 3 above).
- `scripts/islands_sizes/repeat_2` — `"Data shows the area of islands
  across the world."`, previously zeroed by the generic-opener veto (bug 1).
- `creator/sp500_monthly_performance/repeat_1` — `"Data: S&P 500 daily
  prices and volumes, 2010-2015."`, previously zeroed by the 4-word floor
  (bug 3).

All 6 ground truths' own captions still pass at 3/3. As with the
round-3 recalibration above, this is a scoped, non-committed script
output (see `runner/comparator.py`'s test suite,
`tests/test_caption_not_generic.py`, for the mechanical, deterministic
unit coverage of each fix) — the stored `eval-results/**` files still
reflect the PRE-#116 `check_caption_keywords` scores until a full
harness regenerate lands.

### Round-5 follow-up (2026-08-13): round-4's own fix introduced 2 real regressions, plus 1 unrelated bug

A further review round found that round-4's structural strip-and-grade fix
(above) over-corrected: after stripping a generic-opener prefix or a
citation label, the ONLY remaining defense against the remainder itself
being vacuous was the `_CAPTION_MIN_CONTENT_WORDS` word-count floor — which
any generic table description clears trivially (naming 3+ of the table's
own column/subject nouns is enough). This made the generic-opener gate
**effectively unreachable**, and separately, round-4's floor change
(4 -> 3) accidentally un-broke a bare `"Data:"` citation label round-2 had
deliberately made to fail. Two concrete real-corpus consequences, and the
tests that should have caught them:

- **`scripts/islands_sizes/repeat_2`** — `"Data shows the area of islands
  across the world."` — this is the SAME caption the very first version of
  this PR's own "Calibration" section (above) cited as a textbook generic-
  template-opener failure, and round-4's own recalibration table
  (immediately above) mischaracterized this exact candidate flipping to
  3/3 as a *fix* ("previously zeroed by the generic-opener veto") — it was
  actually a regression: round-4's strip-and-grade change stripped "Data
  shows " and then had nothing left to stop "the area of islands across
  the world" (a bare, insight-free noun phrase) from passing on word count
  alone. The original verdict-level test asserting this exact caption
  fails (`test_generic_template_opener_fails`) was **deleted** in round-4
  and replaced with a strictly weaker test that only checked a helper
  function's raw string output, never the actual pass/fail verdict — so
  it couldn't have caught this regression shipping.
- **`creator/sp500_monthly_performance/repeat_1`** — `"Data: S&P 500 daily
  prices and volumes, 2010-2015."` — round-2 had deliberately added `"data"`
  to the stopword list specifically to zero this exact caption (see that
  round's own PR text, Fix 2: *"creator/sp500_monthly_performance/repeat_1's
  caption ... was creator's ONLY passing caption in the whole corpus, and
  it's itself vacuous"*). Round-4's floor change (4 -> 3) accidentally let
  this caption's 3 surviving content words (daily/price/volume) clear the
  lowered floor, un-breaking round-2's deliberate fix — and the test
  covering it was **inverted** (changed to assert the caption passes)
  rather than the regression being caught and the logic fixed.

**Fixed this round:**

1. A citation-/generic-opener-stripped remainder now has to clear an
   additional check, `_stripped_remainder_is_vacuous` (reuses the same
   overlap-based restatement test the whole-caption check already used,
   applied to just the remainder, OR'd with a new "no analytical signal"
   check — a curated comparison/trend/relationship word list plus a crude
   past-tense/gerund verb heuristic) — a remainder that's itself just a
   bare restatement of the title/subtitle, or a bare noun phrase with no
   comparison/computation/relationship language, contributes nothing, the
   same way an empty remainder always has. A caption's naturally-written
   sentences (never opener-/citation-prefixed) are NOT subject to this
   extra scrutiny — only prefix-stripped remainders are.
2. `_CAPTION_LABELED_CITATION_RE` now also recognizes a bare `"Data:"`
   label (previously only `"Source:"`/`"Data source:"`/`"Dataset:"`),
   stripping it the same way and grading what's left via the same
   `_stripped_remainder_is_vacuous` check — the stale code comment that
   described the now-superseded "data" stopword-list defense mechanism
   was also corrected.
3. `_stem`'s trailing-`s` strip was mangling stopwords that end in "s" but
   aren't plurals ("across" -> "acros", "this" -> "thi"), so they no
   longer matched the (unstemmed) stopword set and leaked through as
   counted content words. Fixed by checking the raw word against the
   stopword set BEFORE stemming, in addition to (not instead of) checking
   the stemmed form (which round-4 added to catch plurals of stopwords).
   Verified zero corpus-verdict impact in isolation (see below).

Restored/added tests in `tests/test_caption_not_generic.py`: the deleted
`test_generic_template_opener_fails` (verdict-level, the exact caption
above), a new verdict-level test sweeping every recognized opener verb
against a vacuous remainder, the inverted `"Data:"` test corrected back to
asserting FAIL, and direct coverage of the stemming/stopword-order fix.

**Isolated before/after impact of just this round's fixes** (same
72-candidate methodology; "before" = the round-4 numbers already in the
table above, "after" = post round-5 fix):

| Skill | Before (round-4) mean pts/3 | After (round-5) mean pts/3 | Mean points delta | Before pass-rate | After pass-rate |
|---|---|---|---|---|---|
| `house` | 2.667 | 2.667 | +0.000 | 88.9% | 88.9% |
| `prose` | 2.833 | 2.833 | +0.000 | 94.4% | 94.4% |
| `scripts` | 2.833 | 2.667 | **-0.167** | 94.4% | 88.9% |
| `creator` | 0.500 | 0.333 | **-0.167** | 16.7% | 11.1% |
| **All 72** | **2.208** | **2.125** | **-0.083** | 73.6% | 70.8% |

Exactly 2 of the 72 candidates changed verdict, and both are the two
regressions identified above, both correctly flipping back from an
incorrect 3/3 to the correct 0/3 (not new failures — a restoration of the
pre-round-4 correct verdict for each):

- `scripts/islands_sizes/repeat_2` — `"Data shows the area of islands
  across the world."` — correctly fails the generic-opener check again.
- `creator/sp500_monthly_performance/repeat_1` — `"Data: S&P 500 daily
  prices and volumes, 2010-2015."` — correctly fails as a bare, insight-free
  citation again.

No other candidate's verdict changed. Fix 3 (the stemming/stopword-order
fix) was verified in isolation to have **zero verdict impact** on any of
the 72 candidates — several candidates' detail messages now report
slightly different word counts/overlap percentages (since "across"/"this"
no longer inflate the content-word count), but no pass/fail outcome moved
because of Fix 3 alone; the two flips above are entirely attributable to
Fixes 1 and 2. All 6 ground truths' own captions still pass at 3/3. As
with prior rounds, this is a scoped, non-committed script output — the
stored `eval-results/**` files still reflect the PRE-#116
`check_caption_keywords` scores until a full harness regenerate lands.
