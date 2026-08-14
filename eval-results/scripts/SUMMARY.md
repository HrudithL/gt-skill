# `scripts` skill — eval summary

Sweep: `runs/sweep/20260812_212019_scripts_6prompts` — 6 corpus prompts x (3
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
`house`-specific parsing gap; see `house/SUMMARY.md` and the note below on
how it affects `scripts` at much smaller scale). All three landed on `main`
before this sweep ran. **This supersedes round 2's numbers for the same
reason round 2 superseded round 1: a real scoring bug got fixed, not a
skill change** — there is no valid "before → after %" to compute across
rounds for `scripts` in general; see the top-level
[`SUMMARY.md`](../SUMMARY.md)'s "Data refresh" section for the full
history.

**One invocation, `airquality_monthly_summary/repeat_1`, has no score.**
The same still-open `runner/comparator.py` bug documented in round 2's
`prose/SUMMARY.md` (`check_caption_keywords` crashes with `TypeError` when
a candidate's caption text isn't a static string literal) hit a different
invocation this round — this one, on `scripts`, not `prose`'s
`sp500_monthly_performance/repeat_2` from round 2 (which does not crash on
this round's `prose` data; see `prose/SUMMARY.md`). Confirms the bug is
real and candidate-text-dependent rather than tied to one specific
skill/prompt. Out of scope to fix here (touches `runner/`); this file's
mean is computed over the other 17 invocations, worked around per this
task's instructions (a small scratchpad script that catches this one
specific exception per-invocation, reusing `make_plots.py`'s own
unmodified plotting/scoring code otherwise — `runner/comparator.py` itself
was not touched).

| Metric (mean across scored invocations) | `scripts` skill | baseline (no skill) |
|---|---|---|
| Comparator total score | **82.3%** (n=17) | 22.2% |
| Data-compliance split | 75.9% (591/779 pts) | — |
| Formatting-compliance split | 88.9% (666/749 pts) | — |
| Cost per invocation | $0.184 | $0.068 |
| Repeat-to-repeat spread (mean across 6 prompts) | 20.2 points | n/a (1 run) |

See [`plots/usage.png`](plots/usage.png) and
[`plots/comparator_score.png`](plots/comparator_score.png).

`scripts` again scores highest of the three real skills on this sweep
(82.3% vs. `house`'s 79.4% and `prose`'s 79.0% — see the top-level
`SUMMARY.md` for the full cross-skill read). `sp500_monthly_performance` is
by far its hardest prompt (59.8% mean, vs. 74–96% everywhere else) — same
as for `prose` and `house`. The checker loop (`gt_check.py`) is also the
most expensive of the three real skills here ($0.184/invocation, vs. $0.182
for `prose` and $0.134 for `house`), consistent with every prior sweep this
file has reported.

## What the comparator still fails `scripts` on

Computed across the 17 scored (non-baseline) invocations, sorted by how
often each check fails or partially fails:

1. **Title quality (judge)** — 5/6 (83%) fail or partially fail, mean
   66.7%, judge-scored rather than mechanical — mostly small
   specificity gaps, not wrong titles.
   - `[islands_sizes/repeat_2]` "judge score 2/5 -- The candidate's title
     is 'Island Sizes' — generic and flat. The ground truth's title is
     'Islands of the World, by Size,' which establishes both the scope
     (world) and the ordering principle (by size)."
2. **Column order quality (judge)** — 5/6 (83%) fail or partially fail,
   mean 50.0%.
   - `[islands_sizes/repeat_1]` "judge score 2/5 -- The candidate orders
     rows alphabetically ... rather than by descending size as the ground
     truth does ... This alphabetic order breaks the core analytical
     story."
3. **Caption keyword coverage** — 14/17 (82%) fail or partially fail, mean
   60.8%.
   - `[gtcars_hp_price/repeat_1]` "3/6 caption-keyword rules satisfied;
     caption missing: ['bentley', 'corvette', "don't move together"]" —
     same specific-outlier-naming gap seen in `prose` and `house` on this
     exact prompt; this looks like a corpus-wide pattern (the model
     writes a directionally-correct caption without the two named cars
     the ground truth's caption calls out), not a `scripts`-specific one.
4. **Column set shown vs. hidden** — 12/17 (71%) fail or partially fail,
   mean 58.8%.
   - `[airquality_monthly_summary/repeat_2]` "visible-column overlap 0.00
     (candidate-only=['Month', 'Ozone', 'Temp', 'Wind'],
     missing=['avg_ozone', 'avg_temp', 'avg_wind', 'month'])" — a full
     rename the matcher can't reconcile.
5. **Column-label concept-correctness (judge)** — 4/6 (67%) fail or
   partially fail, mean 33.3%.
   - `[islands_sizes/repeat_3]` "judge score 1/5 -- The candidate's column
     header reads only 'size' while the ground truth clearly labels it
     'Size (thousand sq. mi.)' ... The candidate's subtitle says 'Land
     area in thousands of km²' — a different unit entirely."
6. **Computed/derived value correctness** — 9/17 (53%) fail or partially
   fail, mean 62.9%.
   - `[airquality_monthly_summary/repeat_2]` "0/3 canonical measures have
     a value-matching candidate column; unmatched: ['avg_temp',
     'avg_ozone', 'avg_wind']".
7. **Signed-percent force_sign correctness** — 3/6 (50%) fail, mean 50.0%,
   always a full miss.
   - `[sp500_monthly_performance/repeat_1]` "0/1 signed percent columns
     use force_sign=True; missing/wrong on: ['pct_change']" — a
     diverging (crosses-zero) percent column rendered without an explicit
     `+` sign on positive values.

`Frame + hairlines + dividers` (41% fail, mean 84.3%, entirely partial
misses) and `Render mechanics` (0% fail, mean 100%) both continue to score
well here — for `scripts`, most candidates already inline an explicit
`table_body_hlines_*` `tab_options` call and/or pass `path="table.png"`
explicitly rather than relying on the `hairlines(gt)`/`finalize(gt)`
helper defaults alone, so `scripts` was only lightly exposed to the two
comparator gaps PR #103 fixed (unlike `house`, which relies on the bare
helper forms almost exclusively — see `house/SUMMARY.md`). `Render
mechanics` moving from 11% fail (round 2) to 0% fail here is consistent
with PR #103's fix, at the smaller scale `scripts`' worked example was
ever exposed to it.

See [`progressive_disclosure.md`](progressive_disclosure.md) for a
transcript excerpt showing both halves: reference reads before writing
code, then a targeted checker-driven fix pass after.

Curated candidate scripts, renders, and comparator reports for every
invocation are under [`samples/`](samples/), organized `samples/<prompt>/<variant>/`.

## Round 4 (2026-08-13) — missing hairlines() helper + checker rule fixed

Fresh sweep (`runs/sweep/20260813_080340_scripts_6prompts`), run after `main` had all
five rounds of fixes merged: `gt_consistency.py` had `frame`/`finalize`/`heatmap`/`band`/
`stripe`/`stub_tint` helpers but no `hairlines()`, and `gt_check.py` never verified the
hairline color either — this skill silently missed the required body-row hairline on
~29% of an earlier sweep's invocations, undetected by its own "self-checking" premise.
Also fixed: the `≤30%`-cap-vs-Top-N routing gap this skill shared with `great-tables`.

| Metric | This round | Round 3 |
|---|---|---|
| Mean score | **86.0%** | 82.3% |
| Mean repeat spread | 16.4pp | 20.2pp |
| Mean cost | $0.189 | $0.184 |

**RESOLVED (2026-08-13, `chore/recompute-eval-results-post-fixes`):** the
figures above (86.0% / 16.4pp) are the final, fully-recomputed numbers,
after the deferred `normalize_id` date-matching fix and the
`check_caption_not_generic` redesign were both applied to this round's
actual committed candidates. They supersede an earlier, briefly-committed
81.5% / 16.2pp reading of this same sweep that predated that recompute —
`scripts` gained the most of the three skills (+4.5pp), since ALL 3
`sp500_monthly_performance` repeats had rendered month labels as
`"2010-01"`-style strings that `normalize_id` previously couldn't
reconcile with the ground truth's `"Jan 2010"`, flipping row-identity
(and downstream value-correctness) from a full miss to a full pass across
the board, plus a smaller, broader gain from the caption-check fix across
several other prompts. See the top-level `SUMMARY.md` for the full
three-skill picture: **`scripts` is now the top-scoring skill of the
three**, ahead of `prose` and `house`.

Per-prompt means: `gtcars_top10_by_country` 94.0%, `islands_sizes` 94.4%,
`gtcars_hp_price` 86.0%, `airquality_monthly_summary` 84.0%, `towny_growth_trends`
83.0%, `sp500_monthly_performance` 74.8% (still the hardest prompt, but no longer by
as wide a margin now that the `normalize_id` fix has landed — see "RESOLVED" above).

Two individual repeats scored far below their siblings, each from a stub-related
mistake: `gtcars_hp_price/repeat_3` (61.4% vs. 96.5%/100.0% siblings, which have
since diverged from each other too) created a stub using
`rowname_col="mfr"`, but `mfr` alone is non-unique in gtcars (multiple cars share
the same manufacturer), so the stub rows didn't match the ground truth's composite
`mfr`+`model` identifiers. `airquality_monthly_summary/repeat_1` (57.5% vs.
97.8%/96.7% siblings, which also added an unwanted column-group spanner the prompt
never asked for) forgot `rowname_col=` in the `GT(...)` constructor entirely, so no
stub was created. Both are places `gt_consistency.py`'s own worked pattern is
unambiguous and the sibling repeats on the same prompt got it right — haiku-tier
sampling variance, not a skill or checker gap.

## Round 5 (2026-08-13) — verification sweep, no new code changes

A second, independent 6-prompt sweep (`runs/sweep/20260813_161442_scripts_6prompts`)
against the exact same commit round 4's numbers above were computed from — checking
whether round 4's results (and its `gtcars_hp_price` outlier) hold up under a fresh
random draw. No code changed between round 4 and this round.

| Metric | This round | Round 4 |
|---|---|---|
| Mean score | 87.7% | 86.0% |
| Mean repeat spread | 19.2pp | **16.4pp** (worse) |
| Mean cost | $0.188 | $0.189 |

Mean score is up slightly (+1.7pp), within noise. Mean repeat spread is worse than
round 4, driven entirely by one new outlier (below) — not a general regression.

Per-prompt means: `gtcars_hp_price` 98.5%, `islands_sizes` 98.1%,
`gtcars_top10_by_country` 94.1%, `towny_growth_trends` 86.5%,
`sp500_monthly_performance` 79.0%, `airquality_monthly_summary` 69.9%.

**`gtcars_hp_price`'s composite-stub outlier does not recur, cleanly.** Round 4's
`repeat_3` scored 61.4% vs. 96.5%/100% siblings because it used the bare, non-unique
`mfr` column as the stub instead of the `mfr` + `model` composite — the exact
gtcars example PR #112 added to `data.md`. This round's three `gtcars_hp_price`
repeats score `[100.0%, 98.9%, 96.7%]` — tightly clustered. Reading all three
`table.py` files confirms all three build `df["car"] = df["mfr"] + " " +
df["model"]` and pass that as `rowname_col`, scoring 10/10 on row identity across
the board. No caveats on this one.

**A new outlier: `airquality_monthly_summary/repeat_2` scored 21.1%** vs.
91.8%/96.9% siblings — this round's widest single-prompt spread (75.8pp) and the
reason this skill's mean spread got worse, not better, this round. Its `report.txt`
shows a comprehensive, near-total failure (no stub, no colored measures, no frame,
no hairlines, no header branding, no caption — 19/90). Reading its `table.py`
confirms this is not a narrow, specific mistake: the script is 36 lines of bare
`pandas`/`great_tables` code with none of `gt_consistency.py`'s helpers imported at
all. Reading the run's own transcript
(`runs/sweep/20260813_161442_scripts_6prompts/prompts/airquality_monthly_summary/
repeat_2/transcript.json`) shows why: **the model never invoked the `Skill` tool in
this run** — its full tool sequence is `Read` (CSV) → `Write` (`table.py`) → `Bash`
(run) → `Read` (view PNG), 4 calls in 5 turns, versus `repeat_1` (14 calls) and
`repeat_3` (18 calls), both of which open with a `Skill` call before writing any
code. This reads as inherent haiku-tier sampling variance in whether the model
elects to invoke an available skill at all on a given run, not a doc or comparator
gap — the skill materials (including a copy of `gt_consistency.py` in the working
directory) were present and used correctly by both siblings on the identical
prompt.

Execution: 24/24 successful (no crashes) — see the top-level `SUMMARY.md` for the
caveat on why this isn't claimed as a rigorously-proven improvement over any pre-fix
baseline.
