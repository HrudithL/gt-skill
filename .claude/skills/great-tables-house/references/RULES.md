# RULES — per-data-type formatting rules

No flowchart here. Find the row below that matches your column's kind, then
open `scripts/house_table.py` and find the function/section it names — copy
and adapt that, not this file's prose.

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
gets no fill at all — its anchor is the heading band
(`band(gt, shade="dark", hue=...)`). `house_table.py` uses exactly 2:
`revenue` (sequential) and `yoy_change` (diverging); `status` is a 3rd
color story but is a categorical chip, not a heatmap, so it doesn't count
against the ceiling.

## Global constants

- Frame: `frame(gt)` — `#CCCCCC`, 1px, all four sides.
- Save: `finalize(gt, path=...)` — `expand=15`, `zoom=2.0`.
- Title + subtitle: always present, centered (`tab_header`, see
  `house_table.py`'s `tab_header` call).
- Font size: shrink only as a last resort, in this order — bigger canvas
  (`gtsave(vwidth=..., vheight=...)`) → higher zoom (`gtsave(zoom=...)`) →
  smaller font.
