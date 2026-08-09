# `scripts` skill — eval summary

Sweeps: `runs/sweep/20260808_102053_scripts_6prompts` (round 2, after the
archetype `gt=` bug fix) and `runs/sweep/20260808_190400_scripts_6prompts`
(round 3, independent second sample of the SAME final content — no code
changed between rounds 2 and 3 for `scripts`) — 6 corpus prompts x (3
repeats + 1 auto-baseline) each, Haiku, scored by
`runner.comparator.compare()`. `metrics.json`/`samples/` in this directory
reflect round 3 only (regenerating overwrites, it doesn't pool); round 2's
numbers are preserved here as text since they're an equally valid
independent sample of the same code.

| Metric (mean across 6 prompts) | round 1 (2026-08-07) | round 2 | round 3 | **pooled (rounds 2+3, n=36)** |
|---|---|---|---|---|
| Comparator total score | 65.0% | 52.7% | 60.1% | **56.4%** |
| Cost per invocation | $0.188 | $0.164 | $0.183 | — |

**Pooling two independent samples of the identical final content still
lands below round 1's 65.0%, not above it — this is the one result in this
verification round that does NOT clearly read as an improvement.** Three
things are true at once here, and none of them cancels the others out:

1. **Genuine noise is real and large.** The SAME prompt+skill combination
   swung 40-65 points across its own 3 repeats within a single sweep (e.g.
   round 3's `sp500_monthly_performance`: 77.2% / 71.3% / 21.6%). Pooling to
   n=36 narrows this but doesn't eliminate it.
2. **A second, separate comparator-defect finding, discovered during this
   verification round, is NOT yet fixed in the data these numbers reflect.**
   `great-tables-ci` has its own `gt_consistency.py` wrapper module (a
   pre-existing convention, distinct from anything this whole effort had
   touched until now) whose `finalize()` some candidates reach for — and a
   bare `finalize(gt, ...)` statement is invisible to the comparator's
   render-mechanics check for the same reason it was for `house` (see the
   top-level `SUMMARY.md`'s verification report for the full root-cause).
   Round 3's "Render mechanics" check reads 27.8% (was 61% originally) —
   this is now fixed in `references/scripts.md` (commit after this sweep),
   **not yet re-verified via a fresh sweep** (budget exhausted this round).
3. The archetype `gt=` bug (fixed before round 2) genuinely was a real,
   separate improvement — confirmed by `prose`'s render-call failures
   dropping once fixed.

**Bottom line: `scripts`' net effect from this round's content additions is
genuinely inconclusive, not confirmed-negative.** The render-mechanics
defect alone plausibly explains several points of round 3's apparent
shortfall on its own (it's a 2-point mechanical check that misfires on a
large fraction of samples, in a 104-point rubric) — but that hypothesis
itself needs a follow-up sweep to confirm, which this round's budget
doesn't allow. Recommend re-testing with the render-mechanics fix in place
before drawing a final conclusion on `scripts` specifically.

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
