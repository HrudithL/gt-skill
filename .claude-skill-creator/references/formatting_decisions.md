# Formatting decisions: how to keep tables consistent across very different data

This is the guide for the judgment calls that can't be hard-coded into a
helper function because they depend on what the data actually *means* --
column dtype alone isn't enough to know whether `0.12` is a rate that needs
`fmt_percent` or a raw measurement that needs `fmt_number`.

## Picking a formatter per column

Ask what the number represents, not just what type it is:

- **Money** (revenue, price, cost, salary, any `$`/currency-denominated
  value) -> `fmt_currency`. If the source data is a string like `"$1,200.50"`
  or `"1200,50 €"`, strip it to a plain float *before* it reaches gt --
  `fmt_currency` formats numbers, it does not parse currency strings.
- **Rates, ratios, shares of a whole** (a column that's conceptually a
  percentage) -> `fmt_percent`. Check whether the underlying value is already
  a fraction (`0.12`) or already scaled (`12`) -- `fmt_percent` expects the
  fractional form by default; a column that's already `12` meaning "12%"
  needs dividing by 100 first, or it will render as `1200%`.
- **Counts, quantities, anything that's conceptually an integer** ->
  `fmt_integer` rather than `fmt_number` with `decimals=0` -- it's clearer
  intent and handles the edge cases (like never showing `"5.0"`) correctly.
- **Plain continuous measurements** (temperatures, scores, physical
  quantities) -> `fmt_number` with a `decimals=` value that matches the
  data's actual precision -- don't default to 2 decimals out of habit; a
  score out of 10 probably wants 1, a physical constant might want more.
- **Dates and times** -> `fmt_date`/`fmt_time`/`fmt_datetime`, not
  string-formatted dates left as-is. Pick a `date_style` that matches the
  audience/locale (ISO for anything technical or international, a written-out
  style for a general audience).
- **Booleans** -> `fmt_tf` or `fmt_icon` (a check/x icon) rather than leaving
  raw `True`/`False`, which reads as code, not prose.
- **IDs, codes, free text** -> no numeric formatter; make sure `cols_align`
  leaves them left-aligned (gt's `auto_align=True` default usually gets this
  right already).

Never leave a formatter decision as "whatever the default rendering happens to
be" -- that's exactly the inconsistency this skill exists to avoid.

## Column labels

Always relabel out of raw source names -- `humanize_labels()` in
`gt_house_style.py` handles the mechanical part (title-casing, underscores to
spaces), but override it wherever the automatic version is wrong: acronyms
(`"Yoy Change"` should be `"YoY Change"`), units (`"revenue_usd"` should
probably become `"Revenue (USD)"` rather than just `"Revenue Usd"`), and
anything ambiguous without domain context.

## Row structure: stub, groups, and spanners

- Use `rowname_col=` when one column is genuinely a row identifier a reader
  would scan down (a name, a ticker, a date) -- it visually separates
  identity from data and looks intentional rather than just "another column."
- Use `groupname_col=` when rows fall into real categories the reader would
  want to think about *in* groups (regions, departments, years) -- this adds
  row-group header bars, which meaningfully aids scanning a long table.
  Don't use it for a column with too many unique values (e.g. one group per
  row) -- that defeats the purpose and just adds visual noise.
- Use `tab_spanner` when 2+ columns are sub-parts of one concept (`q1_actual`/
  `q1_target`, or `2024`/`2025` under a "Revenue" spanner) -- it makes a
  relationship visible that would otherwise only live in the column names.

## Heatmaps: when they help and which palette

A heatmap (via `add_heatmap()` / `data_color()`) earns its place when a reader
benefits from seeing *relative magnitude at a glance* across many rows --
performance metrics, changes over time, scores. It does not help, and usually
hurts, on:
- Tables with very few rows (3-4) where the numbers themselves are easy to
  scan directly.
- Columns of unique identifiers or categorical codes with no inherent order.
- A column that's already the visual focus via bold text or a spanner --
  stacking emphasis techniques dilutes all of them.

Palette choice:
- **Sequential** (`Blues`, `Greens`, etc.) for magnitude-only data with no
  natural midpoint -- more is just more (revenue, population, counts).
- **Diverging** (`RdBu`, `PRGn`, etc.) for data where the *sign* or
  *direction relative to a reference point* is the meaningful thing --
  % change, actual-vs-target deviation, profit vs. loss. `add_heatmap(kind=
  "auto")` picks this automatically by checking whether the targeted columns
  actually contain both negative and positive values -- but that check is
  centered on zero, so it misses metrics that diverge around a *nonzero*
  reference. Quota attainment stored as a fraction (0.76, 1.04, 1.22 -- all
  positive, but meaningfully "below/above 100%") is the classic case: pass
  `kind="diverging", center=1.0` explicitly rather than relying on auto-detect.
- Always set an explicit `domain=` (which `add_heatmap()` does automatically
  from the real data) rather than relying on gt's per-call auto-range,
  especially when a single outlier would otherwise compress every other
  value's color into a narrow, hard-to-distinguish band.

## Missing and messy data

- Decide, and state, what a missing value means before formatting around it.
  "No data collected" and "true zero" and "not applicable" are different
  claims -- don't let them all silently collapse into a blank cell.
- `sub_missing(missing_text="—")` for a clean placeholder is almost always
  better than leaving `None`/`NaN` to render as an empty box.
- Common CSV/Excel import pitfalls to check for before formatting:
  - Numbers imported as strings because of thousands separators, currency
    symbols, or a stray unit suffix (`"12%"`, `"$1,200"`, `"5 kg"`).
  - A header row that isn't row 0 (title rows, merged cells, or a blank row
    above the real header).
  - Mixed types in one column (numbers and text like `"N/A"` in the same
    column) -- coerce deliberately (`pd.to_numeric(..., errors="coerce")`)
    rather than letting the column stay `object` dtype, which breaks
    `fmt_number`/`data_color`.
  - Trailing/leading whitespace in string columns that breaks exact matching
    for group labels or joins.
- For SQL results: watch for `Decimal` types (cast to `float` for gt's
  formatters) and confirm NULL handling matches the missing-value convention
  chosen above.