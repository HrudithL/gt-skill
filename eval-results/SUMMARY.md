# Full comparator sweep — cross-skill summary

All four skill variants (`house`, `scripts`, `prose`, `creator`), the same 6
corpus prompts, 3 repeats + an auto-baseline each (96 harness invocations
total), scored by the hybrid deterministic + LLM-judge comparator
(`runner/comparator.py` + `runner/judge.py`, merged to `main` in PR #79).
Per-skill detail, plots, and curated runs are in `house/`, `scripts/`,
`prose/`, `creator/` — see each skill's own `SUMMARY.md`.

| Skill | Mean comparator score | vs. baseline | Score spread (3 repeats) | Mean cost/invocation |
|---|---|---|---|---|
| `prose` | **70.5%** | +45.7 pts | **11.1 pts** (most consistent) | $0.150 |
| `scripts` | 65.0% | +42.1 pts | 22.1 pts (least consistent) | **$0.188** (most expensive) |
| `house` | 57.7% | +36.4 pts | 15.8 pts | **$0.110** (cheapest of the 3 real skills) |
| `creator` | 21.7% | **-3.0 pts** | 16.7 pts | $0.095 |
| baseline (no skill) | 21.3-24.8%\* | — | n/a (1 run) | $0.060-$0.089\* |

\*baseline varies slightly per skill's sweep because each sweep's baseline
runs are separate invocations (same prompts, no skill mounted, different
sampling) — see each skill's `plots/cost.png` / `comparator_score.png` for
the per-skill baseline actually used in that comparison.

## Findings

- **`prose` wins on both quality and consistency.** The full 7-step
  flowchart + `REFERENCE.md` router produces the highest mean score and the
  smallest repeat-to-repeat spread of the three real skills, at a mid-range
  cost.
- **`scripts`' checker loop is a double-edged sword.** It pushes the mean
  score above `prose`'s in aggregate, but the loop itself (how many issues
  it catches, how many fix attempts it takes) makes `scripts` both the most
  expensive and the least consistent skill.
- **`house` is the cheap, decent option.** No flowchart, no checker loop —
  one worked reference script + a rules file — costs the least of the three
  real skills for a real (if smaller) quality gain over baseline.
- **`creator` currently loses to no skill at all.** This is the headline
  result of this sweep: the skill-creator-produced candidate mounted by
  `creator` scores *below* the baseline on average, while still costing
  more per invocation than baseline. See `creator/SUMMARY.md` and
  `creator/progressive_disclosure.md` for one concrete, falsifiable partial
  explanation (shallower, less-routed reference reading), not a full
  diagnosis.

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
