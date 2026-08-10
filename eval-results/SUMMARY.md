# Full comparator sweep — cross-skill summary

All four skill variants (`house`, `scripts`, `prose`, `creator`), the same 6
corpus prompts, 3 repeats + an auto-baseline each (96 harness invocations
total), scored by the hybrid deterministic + LLM-judge comparator
(`runner/comparator.py` + `runner/judge.py`).
Per-skill detail, plots, and curated runs are in `house/`, `scripts/`,
`prose/`, `creator/` — see each skill's own `SUMMARY.md`.

**Comparator methodology (2026-08-09 — consensus-tuning pass):** the
comparator was originally scored against an idealized standard rather than
against what current skill-guided LLM output actually achieves. Checking
per-check pass rates across `house`/`prose`/`scripts`'s 18 non-baseline
invocations each (54 max per check) found 3 checks scoring near-zero across
*every* skill regardless of quality — not just weak for one skill, which
would be a real quality signal, but flat across all three:

| Check (removed) | Avg | house | prose | scripts |
|---|---|---|---|---|
| Hero-column formatting when nothing is colored (n=39/54 applicable) | 0.0% | 0.0% | 0.0% | 0.0% |
| Caption doesn't just restate the subtitle, judge-scored (n=52/54) | 3.9% | 0.0% | 11.8% | 0.0% |
| Stub tint + grey-budget correctness (n=54/54) | 27.8% | 33.3% | 33.3% | 16.7% |

These were removed entirely from `runner/comparator.py` (Formatting-compliance
ceiling 61 → 53 pts; combined 114 → 106 pts). Two of the three (hero-column,
caption) are a genuine near-universal 0: hero-column is 0/39 applicable
instances (only 1 of those 39 zeros is itself an execution-failure
artifact), and caption scored ≤2/5 from the judge in 67 of 69 judged
instances. **Stub tint's rationale is different, and more specific, than
"nothing can pass it"** — it actually shows real skill-to-skill spread
(16.7% to 33.3%, comparable to checks that were kept) and 15/96 invocations
passed it outright. It was removed because its zeros decompose into two
non-discriminating failure modes: 49/96 are `"ground truth requires a stub
but candidate has none"` — a missing stub, which `check_stub_existence`
(kept, unchanged) already penalizes separately, so failing this check too
was double-counting the same defect; the other 28/96 are a literal
grey-budget-violation pattern (`stub=True, striped=True -> expected
tint=False, actual=True`) that isn't really about tasteful tinting choice.
Checks with real skill-to-skill spread that *aren't* double-counting or a
mechanical artifact were kept even where the average is also low (e.g.
"Render mechanics" varies sharply by skill) — that spread *is* the signal
the comparator exists to surface.

**Every number below re-scores the exact same already-existing candidates**
(the same sweep this file previously reported on) **against the updated
comparator — nothing was re-generated or re-executed.** This is deliberate:
removing a check is a pure subtraction of that check's fixed points from
whichever bucket it belonged to (confirmed by grep — none of the 3 removed
checks' underlying fields are read by any other check), so holding the
candidate set fixed isolates the comparator change as the only variable.
This holds exactly for the 23 surviving *mechanical* checks (independently
verified: re-running `comparator.compare()` on all 96 checked-in candidates
under both the old and new comparator produces byte-identical
points/passed/tier for every one of them). It holds only *approximately*
for the 6 surviving judge-backed checks' stored scores, since those were
elicited by the judge's OLD 7-dimension system prompt (which still
mentioned `caption_quality`) — a live re-run of the judge today, on the
same candidates, would use the new 6-dimension prompt and could score
those dimensions slightly differently. An internal review caught an
earlier draft of this file conflating "the comparator changed" with "we
also re-ran on a fresher, different set of candidates" — that draft's
numbers and its "ranking flips" claim were wrong and are not reflected
here. The transform script that produced this data is committed at
[`_apply_check_removal.py`](_apply_check_removal.py) for auditability.

| Skill | Mean comparator score | vs. baseline | Score spread (3 repeats) | Mean cost/invocation |
|---|---|---|---|---|
| `prose` | **74.2%** | +47.3pp | **11.0pp** (most consistent) | $0.150 |
| `scripts` | 69.2% | +44.3pp | 21.9pp (least consistent) | **$0.188** (most expensive) |
| `house` | 60.4% | +37.2pp | 16.4pp | **$0.110** (cheapest of the 3 real skills) |
| `creator` | 23.5% | **-3.3pp** | 18.1pp | $0.095 |
| baseline (no skill) | 23.2-26.9%\* | — | n/a (1 run) | $0.060-$0.089\* |

\*baseline varies slightly per skill's sweep because each sweep's baseline
run is a separate invocation (same prompts, no skill mounted, different
sampling) — see each skill's `plots/cost.png` / `comparator_score.png` for
the per-skill baseline actually used in that comparison.

## Findings

- **Every skill's score rose** (house +2.7pp, prose +3.7pp, scripts +4.2pp,
  creator +1.8pp) **and the ranking did not change**: `prose` > `scripts` >
  `house` > `creator`, same order as before this pass. This is the expected,
  mechanical result of removing 3 checks nothing could pass — it raises
  everyone's floor roughly in proportion to how much those specific checks
  were dragging each skill's own average down, not a reshuffling of who's
  actually better. Don't read a skill recommendation into the fact that the
  numbers went up; read it into the (unchanged) order.
- **`prose` still wins on both quality and consistency.** The full 7-step
  flowchart + `REFERENCE.md` router produces the highest mean score and the
  smallest repeat-to-repeat spread of the three real skills, at a mid-range
  cost. Its lead over the runner-up narrowed slightly (5.5pp → 5.0pp over
  `scripts`) — the checks removed happened to be ones `prose` did
  comparatively less badly on than the average of its own other checks.
- **`scripts`' checker loop is a double-edged sword.** It pushes the mean
  score above `house`'s, and its lead over `house` widened slightly (7.3pp
  → 8.8pp) — but the loop itself (how many issues it catches, how many fix
  attempts it takes) still makes `scripts` both the most expensive and the
  least consistent of the three real skills.
- **`house` is the cheap, decent option.** No flowchart, no checker loop —
  one worked reference script + a rules file — costs the least of the three
  real skills for a real (if smaller) quality gain over baseline. Its
  spread (16.4pp) sits between `prose`'s (still lowest, most consistent,
  11.0pp) and `scripts`' (still highest, least consistent, 21.9pp) — same
  ordering as before this pass.
- **`creator` still loses to no skill at all.** Its score moved the least
  of the four (+1.8pp) and it remains *below* baseline (23.5% vs. 26.8%,
  -3.3pp) — removing 3 universally-hard checks didn't change this
  conclusion. See `creator/SUMMARY.md` and `creator/progressive_disclosure.md`
  for one concrete, falsifiable partial explanation (shallower, less-routed
  reference reading), not a full diagnosis.

## Which skill is best overall

**`prose`** — highest mean score and most consistent of the four before this
pass, and still both after it; the consensus-tuning pass changed everyone's
absolute numbers but not this conclusion. `house` is the right pick when
cost matters more than the last several points of quality. `scripts`'
checker loop costs the most for a smaller consistency edge over `house`
than its score alone suggests. `creator` is not yet a real contender.

## Layout

```
eval-results/
  _lib.py                     shared metrics-extraction helpers (see its docstring)
  _apply_check_removal.py     the one-off transform that produced this consensus-tuning pass's data
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
the confound an internal review caught and this pass had to correct (see
above). It will also hard-fail for `creator`, whose original sweep
directory has been deleted. If you need to re-apply a comparator change to
the data already committed here without changing candidates, use
`_apply_check_removal.py` as a template (point-subtraction on the existing
`metrics.json`, not a live re-run) rather than `make_plots.py`. Only use
`make_plots.py` when you deliberately want to score a fresh sweep from
scratch (needs `ANTHROPIC_API_KEY` in `.env` for the judge calls).
