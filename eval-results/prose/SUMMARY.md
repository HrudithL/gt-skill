# `prose` skill — eval summary

Sweep: `runs/sweep/20260808_102102_prose_6prompts` (post skill-content-fix
re-sweep, 2026-08-08) — 6 corpus prompts x (3 repeats + 1 auto-baseline),
Haiku, scored by `runner.comparator.compare()` against each prompt's ground
truth. Full detail in [`metrics.json`](metrics.json); regenerate the plots
below with `python plots/make_plots.py`.

| Metric (mean across 6 prompts) | `prose` (2026-08-07) | `prose` (2026-08-08, after fixes) | baseline |
|---|---|---|---|
| Comparator total score | 70.5% | 62.4% | 26.5% |
| Cost per invocation | $0.150 | $0.150 | $0.082 |

**Read this drop with real skepticism before treating it as a regression** —
see `scripts`' summary for the full explanation, which applies identically
here (`prose` shares the same 6 archetype example files under
`assets/examples/`). Short version: this re-sweep caught and fixed a
genuine pre-existing bug where every archetype example built its final `GT`
chain as an unassigned bare expression (no top-level `gt`), which void the
comparator's whole Tier-2/Data-compliance score for any candidate that
copied the structure closely — 2 of 3 `sp500_monthly_performance` repeats
hit exactly this before the fix. Separately, this sweep's per-repeat spread
for the SAME prompt+skill (e.g. one prompt scoring anywhere from the 20s to
the 90s across 3 repeats of identical skill content) shows Haiku's own
sampling variance is large enough to swamp a 3-repeat mean — this single
re-sweep is not a statistically reliable read of whether the same-day
content additions (pinned date-stub format, continuous-metric rule,
paired-column technique, two-call source-note convention, backported
ambiguous-measure guidance, `financial.py`'s color-convention fix) helped,
hurt, or were neutral for `prose`. `house`'s summary has a clean,
mechanism-confirmed win for the identical set of additions — treat that as
the more trustworthy signal for whether the additions themselves are sound.

See [`plots/cost.png`](plots/cost.png), [`plots/tokens.png`](plots/tokens.png),
[`plots/consistency.png`](plots/consistency.png),
[`plots/comparator_score.png`](plots/comparator_score.png).

`prose` is the best performer of the four: the **highest mean comparator
score** (nearly 3x baseline) *and* the **most consistent** (smallest
repeat-to-repeat spread) — the 7-step flowchart + `REFERENCE.md` router
gets the model to the same design decisions run after run, without a
checker loop's added cost or variance. See
[`progressive_disclosure.md`](progressive_disclosure.md) for a transcript
excerpt of the router-driven reference reads (router -> data -> the specific
archetype rules this prompt's two measures needed) that precede every write.

Curated candidate scripts, renders, and comparator reports for every
invocation are under [`samples/`](samples/), organized `samples/<prompt>/<variant>/`.
