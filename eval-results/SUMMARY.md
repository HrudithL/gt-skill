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
per-check pass rates across `house`/`prose`/`scripts`'s 6-prompt sweeps (54
non-N/A instances per check) found 3 checks uniformly near-zero across
*every* skill regardless of quality — not just weak for one skill, which
would be a real quality signal, but flat-lined for all three:

| Check (removed) | Avg | house | prose | scripts |
|---|---|---|---|---|
| Hero-column formatting when nothing is colored | 7.5% | 0% | 15% | 7% |
| Caption doesn't just restate the subtitle (judge) | 14.8% | 6% | 28% | 11% |
| Stub tint + grey-budget correctness | 24.1% | 33% | 28% | 11% |

These were removed entirely from `runner/comparator.py` (Formatting-compliance
ceiling 61 -> 53 pts; combined 114 -> 106 pts) — they were measuring something
no current skill achieves, not a real quality gap. Checks with real
skill-to-skill spread were kept even where the average is also low (e.g.
"Render mechanics": 0%/97%/39% across house/prose/scripts) — that spread
*is* the signal the comparator exists to surface. **Every number below is
under the new, consensus-tuned scoring and is not comparable to this file's
pre-2026-08-09 numbers.**

| Skill | Mean comparator score | vs. baseline | Score spread (3 repeats) | Mean cost/invocation |
|---|---|---|---|---|
| `prose` | **74.8%** | +46.9 pts | **10.4 pts** (most consistent) | $0.167 |
| `house` | 67.2% | +39.7 pts | 17.2 pts | **$0.117** (cheapest of the 3 real skills) |
| `scripts` | 63.2% | +36.0 pts | 22.8 pts (least consistent) | **$0.175** (most expensive) |
| `creator` | 18.3% | +1.6 pts | 3.3 pts | $0.095 |
| baseline (no skill) | 16.7-27.9%\* | — | n/a (1 run) | $0.065-$0.090\* |

\*baseline varies per skill's sweep because each sweep's baseline run is a
separate invocation (same prompts, no skill mounted, different sampling);
`creator`'s baseline is additionally from an older (2026-08-07) sweep whose
raw run data no longer exists to refresh (see `creator/SUMMARY.md`) — see
each skill's `plots/cost.png` / `comparator_score.png` for the per-skill
baseline actually used in that comparison.

## Findings

- **`prose` still wins on both quality and consistency** — and by a wider
  margin than before the consensus-tuning pass (74.8% vs. the runner-up's
  67.2%, up from a 5.5pp gap). The full 7-step flowchart + `REFERENCE.md`
  router produces the highest mean score and the smallest repeat-to-repeat
  spread of the three real skills, at a mid-range cost.
- **The consensus-tuning pass flips `house` and `scripts`' ranking.**
  Under the old comparator `scripts` led `house` (65.0% vs. 57.7%); under
  the new one `house` leads `scripts` (67.2% vs. 63.2%). The 3 removed
  checks were, on net, ones `house` happened to do relatively better on
  (e.g. stub tint: `house` 33% vs. `scripts` 11%) — removing them removed
  a drag that was disguising `house`'s actual standing. `scripts`' checker
  loop (`gt_check.py`) remains both the **most expensive and least
  consistent** of the three real skills — the loop itself (how many issues
  it catches, how many fix attempts it takes) is a source of run-to-run
  variance that a bigger mean score doesn't average away.
- **`house` is the cheap, now-competitive option.** No flowchart, no
  checker loop — one worked reference script + a rules file — costs the
  least of the three real skills and, under the consensus-tuned comparator,
  no longer trails `scripts`.
- **`creator` still doesn't beat baseline in any way that matters.** Its
  +1.6pp margin over baseline is well inside the noise of a 3-repeat sample
  (contrast the 3.3pp repeat-to-repeat spread), and it still costs more per
  invocation than baseline. Removing 3 checks nobody could pass moved every
  skill's score up somewhat, including baseline's — `creator` gained
  nothing relative to it. See `creator/SUMMARY.md` and
  `creator/progressive_disclosure.md` for one concrete, falsifiable partial
  explanation (shallower, less-routed reference reading), not a full
  diagnosis.

## Which skill is best overall

**`prose`** — highest mean score, most consistent, and the only skill whose
lead over the runner-up widened (not narrowed) once the comparator stopped
scoring 3 checks nothing could pass. `house` is the right pick when cost
matters more than the last few points of quality; `scripts`' checker loop
costs the most for a worse mean and worse consistency than `house` under
this scoring; `creator` is not yet a real contender.

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
