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
relatively low on them: `Column-label concept-correctness` (house 55.6%,
prose 38.9%, scripts 41.2% — 16.7pp spread) and `Striping gate
correctness` (house 27.8%, prose 38.9%, scripts 55.6% — 27.8pp spread).
These show real cross-skill variation — removing them would erase
evidence that other skills currently handle these differently/better than
`prose`, not evidence the check is unreasonable for everyone. Likewise
`Computed/derived value correctness` (house 22.8%, prose 63.3%, scripts
50.6% — 40.6pp spread, the single largest in the whole comparator) stays:
it reveals a real, important defect in `house`'s value-correctness, exactly
the kind of signal this comparator exists to surface.

Both passes' exact checks and mechanism (full deletion) were confirmed
with the user via AskUserQuestion before any code changed.

**Combined effect**: Formatting-compliance ceiling 61 → 53 → 44 pts.
Data-compliance unaffected throughout. Combined: 114 → 106 → 97 pts.

**Every number below re-scores the exact same already-existing candidates**
(the same sweep this file has always reported on) **against the updated
comparator — nothing was re-generated or re-executed.** Removing a check is
a pure subtraction of that check's fixed points from whichever bucket it
belonged to (confirmed by grep — none of the 6 removed checks' underlying
fields are read by any other check), so holding the candidate set fixed
isolates the comparator change as the only variable. This holds exactly
for the 20 surviving *mechanical* checks: the transform (`_apply_check_
removal.py`) only ever filters the 6 removed checks out of each
invocation's already-computed check list and re-sums, never recomputes a
surviving check's own value, so every surviving mechanical check's
points/passed/tier are byte-identical to `main`'s original data by
construction — a live dual-comparator A/B run against a first, smaller
version of this same transform (pass 1's 3 checks) already confirmed this
holds in practice, not just in theory. It holds only *approximately* for
the 4 surviving judge-backed checks' stored scores, since those were elicited by the
judge's original 7-dimension system prompt (now 4 dimensions) — a live
re-run of the judge today on the same candidates could score those
dimensions slightly differently. The transform script that produced this
data is committed at [`_apply_check_removal.py`](_apply_check_removal.py)
for auditability.

| Skill | Mean comparator score | vs. baseline | Score spread (3 repeats) | Mean cost/invocation |
|---|---|---|---|---|
| `prose` | **75.6%** | +51.0pp | **11.1pp** (most consistent) | $0.150 |
| `scripts` | 69.9% | +47.6pp | 23.7pp (least consistent) | **$0.188** (most expensive) |
| `house` | 60.0% | +38.7pp | 18.5pp | **$0.110** (cheapest of the 3 real skills) |
| `creator` | 21.7% | **-3.2pp** | 18.1pp | $0.095 |
| baseline (no skill) | 21.3-24.9%\* | — | n/a (1 run) | $0.060-$0.089\* |

\*baseline varies slightly per skill's sweep because each sweep's baseline
run is a separate invocation (same prompts, no skill mounted, different
sampling) — see each skill's `plots/cost.png` / `comparator_score.png` for
the per-skill baseline actually used in that comparison.

## Findings

- **The ranking is unchanged across both passes**: `prose` > `scripts` >
  `house` > `creator`, the same order this file has always reported.
  Absolute scores moved (mostly up — removing checks nothing/nobody-
  discriminating could pass raises everyone's floor — except `creator`,
  which moved slightly *down* because it happened to score disproportionately
  well, relative to its own dismal average, on exactly pass 2's 3 removed
  checks), but the relative order never changed. Don't read a skill
  recommendation into the absolute numbers moving; read it into the
  (unchanged) order.
- **`prose` still wins on both quality and consistency.** The full 7-step
  flowchart + `REFERENCE.md` router produces the highest mean score and the
  smallest repeat-to-repeat spread of the three real skills, at a mid-range
  cost.
- **`scripts`' checker loop is a double-edged sword.** It pushes the mean
  score above `house`'s, but the loop itself (how many issues it catches,
  how many fix attempts it takes) still makes `scripts` both the most
  expensive and the least consistent of the three real skills.
- **`house` is the cheap, decent option.** No flowchart, no checker loop —
  one worked reference script + a rules file — costs the least of the three
  real skills for a real (if smaller) quality gain over baseline.
- **`creator` still loses to no skill at all.** Its score moved the
  "wrong" direction across these passes (down, not up) precisely because
  its few relative strengths were concentrated in checks that turned out
  not to discriminate skill quality at all — everything that's actually
  hard, it still doesn't do. It remains *below* baseline (21.7% vs. 24.9%,
  -3.2pp). See `creator/SUMMARY.md` and `creator/progressive_disclosure.md`
  for one concrete, falsifiable partial explanation (shallower, less-routed
  reference reading), not a full diagnosis.

## Which skill is best overall

**`prose`** — highest mean score and most consistent of the four, before
and after both consensus-tuning passes. `house` is the right pick when
cost matters more than the last several points of quality. `scripts`'
checker loop earns a higher mean than `house`'s, but costs the most and is
the least consistent of the three real skills — its mean-score edge over
`house` doesn't come with a consistency edge too. `creator` is not yet a
real contender.

## Layout

```
eval-results/
  _lib.py                     shared metrics-extraction helpers (see its docstring)
  _apply_check_removal.py     the one-off transform that produced both consensus-tuning passes' data
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
`ANTHROPIC_API_KEY` in `.env` for the judge calls).
