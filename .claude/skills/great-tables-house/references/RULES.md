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
   still a gap, not a neutral default.
3. **The boxed frame, always** — `frame(gt)`.
4. **At most 2 colored measures, TOTAL, no exceptions** — `data_color`/
   `heatmap()` calls across the WHOLE table, not per column-group and not
   "one per numeric column." A table with 5 numeric columns still gets
   **at most 2** heatmaps — pick the 1–2 that are actually the point of the
   request and leave the rest uncolored (bold text at most). Three or more
   `heatmap(...)` calls in one script is always a bug, never a stylistic
   choice — if you catch yourself writing a third one, delete it.
5. **`finalize(gt, path="table.png")`** — the mandatory render, always last.

Everything else in this file — a stub, a group, a spanner, a status chip,
a summary row, the striping/tint hierarchy — is genuinely conditional on
what the data and request actually call for, and stays that way. The five
items above are different in kind: they are the base every table stands
on, never something to selectively adopt. If you imported a helper
(`stripe`, `stub_tint`, `humanize_labels`, ...) and then don't end up
calling it, that's a sign you copied more of `house_table.py` than your
table needs — remove the unused import, but never let "I didn't get to
it" cost you an item on this list.

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

Becomes the stub: `rowname_col=...`, default ON whenever a column holds
row identifiers. `tab_stubhead(label=...)` requires the stub to already
exist — see the `product` column / `tab_stubhead("Product")` call in
`house_table.py`.

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

1. **Column-label band** — `band(gt, hue=...)` — the house DEFAULT is the
   `accent_tint` (a clearly-visible light tint, not a solid fill) — the
   MORE visible of the band/stub pairing, since the band spans every
   column and sits right under the title. The heatmap is still the star
   of the table, not the header; reach for `shade="dark"` (a solid
   `accent` fill + white text) only for a pure categorical/text table with
   no heatmap at all, where the band IS the color story.
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
