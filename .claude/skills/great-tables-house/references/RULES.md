# RULES — per-data-type formatting rules

No flowchart here. Find the row below that matches your column's kind, then
open `scripts/house_table.py` and find the function/section it names — copy
and adapt that, not this file's prose.

## THE NON-NEGOTIABLE BASE — every table gets ALL of these, no exceptions

This is not a menu, and it is not conditional on whether a particular table
"seems to need it." Every table this skill produces — no matter how simple
the request looks — gets every item below. Treat this as a checklist to
run through immediately before you call `finalize()`: if any box below is
unchecked, the table isn't done yet.

1. **Title AND subtitle, both, always** — `tab_header(title=..., subtitle=...)`.
   A subtitle-less or title-less table is incomplete, full stop — there is
   no data shape simple enough to skip this.
2. **A source note, always** — `tab_source_note(source_note=...)`. If the
   actual provenance is unknown, write a generic-but-real one ("Source:
   provided dataset.") rather than omitting it — an unstated source is
   still a gap, not a neutral default. See "Two source notes, not one"
   below for the full shape of this rule.
3. **The boxed frame, always** — `frame(gt)`.
4. **Row hairlines between body rows, always** — a THIRD, separate border
   concern from the frame above: the frame is the table's outer box;
   hairlines are the thin rule *between individual body rows*, and
   `frame(gt)` does not set them (it only touches
   `table_border_{top,bottom,left,right}_*`). Write this literally, inline,
   in your own script — do not route it through a helper:
   ```python
   gt = gt.tab_options(
       table_body_hlines_style="solid",
       table_body_hlines_color="#E8E8E8",
       table_body_hlines_width="1px",
   )
   ```
   `#E8E8E8` is the fixed neutral hairline hex (see "Hex reference" below) —
   every table uses this same value, it is never themed to the table's hue.
5. **At most 2 colored measures, TOTAL, no exceptions** — `data_color`/
   `heatmap()` calls across the WHOLE table, not per column-group and not
   "one per numeric column." A table with 5 numeric columns still gets
   **at most 2** heatmaps — pick the 1–2 that are actually the point of the
   request and leave the rest uncolored (bold text at most). Three or more
   `heatmap(...)` calls in one script is always a bug, never a stylistic
   choice — if you catch yourself writing a third one, delete it. This is a
   **floor as well as a ceiling**: if the data genuinely supports 2
   distinct, request-relevant measures, color both — settling for 1 when a
   second legitimate measure is sitting right there is the same kind of
   error as coloring a 3rd. See "A related PAIR of columns can be ONE
   measure" below for the case where a second measure is easy to miss.
6. **`gt = finalize(gt, path="table.png", zoom=2.0, expand=15)`** — the
   mandatory render, always last, with `zoom=`/`expand=` passed
   **explicitly** at the call site even though they match `finalize()`'s
   own defaults, and **assigned back to `gt`**, never called as a bare
   statement. Relying on the hidden default means nothing in your own
   script records what was actually rendered with; typing them out costs
   nothing and makes the script self-documenting. The assignment isn't
   stylistic — `finalize(gt, ...)` written as a bare statement (no `gt =`)
   doesn't change what renders, but it changes nothing else either;
   writing it as `gt = finalize(...)` costs nothing and keeps the render
   call visibly part of `gt`'s own definition rather than a disconnected
   trailing statement.

Everything else in this file — a stub, a group, a spanner, a status chip,
a summary row, the striping/tint hierarchy — is genuinely conditional on
what the data and request actually call for, and stays that way. The six
items above are different in kind: they are the base every table stands
on, never something to selectively adopt. If you imported a helper
(`stripe`, `stub_tint`, `humanize_labels`, ...) and then don't end up
calling it, that's a sign you copied more of `house_table.py` than your
table needs — remove the unused import, but never let "I didn't get to
it" cost you an item on this list.

## Hex reference — copy these literally

`house_table.py`'s `PALETTE` dict holds these same values for the helper
functions to resolve at runtime — but for the two surfaces above that need
their *exact color* typed directly into your own script (the hairline, and
the heading-band background below), copy the hex string itself from this
table rather than writing `PALETTE["accent_tint"]["navy"]` or similar. A
dict lookup resolves correctly at runtime but is invisible to anything that
only reads your script's text (a reviewer skimming a diff, a linter, a
teammate grepping for a color) — the literal string is what makes the
choice legible from the code alone, the same reason `great-tables`/
`great-tables-ci`'s `palettes.md` is written as a copy-from-here table
instead of a Python constants module.

| Hue | `accent_tint` (band) | `washed` (stub) | `accent` (dark band / status chip) | `solid` (rare) |
|---|---|---|---|---|
| navy (default) | `#C9E0F0` | `#EAF0F6` | `#1B5A85` | `#22384F` |
| forest (nature/growth/money) | `#CFEAD9` | `#EAF1EC` | `#2E7350` | `#2F4A38` |
| oxblood (risk/alerts) | `#F4D6D6` | `#F5EBEB` | `#A23A3A` | `#5C2E2E` |
| espresso (historical/vintage) | `#EEDFC7` | `#F1EADD` | `#8A6238` | `#4A3A2C` |
| ochre (premium/highlight) | `#F6E8BE` | `#F5EFDC` | `#B8912E` | `#9A7B33` |
| tan (secondary warm accent) | `#EFE3CE` | `#EFE7D6` | `#9C8258` | `#8A7452` |

Neutral structural surfaces (no Big-Color hue in the table): label band
`#F0F0F0` · row stripe `#F6F6F6` · hairline `#E8E8E8` · column-label bottom
rule / frame border `#CCCCCC` · group/summary rule `#BDBDBD` · vertical
divider `#D0D0D0` · NA cell `#808080`.

## Ambiguous measures / selection criteria — pick ONE definition, STATE it

A request like "Create a table showing **population growth trends** for
the top 15 fastest-growing Ontario towns, comparing their density changes
across all census years from 1996 to 2021, with the percentage changes
between each period" mixes two different questions: what to **rank/select
by** (which 15 towns make the list), and what to **display** for those
towns once selected (which columns appear). Conflating the two — e.g.
ranking by whichever measure happens to sit nearest the superlative
phrase, regardless of which one the request actually frames as the
subject — silently answers a different leaderboard than the one asked
for. None of the *display* choices below are wrong on their own, but
picking any of them **without saying so** is why the same prompt can
render a genuinely different table each time — a real inconsistency, not
a stylistic one.

**"Pick one and state it" is not enough by itself** — two independent runs
can each honestly state a different pick and still diverge. Resolve the
pick with a deterministic precedence, in this order, then STATE the
result in the subtitle or a source note (e.g. "ranked by overall
population growth, 1996–2021"):

1. **Find the ranking/selection metric FIRST, separately from the display
   columns** — it's usually the request's stated TOPIC (the noun phrase
   right after "a table showing/of...", typically at the very start),
   not whatever measure happens to sit nearest "top N"/"fastest-growing"
   in the sentence. In "showing **population growth trends** for the top
   15 fastest-growing... towns, comparing their **density changes**...",
   the topic clause names population growth — rank/select by population
   growth. "Comparing their density changes..." is a SEPARATE instruction
   about what to display for the towns already selected, not a competing
   ranking criterion, even though it sits right next to "fastest-growing."
   An explicitly named metric ("top 15 by revenue") always wins outright,
   full stop, no further judgment needed. **If the topic measure and the
   named display columns are different things** (population to rank by,
   density to display), show BOTH as columns, not just the display one —
   a table titled "population growth trends" that contains zero
   population data reads as incomplete regardless of how well it answers
   the density question.
2. **Entity/category scope: ALWAYS match the request's term to every data
   row it plausibly covers — never the narrower literal subset.**
   "Ontario towns" in ordinary usage means "Ontario municipalities"
   generically; if the data has a type/category column (e.g. `csd_type`
   with `town`/`city`/`township`/`municipality`/`village`), include every
   type, not just the rows whose type-value literally matches the
   request's word ("town-type records only" is NOT an acceptable
   alternative reading — it's the narrower literal subset this rule
   exists to rule out). State the scope in the subtitle/source note (e.g.
   "all municipality types") so the choice is explicit, not because there
   are two valid options to pick between.
3. **A stated date range always means the FULL span, not a sub-period** —
   "from 1996 to 2021" compares `value_2021` against `value_1996`, never a
   single interior period, unless the request names that period
   specifically. Compare them as a **percentage/relative change**
   (`(value_2021 - value_1996) / value_1996`), not an absolute difference,
   whenever the request says "growth," "fastest-growing," or "rate" —
   ordinary usage of "fastest-growing" means highest relative growth rate
   (a small town doubling in size is "faster-growing" than a large city
   adding the same absolute headcount), the same convention "fastest-
   growing companies/cities" lists use elsewhere. Use absolute change
   instead only when the request explicitly asks for a magnitude ("added
   the most residents," "grew by the largest number"). **Guard the
   baseline first, against the ACTUAL data, not the measure's type in the
   abstract**: check whether any eligible row's starting value is actually
   zero/negative before doing anything about it — a measure that could
   theoretically go negative (profit) but happens to be positive for
   every eligible row needs no special handling at all; don't fall back to
   absolute change just because the measure's category is capable of it.
   When a real zero/negative baseline IS present: if the request left the
   metric **unstated** (just "growth"/"fastest-growing"), fall back to
   absolute change for the whole table and say so in the subtitle/source
   note. If the request **explicitly** asked for a rate/percentage
   specifically, don't silently swap the whole table to a different metric
   — instead **exclude only the rows with a non-positive baseline** from
   the ranking (a rate is genuinely undefined for them, not just
   inconvenient to compute) and note the exclusion, so the metric actually
   answers what was asked for the rows it can.
4. **"Show X across all periods, with changes between each period" means
   BOTH, not one or the other** — when a request separately names the
   per-checkpoint values ("density changes across all census years") AND
   the between-period deltas ("percentage changes between each period"),
   include both as separate columns rather than picking one representation
   to stand in for the other. This is a *display* choice — it never
   overrides the ranking metric found in step 1. The baseline guard from
   step 3 applies to EVERY individual period's delta too, not just the
   overall ranking figure — a period whose starting value is zero/negative
   makes that one cell's percentage undefined, and **not always in an
   obviously-broken way**: a zero baseline computes to `inf` (`sub_missing`
   does NOT catch this — confirmed by direct test: it only substitutes
   `None`/`NaN`, so an unmasked `inf` renders as the literal text
   `"inf%"`), but a *negative* baseline computes to a finite,
   sign-reversed, equally-meaningless value (confirmed: `(5 - (-10)) /
   (-10)` = `-1.5`, i.e. "-150%" — a plausible-looking number that passes
   right through `sub_missing` uncaught). Mask on the condition, not the
   symptom: compute with `np.where(start > 0, (end - start) / start,
   None)` so both the zero-baseline (`inf`) and negative-baseline
   (finite-but-meaningless) cases become `None` up front — confirmed by
   direct test to render `"—"` for both — THEN call `sub_missing`, without
   discarding the rest of that row.

This narrows the ambiguity considerably but — being a precedence over
natural-language phrasing, not a closed-form algorithm — does not
guarantee two runs land on byte-identical column choices for every
conceivable prompt; genuinely irreducible ambiguity still gets resolved by
judgment. STATING the resolved definition (not just making the same
mechanical pick) is still what makes an individual table's numbers
reproducible and defensible on its own. Do all of this BEFORE organizing
columns — it decides which columns (and which 15 rows) exist at all, not
just how they're formatted.

## Period-over-period / day-over-day metrics — compute CONTINUOUSLY, never reset at a boundary

A request like "the highest single-day gain/loss **within each month**" (or
"...within each quarter/week/year") is asking for an aggregation
**window**, not a computation boundary. It is tempting to compute the
day-over-day change ONLY from data already inside that window (e.g. treat
each month's first row as having no prior day, or recompute the delta
same-day as `close − open` to sidestep the boundary question entirely) —
resist that. The underlying process (a stock price, a sensor reading, a
running total) did not stop and restart at the window edge; it kept moving
continuously, and the window is only how you're choosing to REPORT it.

**The canonical definition, in order:**

1. Sort the FULL underlying series (every row, not the request's date
   range) chronologically first.
2. Compute the period-over-period change (`series.pct_change()`, or the
   equivalent `(this - previous) / previous`) across that FULL sorted
   series, unconditionally — a month's first day still gets a real change
   value relative to the PRIOR month's last entry, not `NaN`/undefined.
3. THEN filter down to the requested date range and group into the
   requested window.
4. Aggregate within each group (`max`/`min`/etc.) over the per-row change
   column computed in step 2 — never a value recomputed fresh from only
   that group's own rows.

**Why this is the canonical reading, not a same-day-delta alternative:** a
"day-over-day"/"single-day change" phrase names two ADJACENT observations
in the underlying continuous series — the wording itself never says
"restart counting at the window boundary." A same-day computation
(`close − open` on one row) answers a genuinely different, narrower
question (intraday movement) that the request didn't ask, even though it's
a simpler thing to compute from a single grouped-and-filtered DataFrame.
When the request's phrase is ambiguous between "day-over-day" and
"intraday," the "Ambiguous measures" precedence above still applies (pick
one, state it) — but when it specifically says day-over-day/period-over-
period, this continuous-series definition is not a discretionary pick.

## Two source notes, not one

Every table gets a source note (non-negotiable base, above) — but when the
table ALSO makes a non-obvious computational choice (the continuous-series
rule just above, an ambiguous-measure resolution, a baseline-guard
exclusion), that choice needs its OWN, separate `tab_source_note(...)` call,
distinct from the plain provenance citation:

```python
gt = (
    gt.tab_source_note(
        source_note="Single-day gain/loss use a continuous day-over-day change "
                     "across the full historical series, not reset at each month's start."
    )
    .tab_source_note(source_note="Source: provided S&P 500 dataset.")
)
```

The FIRST call states the methodology (why the numbers are what they are —
it should mention the specific words that make the choice concrete, e.g.
"continuous"/"day-over-day"/"not reset", not a vague "see methodology"
gesture); the SECOND is the plain, generic citation ("Source: ..."). Two
short notes, not one note trying to carry both jobs — a single combined
sentence tends to drop the methodology half, since the citation phrasing
("Source: ...") is the part that comes to mind first. If there's no
non-obvious computational choice to explain, the plain citation alone is
enough — don't invent a methodology note with nothing to say.

## Data-cleaning gotchas (fix these before any `fmt_*`/`data_color` call)

- A currency string like `"$1,200"` or a percent string like `"12%"` is
  still a *string* — `great_tables` formats numbers, it does not parse
  them. Strip the symbol/separators and cast to `float` first.
- A `Decimal` from a SQL result should be cast to `float` (or quantized)
  before formatting — `great_tables` doesn't know how to format `Decimal`.
- A non-zero header row (extra title/blank rows above the real header) in
  a CSV needs `header=`/`skiprows=` in the read call — check the first
  parsed row is real data, not a stray label.

## Financial (money / price / revenue / cost)

Round to 2 decimals for small amounts, 0 decimals for large/whole-dollar
figures. Always a currency symbol: `fmt_currency(columns=..., decimals=0|2)`.
A single neutral magnitude column is the sequential **Blues** heatmap hero —
`heatmap(gt, "revenue", kind="sequential", hue="neutral")` — see `revenue` in
`house_table.py` — **only** when it's the hero measure the request is
actually about. Otherwise leave it uncolored (bold text at most).

## Percent / rate / change

`fmt_percent(columns=..., decimals=1)`. Decide once whether the data is
fractional (`0.12`) or already-scaled (`12`, needs `scale_values=False`),
and stay consistent for that column. A **signed** percent (year-over-year,
above/below target) is the diverging **RdYlGn** measure —
`heatmap(gt, "yoy_change", kind="diverging", hue="default")` — see
`yoy_change` in `house_table.py`. `positive=good` is the default
orientation; pass `reverse=True` only when positive genuinely means worse
(cost overrun, error rate, latency, churn).

**A related PAIR of columns can be ONE measure.** When a request names two
columns that are really one comparison split across two cells — a
best/worst pair, a high/low pair, a before/after pair — color BOTH columns
together via a SINGLE `heatmap(gt, [col_a, col_b], kind="diverging", ...)`
call sharing one domain, rather than either coloring only one of the pair
or spending two separate slots of the 2-measure ceiling on them. This keeps
the colored-measure COUNT at 1 for the pair (not 2), leaving the ceiling's
other slot free for a genuinely different measure elsewhere in the table.
It's easy to color only the obvious "headline" measure (e.g. overall
percent change) and never notice the pair exists as a second colorable
measure at all — actively look for one before finalizing which columns are
colored. Use a SHARED symmetric domain spanning both columns (`M =
max(abs of every value in EITHER column)`, `domain=[-M, M]`) so the two
columns render at comparable saturation for comparable magnitude,
regardless of which column happens to hold the larger value in a given row:
```python
day_m = max(df["best_day_gain"].abs().max(), df["worst_day_loss"].abs().max())
gt = heatmap(gt, ["best_day_gain", "worst_day_loss"], kind="diverging",
             hue="PuOr", domain=[-day_m, day_m])
```
(`hue="PuOr"` is passed straight through as an explicit palette name — not
one of the `PALETTE["diverging"]` keys — deliberately NOT `RdYlGn` again if
another diverging measure elsewhere in the same table already uses it: two
diverging measures in one table must use two different palette families,
same rule as two sequential measures never sharing one hue.)

**Want an explicit `+`/`−` sign on a signed value?** Pass `force_sign=True`
— do NOT hand-rewrite it with `pattern="{x:+.1f}%"`. `force_sign=True` is a
plain keyword on `fmt_number`/`fmt_percent`/`fmt_currency`/`fmt_integer`
(the formatters this skill actually uses); `fmt_scientific` is the one
exception, with separate `force_sign_m=`/`force_sign_n=` keywords instead
of a single `force_sign=`.

`pattern=`'s `{x}` is a **literal substitution token** that must appear
EXACTLY as `{x}` — it is not a Python format-spec slot, so
`great_tables` does a plain string-replace of the substring `{x}`, not an
f-string evaluation. Write `:+.1f` (or any format spec) inside the braces
and the substring no longer matches `{x}` at all, so **nothing gets
replaced and every cell renders the literal text `{x:+.1f}%`** — silently,
with no exception raised. Confirmed by direct test:
`fmt_number(columns="x", pattern="{x:+.1f}%")` renders literal
`{x:+.1f}%` in every cell. For a genuine **percent** column, fix it with
`fmt_percent`, not a `fmt_number` + manual `%` suffix (a `%`-suffixed
`fmt_number` call is cosmetically similar but semantically wrong for a
percent value — it skips `fmt_percent`'s scale handling and locale-aware
percent formatting, contradicting this section's own rule above):
`fmt_percent(columns="x", decimals=1, scale_values=False,
force_sign=True)` renders `+86.5%` / `−12.3%` correctly for already-scaled
inputs like `86.5` (`scale_values=True`, the default, is for fractional
inputs like `0.865`) — `decimals=` still needs to be passed explicitly (it
defaults to `2`, so omitting it here would render `+86.50%`, not
`+86.5%`); `pattern=` is only for wrapping the
already-formatted number in literal text (a unit suffix, parentheses,
etc.), never for a format spec.

## Ranking / rank / position

Plain integers, no decimals, no color — `fmt_integer(columns="rank")`, see
`rank` in `house_table.py`. A rank's information is its *order*, not its
magnitude: never `data_color`/`heatmap` a rank column.

## Categorical status / binary state

Never `data_color`. Use `status_chip(gt, column, meaning)` with an explicit
value → `"good"`/`"bad"`/`"neutral"` map — see `status` in
`house_table.py`. The rule made explicit: a red/green column always means
good/bad, whether it's continuous (a heatmap) or discrete (a status chip)
— color is never decorative.

## Row identifiers (name / date / ID)

Becomes the stub: `rowname_col=...`, **default ON, not optional, whenever a
column holds row identifiers** — resolve this BEFORE you organize the rest
of the columns (right after you've decided what the rows and grain of the
table are), not as a pattern-match you get to later. `tab_stubhead(label=
...)` requires the stub to already exist — see the `product` column /
`tab_stubhead("Product")` call in `house_table.py`. Skipping the stub on an
obvious identifier column is not a stylistic minimalism — it's an
incomplete table.

**A month/date-and-year stub is always formatted `"Mon YYYY"`** (Python
`strftime("%b %Y")` — e.g. `"Apr 2010"`), never `"YYYY-MM"`/`"YYYY-Mon"`/a
raw `Period`'s default string form. This is a pinned, deterministic choice
like every other value in this file — don't let `str(a_pandas_period)` or
`to_period("M")`'s default stringification leak into the stub unformatted;
always route it through an explicit `strftime`.

**A day-level date stub** (a daily time series, not a monthly aggregation)
is formatted `"Mon DD, YYYY"` (`strftime("%b %d, %Y")` — e.g. `"Jan 05,
2010"`) — always include the year even when it's constant across every row,
since a stub label should be unambiguous read in isolation.

## Natural grouping category

`groupname_col=...` + `group_emphasis(gt, hue=...)` when the prompt names
a grouping dimension, or a low-cardinality categorical is the organizing
story — see `region` / `group_emphasis` in `house_table.py`.

## Unified color theme — the band/stub/group/stripe hierarchy

Pick ONE hue for the whole table (the DA hue-selection rule: match an
existing heatmap's family first, else the data's subject, else Navy) and
run every quiet structural surface through it — but not at the same
strength. Only ONE row deserves its own distinct, highlighted treatment: a
summary/total row (see below). Column labels, the stub, and group headers
are all quieter than that, and quieter than each other:

1. **Column-label band.** The house DEFAULT is the `accent_tint` (a
   clearly-visible light tint, not a solid fill) — the MORE visible of the
   band/stub pairing, since the band spans every column and sits right
   under the title. The heatmap is still the star of the table, not the
   header. Write this call directly, with the literal hex copied from the
   "Hex reference" table above, rather than through `band(gt, hue=...)` —
   the exact color should be visible in your own script's text, not only
   resolvable by running it:
   ```python
   gt = gt.tab_options(
       column_labels_background_color="#C9E0F0",  # accent_tint.navy, from the table above
       column_labels_border_bottom_color="#CCCCCC",
       column_labels_border_bottom_width="2px",
       column_labels_border_bottom_style="solid",
   )
   ```
   (`band()` in `house_table.py` still exists and does the same thing — use
   it if you prefer, but this literal form is the one to reach for when the
   script's own text should show the exact choice made.) Reach for the dark
   variant (`accent` solid fill + white column-label text) only for a pure
   categorical/text table with no heatmap at all, where the band IS the
   color story.
2. **Stub** — `stub_tint(gt, hue=...)` — the quieter `washed` tint. A
   narrower, secondary surface next to the more prominent band, so it
   stays subtler rather than competing with it.
3. **Group headers** — `group_emphasis(gt)` — bold weight + the `#BDBDBD`
   structural rule ONLY, deliberately **no background fill**. A group
   label is a section break, not a result worth its own highlight.
4. **Row stripe** — `stripe(gt)` — always the flat neutral grey, NEVER
   tinted to the table's hue (unlike band/stub) — an alternating tinted
   fill reads as busy across many rows in a way a single flat surface
   doesn't.

Pass the SAME hue to `band()`/`stub_tint()` so the theme reads as one
thing. This hierarchy is what keeps the heatmap the star: nothing in the
structural furniture is as loud as a heatmap's own gradient (pale to deep,
varying row by row), which stays the only element on the page that
visually "moves." See `house_table.py`'s `band(gt, hue="navy")` /
`stub_tint(gt, hue="navy")` / `group_emphasis(gt)` / `stripe(gt)` calls for
the worked example.

## Summary / total rows

Add **only** when the request implies totals/aggregates; don't invent one
otherwise. For a whole-table grand total, use `great_tables`' native
`gt.grand_summary_rows(fns={"Total": ...})` + `tab_style(...,
locations=loc.grand_summary())` — see the `Total` row in `house_table.py`.
It's structurally separate from any `groupname_col` section (no fake group
label needed) and it's excluded from `data_color`'s domain automatically.
Sum only the columns that are meaningfully summable (`units_sold`/`revenue`
in the demo; `yoy_change`/`status`/`rank` are left blank via `missing_text`
because summing them is meaningless). Reach for the `summary_row(gt,
row_index, bold=True)` helper only when a total must live inline as an
ordinary data row instead (e.g. a per-group subtotal positioned among that
group's own rows) — `grand_summary_rows` always places its total(s) at the
very top or bottom of the whole table, never inline.

## Missing values

Always `sub_missing(columns=..., missing_text="—")` — never a raw blank
cell. See the injected `yoy_change` gap on `Zeta Kit` and the blank
`Total` row cells in `house_table.py`.

## The ≤2 colored-measures ceiling

Hard rule, same as the other two skills: at most 2 columns get continuous
color treatment (`data_color`/`heatmap`). A pure categorical/text table
gets no fill at all — its anchor is the heading band, switched to
`band(gt, shade="dark", hue=...)` for this no-heatmap case only (see
"Unified color theme" below). `house_table.py` uses exactly 2:
`revenue` (sequential) and `yoy_change` (diverging); `status` is a 3rd
color story but is a categorical chip, not a heatmap, so it doesn't count
against the ceiling.

## Global constants

Frame/save/title/subtitle are covered by "THE NON-NEGOTIABLE BASE" at the
top of this file — this section is just the remaining fit-and-finish
constants:

- Header alignment: title + subtitle centered (`tab_header`'s default).
- Font size: shrink only as a last resort, in this order — bigger canvas
  (`gtsave(vwidth=..., vheight=...)`) → higher zoom (`gtsave(zoom=...)`) →
  smaller font.
