# Full comparator sweep — cross-skill summary

All four skill variants (`house`, `scripts`, `prose`, `creator`), the same 6
corpus prompts, 3 repeats + an auto-baseline each (96 harness invocations
total), scored by the hybrid deterministic + LLM-judge comparator
(`runner/comparator.py` + `runner/judge.py`).
Per-skill detail, plots, and curated runs are in `house/`, `scripts/`,
`prose/`, `creator/` — see each skill's own `SUMMARY.md`.

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

**Comparator bug fixes (2026-08-11, after the refresh above):** two bugs
were fixed, applied as a pure mechanical-check recomputation against the
SAME candidates already reported on above (no re-execution beyond what's
needed to re-derive affected checks' inputs, no fresh judge calls).
`creator` could not be recomputed at all (its raw sweep directory no
longer exists) and is carried forward unchanged.

1. `check_render_mechanics` was scoring 0/2 for any candidate that
   renders via a bare `finalize(gt, ...)` statement rather than
   `gt = gt.gtsave(...)` — `_stmt_targets_name` compared the call's
   *function name* ("finalize") against the exported variable name
   ("gt") instead of checking whether "gt" is the call's first argument,
   an equality that could never hold. 16 of `house`'s 24 invocations and
   7 of `scripts`' used that pattern and were false-negative-scored on
   this one check; `prose` and `creator` had zero.
2. Separately, `runner/execution_tier.py` and `runner/convergence.py`'s
   no-render stubs for `GT.gtsave`/`GT.save` returned `None` instead of
   `self`, breaking the (different, narrower) `gt = gt.gtsave(...)`
   *reassignment* idiom specifically. `scripts/towny_growth_trends/
   repeat_1`'s candidate used exactly that idiom and failed Tier-2
   execution entirely as a result (scored 21/81, 25.9%, across *nine*
   checks) even though its rendered PNG was completely fine — this was
   the single largest outlier in the whole `scripts` dataset. Fixed;
   that invocation now scores normally, which also sharply reduced
   `scripts`' own repeat-to-repeat spread (23.8pp -> 16.9pp), not just
   its mean.

The table below reflects both fixes.

| Skill | Mean comparator score | vs. baseline | Score spread (3 repeats) | Mean cost/invocation |
|---|---|---|---|---|
| `prose` | **74.9%** | +49.2pp | **10.6pp** (most consistent) | $0.167 |
| `house` | 69.3% | +42.8pp | 18.2pp (least consistent) | $0.117 |
| `scripts` | 66.2% | +41.5pp | 16.9pp | **$0.175** (most expensive) |
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
on 2026-08-09 data. Its cost figure is the only one here that's cheaper
than a real skill by construction of its A/B design, not evidence of
efficiency — it's a candidate skill under evaluation, not a promoted one.

## Findings

- **`prose` wins, on replication rather than this sweep's margin alone.**
  Its 5.6pp lead over the runner-up here is *smaller* than either
  runner-up's own repeat-to-repeat spread (`house`'s 18.2pp, `scripts`'
  16.9pp) — by this file's own "gap smaller than either skill's own
  spread means don't call it settled" standard, a single sweep's 5.6pp
  isn't decisive on its own either. What makes `prose` the confident pick
  isn't this one number, it's that it led `house` specifically by a
  comfortable margin on *both* sweeps this file has ever measured (15.6pp
  on 2026-08-07, 5.6pp here) — two independent sweeps agreeing, even at
  different margins, is real signal in a way one sweep's raw gap over
  whichever skill happens to be runner-up that week isn't.
- **`house` and `scripts` are genuinely close, and which one is "least
  consistent" has flipped twice as bugs got fixed** — worth naming
  plainly since this file's own prior versions asserted the opposite. On
  the raw fresh sweep, `scripts` trailed `house` by 4.8pp and was both
  the most expensive AND least consistent (23.8pp spread) of the three
  real skills. Fixing the render-mechanics detection bug (above) widened
  that gap to 6.0pp without changing `scripts`' consistency at all — that
  fix affected both skills similarly. Fixing the separate `gtsave`-stub
  bug then did something the first fix didn't: it repaired one severely
  broken `scripts` invocation that had been dragging down BOTH its mean
  AND its own spread simultaneously, narrowing the gap back to 3.1pp
  *and* making `scripts` (16.9pp) more consistent than `house` (18.2pp).
  Net effect of both fixes together: `house` still leads on mean score,
  but by less than the raw sweep suggested, and `scripts` is no longer
  the least consistent of the three — `house` is. Treat the `house`-vs-
  `scripts` mean-score ordering as narrow and sweep-dependent, not
  settled; the consistency ordering, now that it isn't being distorted by
  a since-fixed execution bug, is a fairer comparison than it was before.
- **`scripts` remains the most expensive of the three real skills** —
  the checker loop's cost is a structural property of running it at all,
  unaffected by either bug fix above. Its benefit (a higher mean score)
  is real on this sweep but, per the point above, narrower and less
  certain than previously reported.
- **`house` remains the cheap, decent option** — no flowchart, no
  checker loop, a real and competitive quality gain over baseline for the
  lowest cost of the three real skills, even though it's now the least
  consistent of the three by a small margin.
- **`creator` still loses to no skill at all.** -3.2pp behind baseline,
  unchanged in direction from every prior measurement of it. See
  `creator/SUMMARY.md` and `creator/progressive_disclosure.md` for one
  concrete, falsifiable partial explanation (shallower, less-routed
  reference reading), not a full diagnosis.

## Which skill is best overall

**`prose`** — highest mean score on every sweep this file has ever
reported, under every version of the comparator, and its lead over
`house` specifically replicates across both the 2026-08-07 and 2026-08-09
sweeps (not just a single measurement or a since-fixed bug). `house` vs.
`scripts` is genuinely close and sweep-dependent on mean score, with their
relative consistency having flipped as bugs were fixed (see Findings) —
pick `house` when cost is the deciding factor, `scripts` only if its
checker loop's occasional extra points are worth its reliably-higher
cost. `creator` is
not yet a real contender.

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
