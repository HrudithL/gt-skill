---
name: great-tables
description: Produce a polished, publication-ready table image (PNG) from a CSV or other tabular data file using the Python `great_tables` package. Invoke this skill for ANY request that asks to make, build, render, show, display, or visualize a table from data — including financial, scientific, summary, or comparison tables. Do not write `great_tables` code without loading this skill first.
---

# Great Tables Skill

Build publication-ready display tables in Python using the `great_tables` package.

## Workflow

1. **Validate the request** — Before doing anything, check whether the provided data can fulfill the user's request. If the dataset does not contain relevant columns or rows for what the user is asking, **stop and tell the user** that the request cannot be fulfilled with the given data. Explain what is missing. Write a minimal `table.py` that produces a blank/empty table and save a blank `table.png`. Do not fabricate data or force an irrelevant table.
2. **Understand the data** — Go beyond column names. Examine distributions, ranges, units, and relationships. Understand what makes the data valuable and what story it can tell before deciding how to present it.
3. **Inspect the data** — Read a sample (head + dtypes + shape) to understand columns, types, nulls, scale, and units.
4. **Plan the table** — Decide: which columns to show/hide, how to format each one, whether to use spanners, row groups, a header/subtitle, source notes, or data coloring. Consider what story the table tells.
5. **Write idiomatic code** — Produce a single Python script using method chaining. Import from `great_tables` and `pandas` (or `polars`).
6. **Run and verify** — Execute the script, confirm the PNG was produced and looks correct. If errors occur, fix and re-run.
7. **Commit** — Write the final script to `table.py` and rendered image to `table.png` in the working directory.

## Core Pattern

```python
import pandas as pd
from great_tables import GT, md, html, style, loc

df = pd.read_csv("data.csv")

gt = (
    GT(df, rowname_col="id_col", groupname_col="category_col")
    .tab_header(
        title="Clear Descriptive Title",
        subtitle="Context or date range"
    )
    .cols_label(col_name="Human Label", another_col="Another Label")
    .cols_hide(columns=["internal_id", "raw_field"])
    .fmt_currency(columns="revenue", currency="USD")
    .fmt_number(columns="quantity", decimals=0, use_seps=True)
    .fmt_percent(columns="growth_rate", decimals=1)
    .fmt_date(columns="date", date_style="year.month.day.2")
    .tab_spanner(label="Financial", columns=["revenue", "cost", "profit"])
    .tab_source_note(source_note="Source: Company quarterly reports")
    .tab_options(table_font_size="14px")
)

gt.save("table.png")
```

## Formatting Rules

Match `fmt_*` to data semantics, not just numeric type:

| Data meaning | Method | Key args |
|---|---|---|
| Money/prices | `fmt_currency` | `currency="USD"`, `accounting=True` for finance |
| Counts/integers | `fmt_integer` | `use_seps=True` |
| Decimals/measurements | `fmt_number` | `decimals=` (match precision to context) |
| Percentages/rates | `fmt_percent` | `decimals=1` |
| Dates | `fmt_date` | `date_style=` |
| Datetimes | `fmt_datetime` | `date_style=`, `time_style=` |
| Times | `fmt_time` | `time_style=` |
| Large byte values | `fmt_bytes` | |
| Scientific data | `fmt_scientific` | |
| True/False | `fmt_tf` | |
| Markdown content | `fmt_markdown` | |

## Table Length

Keep tables **concise by default**. A long table is not a better table — it is harder to read and dilutes the story.

- **Target 5–15 rows** for most tables. This is enough to show trends, comparisons, and key data points.
- **Never show every row** from a large dataset unless the user explicitly asks for it. Aggregate, filter to top-N, or sample instead.
- When the data has many rows, choose the most meaningful subset: most recent years, top performers, notable outliers, or a representative sample.
- If you must show more than 20 rows, use `groupname_col` to create visual sections, and consider whether the user's request truly requires all that data.
- **Ask yourself**: "Does every row in this table earn its place?" If a row doesn't add new information or context, cut it.

## Table Structure Decisions

- **`rowname_col`** — Use when a column has unique row identifiers (names, IDs, dates). Creates a stub with a vertical divider.
- **`groupname_col`** — Use when a column has categorical values that naturally group rows (region, category, year).
- **`tab_spanner`** — Use to group related columns under a shared label (e.g., "Performance" over hp/torque/mpg columns).
- **`cols_hide`** — Remove columns used only for grouping or internal IDs from the display.
- **`cols_label`** — Always relabel programmatic column names (e.g., `avg_revenue` → `"Avg. Revenue"`).
- **`tab_stubhead`** — When using `rowname_col`, add a stub heading with `tab_stubhead(label="Year")` to label the row name column. Skip only when the row names are self-evident (e.g., sequential numbers).
- **`tab_source_note`** — Add when data has a clear source or needs citation.

## Units in Column Labels

Include units in column labels when the unit is **not already conveyed by formatting**. This is a judgment call:

- **Skip units when `fmt_*` already shows them**: Currency columns formatted with `fmt_currency` already display `$`, so the label should be `"Revenue"` not `"Revenue ($)"`. Same for `fmt_percent` (already shows `%`).
- **Include units when formatting does not show them**: A column of distances formatted with `fmt_number` should be labeled `"Distance (km)"` not just `"Distance"`. A speed column should be `"Speed (m/s)"`.
- **Include units for scientific/measurement data**: Always include units for physical quantities — `"Temperature (°C)"`, `"Pressure (atm)"`, `"Weight (kg)"`.
- **Use the `{{unit}}` notation** in `cols_label` for proper unit rendering: `cols_label(speed="Speed ({{m/s}})")`.
- **Be consistent**: If one column in a group shows units, all columns in that group should show units.

## Gotchas

- **Save method**: Use `gt.save("table.png")` — NOT `gt.gtsave()`. The `.save()` method is the correct Python API.
- **Absolute paths**: When the working directory might differ from where the script runs, use absolute paths for both input data and output PNG.
- **Column names in `fmt_*`**: Use the *original DataFrame column names*, not the labels set by `cols_label()`. Labels are display-only.
- **Row indices in `loc.body()`**: Use integer indices (0-based position in the displayed table), NOT DataFrame index values.
- **`tab_spanner` column order**: Columns under a spanner are gathered together by default (`gather=True`). If you don't want reordering, set `gather=False`.
- **`data_color` domain**: Always set `domain=` explicitly when using `data_color()`. The domain must cover the **full range of your actual data** — compute `min()` and `max()` of the column first. For diverging palettes (e.g., `"RdYlGn"`), use a **symmetric domain** centered on zero (e.g., `domain=[-40, 40]`). A too-narrow domain makes extreme values invisible; a too-wide domain compresses the color gradient. Use `na_color=` for missing values.
- **Method chaining**: Build the entire table in one chained expression. Avoid mutating the GT object in a loop (use `tab_style` with row lists instead of one call per row).
- **`fmt_percent` input scale**: Values should already be in decimal form (0.15 = 15%). If your data is already 0–100, use `scale_values=False`.
- **Imports**: Always import `style` and `loc` from `great_tables` if using `tab_style` or `data_color`. Common: `from great_tables import GT, md, html, style, loc`.
- **`cols_label` syntax**: Use keyword arguments (`cols_label(col_name="Label")`) or a dict (`cols_label(cases={"col_name": "Label"})`). The dict form is required when column names have special characters.
- **PNG rendering**: `gt.save()` requires `selenium` or the `webdriver-manager` package for PNG output. If unavailable, fall back to `gt.save("table.html")` and note the limitation.

---

# API Reference

Detailed method signatures and parameters for the `great_tables` Python package.

## GT Constructor

```python
GT(
    data,                    # DataFrame (pandas or polars)
    rowname_col=None,        # str — column to use as row labels (stub)
    groupname_col=None,      # str — column to use for row groups
    auto_align=True,         # bool — auto-align columns by type
    id=None,                 # str — custom table ID
    locale=None,             # str — default locale for all fmt_* methods (e.g., "en", "fr")
)
```

Setting `locale` at the GT level avoids repeating it in every `fmt_*` call.

## Header & Footer

### tab_header

```python
.tab_header(
    title,                   # str | md() | html()
    subtitle=None,           # str | md() | html()
    preheader=None,          # str | list[str] — rendered above the table
)
```

Use `md("**bold** text")` or `html("<em>styled</em>")` for rich formatting.

### tab_source_note

```python
.tab_source_note(source_note)   # str | md() | html()
```

Call multiple times to add multiple source notes (they appear in order).

### tab_stubhead

```python
.tab_stubhead(label)   # str | md() | html() — label for the stub column header
```

## Column Operations

### cols_label

```python
.cols_label(
    cases=None,              # dict[str, str | md() | html()] — for special char column names
    **kwargs,                # col_name="Label" pairs
)
```

Unit notation: `"Speed ({{m/s}})"` renders as "Speed (m/s)" with proper formatting.

### cols_hide

```python
.cols_hide(columns)          # str | list[str]
```

### cols_move / cols_move_to_start / cols_move_to_end

```python
.cols_move(columns, after)           # move columns after a specified column
.cols_move_to_start(columns)         # move to leftmost position
.cols_move_to_end(columns)           # move to rightmost position
```

### cols_width

```python
.cols_width(
    cases=None,              # dict[str, str] — e.g., {"col": "200px"}
    **kwargs,                # col_name="150px" or col_name="30%"
)
```

### cols_align

```python
.cols_align(
    align,                   # "left" | "center" | "right"
    columns=None,            # str | list[str] — defaults to all
)
```

## Formatting Methods

All `fmt_*` methods share common parameters:
- `columns` — target columns (str or list)
- `rows` — target rows (int or list of int indices, 0-based)

### fmt_number

```python
.fmt_number(
    columns=None,
    rows=None,
    decimals=2,              # exact decimal places
    n_sigfig=None,           # significant figures (overrides decimals)
    drop_trailing_zeros=False,
    use_seps=True,           # thousands separator
    accounting=False,        # parentheses for negatives
    scale_by=1,              # multiply values before formatting
    compact=False,           # 1230 → "1.23K"
    pattern="{x}",           # decoration pattern
    sep_mark=",",
    dec_mark=".",
    force_sign=False,
    locale=None,
)
```

### fmt_integer

```python
.fmt_integer(
    columns=None,
    rows=None,
    use_seps=True,
    accounting=False,
    scale_by=1,
    compact=False,
    pattern="{x}",
    sep_mark=",",
    force_sign=False,
    locale=None,
)
```

### fmt_currency

```python
.fmt_currency(
    columns=None,
    rows=None,
    currency=None,           # "USD", "EUR", "GBP", etc. (3-letter ISO code)
    use_subunits=True,       # show cents/pence
    decimals=None,           # override default decimal places
    use_seps=True,
    accounting=False,        # parentheses for negatives
    scale_by=1,
    compact=False,           # $1.23M
    pattern="{x}",
    sep_mark=",",
    dec_mark=".",
    force_sign=False,
    placement="left",        # "left" ($450) or "right" (450$)
    incl_space=False,        # space between symbol and value
    locale=None,
)
```

### fmt_percent

```python
.fmt_percent(
    columns=None,
    rows=None,
    decimals=2,
    drop_trailing_zeros=False,
    use_seps=True,
    accounting=False,
    scale_values=True,       # True: 0.15 → "15.00%"; False: 15 → "15.00%"
    pattern="{x}",
    sep_mark=",",
    dec_mark=".",
    force_sign=False,
    locale=None,
)
```

**Important**: `scale_values=True` (default) multiplies by 100. If data is already in 0–100 range, set `scale_values=False`.

### fmt_date

```python
.fmt_date(
    columns=None,
    rows=None,
    date_style="iso",        # see date styles below
    locale=None,
)
```

Date styles: `"iso"` (2020-01-15), `"wday_month_day_year"` (Wednesday, January 15, 2020), `"year.month.day.2"` (2020/01/15), `"day_month_year"` (15 January 2020), `"m_day_year"` (Jan 15, 2020), and more.

### fmt_time

```python
.fmt_time(
    columns=None,
    rows=None,
    time_style="iso",        # "iso", "h_m_s_p" (HH:MM:SS AM/PM), "h_m_p", etc.
    locale=None,
)
```

### fmt_datetime

```python
.fmt_datetime(
    columns=None,
    rows=None,
    date_style="iso",
    time_style="iso",
    sep=" ",                 # separator between date and time
    locale=None,
)
```

### fmt_scientific

```python
.fmt_scientific(
    columns=None,
    rows=None,
    decimals=2,
    drop_trailing_zeros=False,
    scale_by=1,
    exp_style="x10n",        # "x10n", "e", "E"
    pattern="{x}",
    sep_mark=",",
    dec_mark=".",
    force_sign_m=False,
    force_sign_n=False,
    locale=None,
)
```

### fmt_bytes

```python
.fmt_bytes(
    columns=None,
    rows=None,
    standard="decimal",      # "decimal" (KB=1000) or "binary" (KiB=1024)
    decimals=1,
    drop_trailing_zeros=True,
    use_seps=True,
    pattern="{x}",
    sep_mark=",",
    dec_mark=".",
    force_sign=False,
    locale=None,
)
```

### fmt_roman

```python
.fmt_roman(columns=None, rows=None, case="upper")  # "upper" or "lower"
```

### fmt_tf

```python
.fmt_tf(columns=None, rows=None)  # formats True/False values
```

### fmt_markdown

```python
.fmt_markdown(columns=None, rows=None)  # renders Markdown in cells
```

### fmt_image

```python
.fmt_image(
    columns=None,
    rows=None,
    height=None,             # "30px"
    width=None,              # "30px"
    path=None,               # base directory for relative paths
)
```

### fmt_nanoplot

```python
.fmt_nanoplot(
    columns=None,
    rows=None,
    plot_type="line",        # "line" or "bar"
    plot_height="2em",
)
```

Embed sparkline-style plots in cells from list/array data.

### fmt (custom formatter)

```python
.fmt(
    fns,                     # callable that takes cell value, returns str
    columns=None,
    rows=None,
)
```

## Substitution Methods

### sub_missing

```python
.sub_missing(
    columns=None,
    rows=None,
    missing_text="—",        # what to show for None/NaN
)
```

### sub_zero

```python
.sub_zero(columns=None, rows=None, zero_text="—")
```

### sub_small_vals / sub_large_vals

```python
.sub_small_vals(columns=None, rows=None, threshold=0.01, small_pattern="< {x}")
.sub_large_vals(columns=None, rows=None, threshold=1e12, large_pattern="> {x}")
```

## Styling

### tab_style

```python
.tab_style(
    style,                   # CellStyle | list[CellStyle]
    locations,               # Loc | list[Loc]
)
```

**Style classes** (combine in a list for multiple):
```python
style.text(color=None, size=None, weight=None, style=None, decorate=None, transform=None, whitespace=None)
style.fill(color=None)
style.borders(sides, color="#000000", style="solid", weight="1px")
```

**Location classes**:
```python
loc.body(columns=None, rows=None)          # body cells
loc.header()                                # title & subtitle
loc.column_labels(columns=None)            # column label cells
loc.row_groups(rows=None)                  # row group labels
loc.stub(rows=None)                        # stub (row labels)
loc.source_notes()                         # footer source notes
```

### data_color

```python
.data_color(
    columns=None,
    rows=None,
    palette=None,            # list of colors OR named palette string
    domain=None,             # [min, max] for numeric; list of categories for factor
    na_color=None,           # color for missing values (default: "#808080")
    alpha=None,              # 0-1 transparency
    reverse=False,           # reverse palette direction
    autocolor_text=True,     # auto-contrast text color
    truncate=False,          # clip out-of-domain values to boundary colors
)
```

**Named palettes**: All ColorBrewer palettes (`"Blues"`, `"Reds"`, `"RdYlGn"`, `"Spectral"`, `"Set2"`, etc.) and viridis family (`"viridis"`, `"plasma"`, `"inferno"`, `"magma"`, `"cividis"`).

## Spanners & Row Groups

### tab_spanner

```python
.tab_spanner(
    label,                   # str | md() | html()
    columns=None,            # list of column names to span
    spanners=None,           # existing spanner IDs to span over
    level=None,              # explicit level (0 = closest to column labels)
    id=None,                 # ID for referencing this spanner later
    gather=True,             # reorder columns to be contiguous under spanner
    replace=False,           # allow replacing existing spanners
)
```

Multiple levels: call `tab_spanner` multiple times. Spanners stack automatically from bottom to top.

### tab_row_group (via constructor)

Row groups are set via `groupname_col=` in the GT constructor. The order of groups matches their first appearance in the data.

## Table Options

### tab_options (key parameters)

```python
.tab_options(
    # Container
    container_width=None,             # "100%" or pixel value
    # Table
    table_width=None,                 # "auto", pixel, or percentage
    table_font_size=None,             # "14px", "small", etc.
    table_font_names=None,            # ["Arial", "sans-serif"]
    table_background_color=None,
    # Heading
    heading_background_color=None,
    heading_align=None,               # "center", "left", "right"
    heading_title_font_size=None,
    heading_subtitle_font_size=None,
    # Column labels
    column_labels_background_color=None,
    column_labels_font_weight=None,   # "bold", "normal", or numeric
    column_labels_text_transform=None,  # "uppercase", "lowercase"
    column_labels_border_bottom_color=None,
    # Row groups
    row_group_background_color=None,
    row_group_font_weight=None,
    # Body
    table_body_hlines_style=None,     # "solid", "dotted", "none"
    table_body_hlines_color=None,
    table_body_hlines_width=None,
    # Data rows
    data_row_padding=None,            # "8px"
    data_row_padding_horizontal=None,
    # Source notes
    source_notes_font_size=None,
    # Row striping
    row_striping_background_color=None,
)
```

### opt_ helpers

```python
.opt_stylize(style=1, color="blue")          # pre-built theme (styles 1-6, colors: blue/cyan/pink/green/red/gray)
.opt_row_striping()                           # alternate row colors
.opt_horizontal_padding(scale=1)             # multiply horizontal padding
.opt_vertical_padding(scale=1)               # multiply vertical padding
.opt_table_font(font=None, weight=None, size=None)
.opt_all_caps()                              # uppercase column labels
.opt_align_table_header(align="center")
```

## Saving

```python
.save(
    filename,                # str — path ending in .png, .html, .pdf, or .tex
    selector="table",        # CSS selector to capture
    scale=2,                 # pixel density multiplier for PNG
    expand=10,               # padding around table in pixels
    web_driver="chrome",     # or "firefox"
)
```

For PNG: requires Chrome/Chromium + chromedriver (or Firefox + geckodriver). If not available, save as `.html` instead.

## Helpers

```python
from great_tables import md, html, define_units, system_fonts

md("**bold** and *italic*")      # Markdown in headers, labels, cells
html("<span style='...'>X</span>")  # Raw HTML
define_units("m^2 s^-1")         # Unit notation for labels
system_fonts("humanist")         # Font stacks: "humanist", "old-style", "transitional", "geometric-humanist", "classical-humanist", "neo-grotesque", "monospace-slab-serif", "monospace-code", "industrial", "rounded-sans", "slab-serif", "system-ui"
```

## When to Load References

- Read [references/data.md](references/data.md) **before building any table** to guide your data understanding process — how to interpret distributions, identify key metrics, and decide what story the data tells.
- Read [references/design.md](references/design.md) when you need guidance on visual design choices — color palettes, when to use data coloring, typography, or layout patterns for specific table types (financial, scientific, comparison).
