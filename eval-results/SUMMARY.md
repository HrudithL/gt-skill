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
ceiling 61 → 53 pts; combined 114 → 106 pts) — they were measuring something
no current skill achieves, not a real quality gap. Checks with real
skill-to-skill spread were kept even where the average is also low (e.g.
"Render mechanics" varies sharply by skill) — that spread *is* the signal
the comparator exists to surface.

**Every number below re-scores the exact same already-existing candidates**
(the same sweep this file previously reported on) **against the updated
comparator — nothing was re-generated or re-executed.** This is deliberate:
removing a check is a pure subtraction of that check's fixed points from
whichever bucket it belonged to (confirmed by grep — none of the 3 removed
checks' underlying fields are read by any other check), so holding the
candidate set fixed isolates the comparator change as the only variable.
An internal review caught an earlier draft of this file conflating "the
comparator changed" with "we also re-ran on a fresher, different set of
candidates" — that draft's numbers and its "ranking flips" claim were wrong
and are not reflected here.

| Skill | Mean comparator score | vs. baseline | Score spread (3 repeats) | Mean cost/invocation |
|---|---|---|---|---|
| `prose` | **74.2%** | +47.3 pts | **11.0 pts** (most consistent) | $0.150 |
| `scripts` | 69.2% | +44.3 pts | 21.9 pts (least consistent) | **$0.188** (most expensive) |
| `house` | 60.4% | +37.2 pts | 16.4 pts | **$0.110** (cheapest of the 3 real skills) |
| `creator` | 23.5% | **-3.3 pts** | 18.1 pts | $0.095 |
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
  SUMMARY.md                  this file
  <skill>/
    metrics.json              full per-invocation cost/tokens/comparator-score data
    SUMMARY.md                this skill's numbers + findings
    progressive_disclosure.md real transcript excerpt showing the skill being read progressively
    plots/
      make_plots.py           regenerates the 4 PNGs below from metrics.json
      cost.png                 skill cost vs. baseline, per prompt (bar)
      tokens.png                token usage per invocation, per prompt (scatter/strip)
      consistency.png           min-mean-max comparator score across 3 repeats (range/dumbbell)
      comparator_score.png      comparator score distribution: 3 repeats vs. baseline (box)
    samples/<prompt>/<variant>/  curated table.py + table.png + comparator report.txt
```

Regenerate everything for one skill: `python eval-results/<skill>/plots/make_plots.py`
(re-runs the comparator, including one real judge API call per invocation —
needs `ANTHROPIC_API_KEY` in `.env`).
