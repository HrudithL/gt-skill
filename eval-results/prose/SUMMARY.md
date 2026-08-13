# `prose` skill — eval summary

Sweep: `runs/sweep/20260812_212011_prose_6prompts` — 6 corpus prompts x (3
repeats + 1 auto-baseline), Haiku, scored by `runner.comparator.compare()`
against each prompt's ground truth. Full detail in [`metrics.json`](metrics.json).

**This is the third and final sweep round, run after three landed fixes,
in order:** (1) the skill-realignment + comparator-generalization effort
(PRs #93–#101 — redesigned ground truths, removed the ≤2-measure cap on
colored-measure credit, made the header band/stub tint fixed-and-universal,
made striping apply by default); (2) the `runner/convergence.py`
Header-branding/Stub-tint parsing fix (PR #102 — fixed misreading comments
as calls, taking the first matching call instead of the last, and a
hue-defaulting bug that made a correctly-styled header score as missing);
and (3) the `hairlines`/`finalize` helper-detection fix (PR #103 — a
`house`-specific parsing gap; see `house/SUMMARY.md`, zero affected checks
for `prose`). All three landed on `main` before this sweep ran. **This
supersedes round 2's numbers for the same reason round 2 superseded round
1: a real scoring bug got fixed, not a skill change** — there is no valid
"before → after %" to compute across rounds for `prose` (the denominator,
check set, and parsing all changed at least once in between); see the
top-level [`SUMMARY.md`](../SUMMARY.md)'s "Data refresh" section for the
full history.

**All 18 invocations scored this round** — round 2's one crash
(`sp500_monthly_performance/repeat_2`, hitting `check_caption_keywords`'s
still-open `TypeError` on a non-literal caption; see below) didn't recur
for `prose` this round (different candidates, different caption text). The
same bug did hit once elsewhere this round, on a different skill/prompt —
see `scripts/SUMMARY.md`. It remains a real, still-open bug in
`runner/comparator.py`, out of scope to fix here (touches `runner/`).

| Metric (mean across 18 scored invocations) | `prose` skill | baseline (no skill) |
|---|---|---|
| Comparator total score | **79.0%** | 17.5% |
| Data-compliance split | 78.5% (651/829 pts) | — |
| Formatting-compliance split | 79.1% (625/790 pts) | — |
| Cost per invocation | $0.182 | $0.076 |
| Repeat-to-repeat spread (mean across 6 prompts) | 23.5 points | n/a (1 run) |

See [`plots/cost.png`](plots/cost.png), [`plots/tokens.png`](plots/tokens.png),
[`plots/consistency.png`](plots/consistency.png),
[`plots/comparator_score.png`](plots/comparator_score.png).

`sp500_monthly_performance` is the hardest prompt for `prose` by a wide
margin (62.1% mean, vs. 70–91% for every other prompt) — consistent with
it being the hardest prompt for `scripts` and `house` too (see the
top-level `SUMMARY.md`). `prose`'s data-compliance (78.5%) and
formatting-compliance (79.1%) splits are close together this round, unlike
round 2's noticeable gap between them.

## What the comparator still fails `prose` on

Computed across the 18 scored (non-baseline) invocations, sorted by how
often each check fails or partially fails:

1. **Title quality (judge)** — 5/6 (83%) fail or partially fail, mean
   72.2%, concentrated on `islands_sizes` and `gtcars_top10_by_country`.
   - `[islands_sizes/repeat_2]` "judge score 4/5 -- The candidate title
     'World Islands by Size' is accurate and captures the core framing ...
     However, it is slightly less specific than the ground truth's
     'Islands of the World, by Size' and misses the directional framing
     that the ground truth's caption emphasizes ('largest to smallest')."
2. **Header branding (deep navy, bold, white text)** — 15/18 (83%) fail or
   partially fail, mean 40.0%. `prose` hand-writes the header band inline
   per candidate rather than calling a shared, mandatory helper (the way
   `house`/`scripts` do) — so it's the one place the model's own
   consistency, not the comparator, is the bottleneck: several repeats
   drop the background color, the bold weight, or both entirely.
   - `[gtcars_hp_price/repeat_1]` "header background: expected #08306B,
     got None (MISMATCH); column_labels_font_weight: expected bold, got
     None (MISMATCH); column-label text color: expected white, got None
     (MISMATCH)" — the candidate's `tab_header()` call sets only
     title/subtitle, no header-band styling at all.
   - `[gtcars_hp_price/repeat_2]` "column-label text color: expected white,
     got None (MISMATCH)" — background/bold present, just the text-color
     half of the band forgotten.
3. **Caption keyword coverage** — 15/18 (83%) fail or partially fail, mean
   61.1%.
   - `[gtcars_hp_price/repeat_1]` "3/6 caption-keyword rules satisfied;
     caption missing: ['bentley', 'corvette', "don't move together"]" —
     the same specific-outlier-naming gap seen across all three skills on
     this exact prompt.
4. **Column set shown vs. hidden** — 14/18 (78%) fail or partially fail,
   mean 54.2%.
   - `[gtcars_hp_price/repeat_1]` "visible-column overlap 0.50
     (candidate-only=['Car'], missing=['car']); value-matched renamed
     columns: {'hp': 'Horsepower', 'msrp': 'Price'}" — a rename/restructure
     the matcher can only partially reconcile.
5. **Column order quality (judge)** — 4/6 (67%) fail or partially fail,
   mean 58.3%, and **Signed-percent force_sign correctness** — 4/6 (67%),
   mean 33.3%, always a full miss.
   - `[islands_sizes/repeat_1]` "judge score 2/5 -- The candidate sorts
     alphabetically by island name ... rather than by descending size as
     shown in the ground truth ... This directly undermines the prompt's
     'by Size' directive."
   - `[sp500_monthly_performance/repeat_1]` "0/1 signed percent columns use
     force_sign=True; missing/wrong on: ['pct_change']" — a diverging
     (crosses-zero) percent column rendered without an explicit `+` sign.
6. **Stripe color (neutral grey)** — 11/17 (65%) fail, mean 35.3%, always a
   full miss (`[gtcars_hp_price/repeat_1]` "expected #F6F6F6, got None") —
   striping applied without the house-neutral stripe color specifically.
7. **Computed/derived value correctness** — 8/18 (44%) fail or partially
   fail, mean 70.0%, and **fmt_\* per column semantic type** — 8/18 (44%),
   mean 66.7% — both track the same underlying misses as #4 above
   (wrong/missing columns can't be formatted or value-matched correctly if
   they were never emitted under a matchable name).
   - `[airquality_monthly_summary/repeat_1]` "0/3 columns formatted per
     their semantic type; not covered (missing, hidden, or wrong format):
     ['avg_temp', 'avg_wind', 'avg_ozone']"

`Frame + hairlines + dividers` (22% fail, mostly partial, mean 92.6%) and
everything below it passes reliably (`Render mechanics`, `Color
mechanics`, `Grouping existence`, `Striping gate correctness` — all
100%).

See [`progressive_disclosure.md`](progressive_disclosure.md) for a
transcript excerpt of the router-driven reference reads (router -> data ->
the specific archetype rules this prompt's two measures needed) that
precede every write.

Curated candidate scripts, renders, and comparator reports for every
invocation are under [`samples/`](samples/), organized `samples/<prompt>/<variant>/`.

## Round 4 (2026-08-13) — routing ambiguity + baseline-masking docs fixed

Fresh sweep (`runs/sweep/20260813_080331_prose_6prompts`), run after `main` had all
five rounds of fixes merged: `REFERENCE.md`'s Top-N-vs-Ordered-magnitude routing
ambiguity (an earlier sweep's repeat had picked `full_row_highlight.md` for a "top 10
most expensive" table and filled 100% of rows, violating that file's own cap);
`data.md` was missing the zero/negative-baseline percent-masking gotcha entirely.

| Metric | This round | Round 3 |
|---|---|---|
| Mean score | **81.7%** | 79.0% |
| Mean repeat spread | 10.3pp | 23.5pp |
| Mean cost | $0.190 | $0.182 |

Per-prompt means: `gtcars_hp_price` 93.7%, `airquality_monthly_summary` 93.4%,
`islands_sizes` 92.5%, `towny_growth_trends` 86.5%, `gtcars_top10_by_country` 70.9%,
`sp500_monthly_performance` 53.1% (still the hardest — same ground-truth
month-label-format ambiguity noted in the top-level `SUMMARY.md`).

`gtcars_top10_by_country` had the widest single-prompt spread (28.9pp: 57.7%, 86.6%,
68.4%) — the 57.7% repeat used the bare `model` column as the stub instead of the
documented `mfr + model` composite (`data.md`'s own worked example is this exact
dataset), producing row-identity mismatches the comparator can't reconcile (e.g. a
Lamborghini "aventador" mismatching the ground truth's "ferrari laferrari" once names
don't line up); the other two repeats on the same prompt built the composite stub
correctly. Sampling variance on a small repeat count, not a mechanical bug.
