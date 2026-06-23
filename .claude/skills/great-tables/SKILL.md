---
name: great-tables
description: Use when building any `great_tables` table from a data file — provides API reference, design patterns, and the render-to-PNG workflow. Load before writing code so the script follows the documented patterns and saves the PNG correctly.
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

## Understanding the Data

How to read, interpret, and evaluate data before building a table. **Do this before writing any GT code.**

### Step 1: Structural Inspection

Before thinking about presentation, understand what you have:

```python
df = pd.read_csv("data.csv")
print(df.shape)          # How many rows and columns?
print(df.dtypes)         # What types are the columns?
print(df.head(10))       # What do the first rows look like?
print(df.describe())     # What are the distributions?
print(df.isnull().sum()) # Where is data missing?
```

Answer these questions:
- **What is a row?** Each row should represent one "thing" — a year, a person, a product, a measurement. If you can't describe what a row is, the data may need reshaping.
- **What is the grain?** Is this daily, monthly, yearly, per-person, per-transaction? The grain determines how to aggregate and what row labels to use.
- **What are the key identifiers?** Which columns uniquely identify a row? These are candidates for `rowname_col`.
- **What are the measures?** Which columns contain the numbers/values you'd present? These are the display columns.
- **What are the categories?** Which columns partition the data into groups? These are candidates for `groupname_col` or filters.

### Step 2: Understand What the Data Means

Column names are hints, not answers. Go deeper:

**Identify Units and Scale**
- A column called `revenue` — is it in dollars, thousands, or millions? Check the magnitude of values.
- A column called `rate` — is it 0.05 (decimal, needs `scale_values=True`) or 5.0 (percentage, needs `scale_values=False`)?
- A column called `volume` — volume of what? Trading shares? Liters? The context of the dataset determines the unit.

**Identify Relationships**
- Which columns move together? (e.g., `open`/`close`/`high`/`low` are all prices — group them under a spanner)
- Which columns are derived from others? (e.g., `return %` is computed from `open` and `close` — it's a summary metric, often the most important column)
- Are there natural comparisons? (e.g., `budget` vs `actual`, `this_year` vs `last_year`)

**Identify What Makes the Data Valuable**
Ask: **why would someone look at this table?** The answer drives every design decision:
- **To compare** → emphasize the comparison columns, use consistent formatting, consider `data_color`
- **To find extremes** → highlight min/max values with bold or color
- **To see trends** → order chronologically, use `data_color` to show direction
- **To look up a value** → make row labels clear, keep the table scannable
- **To get a summary** → aggregate the raw data, show totals/averages, keep it short

### Step 3: Assess Data Quality

Before presenting data, check for issues that affect table quality:

- **Outliers**: Are there extreme values that will distort `data_color` domains? Compute the range.
- **Missing data**: Use `sub_missing(missing_text="—")` for NaN/None. Don't let blank cells confuse the reader.
- **Precision**: How many decimal places are meaningful? Match precision to context — financial values often need 2 decimals, scientific measurements should match instrument precision, percentages usually 1–2 decimals.
- **Consistency**: Are all monetary values in the same currency? All dates in the same timezone? All percentages on the same scale?

### Step 4: Match Data to the User's Request

This is the critical validation step:

1. **Read the user's request carefully.** What specifically are they asking to see?
2. **Check if the data contains what they need.** If they ask for a view the data cannot support (e.g., quarterly breakdown when only annual totals exist), the data cannot fulfill the request.
3. **If there's a mismatch**: Stop. Tell the user what you found in the data and why it doesn't match their request. Do not force a table that doesn't answer the question.
4. **If the data is close but not exact**: Explain what you can show instead and proceed only if it's genuinely useful.

### Step 5: Plan the Presentation

Now that you understand the data, decide:

**What to Show**
- **Not every column deserves to be in the table.** Internal IDs, raw timestamps, and intermediate calculations should be hidden.
- **Not every row deserves to be in the table.** If there are 1000 rows, show the top 10, the most recent 5 years, or a meaningful aggregate.
- **Derived columns may be more valuable than raw ones.** A "Return %" column tells more story than separate open/close prices.

**How to Aggregate**
- If the raw data is too granular for the requested view, aggregate it: daily → monthly, transactions → totals, individual → category averages.
- Choose aggregation functions that match the data meaning: `sum` for counts and revenues, `mean` for rates and scores, `max`/`min` for extremes.

**What Story to Tell**
- **The title should state the takeaway**, not just describe the data. A title that names the insight is better than one that just names the dataset.
- **The subtitle provides context**: date range, data source, methodology.
- **Column order should follow the reader's eye**: identifiers → key metrics → supporting detail.
- **The most important column** should get visual emphasis: bold headers, `data_color`, or prominent positioning.

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
- **PNG rendering**: Always save with `gt.save("table.png")`. Do not save HTML, hand-roll a PIL/imgkit/wkhtmltoimage renderer, or otherwise substitute another output format — those produce a fake table, not the `great_tables` rendering. If `gt.save()` fails (missing chromedriver, sandboxed environment), surface the error so the environment can be fixed; do not silently fall back to a different format.

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

---

# Design Guide

Visual design principles and patterns for building polished, publication-ready tables.

## Core Design Principles

1. **Tables tell stories** — Every table should have a clear narrative. The title states the takeaway, the subtitle provides context, and the structure guides the reader's eye to what matters.
2. **Less is more** — Hide internal columns, remove visual clutter, use whitespace. A table with 5 well-formatted columns beats one with 15 raw columns.
3. **Format for meaning** — Formatting communicates data type instantly. Currency symbols say "money," percentage signs say "rate." Never show raw floats when a semantic formatter exists.
4. **Group for comprehension** — Spanners and row groups create visual hierarchy. Use them when columns or rows share a logical parent category.
5. **Color with purpose** — Data coloring should encode information (performance, rank, status), not decorate. Every colored cell should answer a question.

## Table Anatomy: When to Use Each Structural Element

| Element | Use when... | Skip when... |
|---|---|---|
| `tab_header` (title) | Always. Every table needs a title. | Never skip this. |
| `tab_header` (subtitle) | There's a date range, data source, or clarifying context | The title is self-explanatory |
| `rowname_col` | A column has unique identifiers (names, dates, IDs) | All columns are value columns |
| `groupname_col` | A column has 2–8 categories that meaningfully partition rows | Too many groups (>8) or only 1 group |
| `tab_spanner` | 3+ columns share a logical parent (e.g., "Q1", "Performance") | Only 1–2 related columns |
| `tab_source_note` | Data has a citable source or needs methodology notes | Data is self-evident or internal |
| `cols_hide` | Columns were used for grouping, or are IDs/internals | Every column has display value |
| `data_color` | Values encode a natural gradient (good→bad, low→high) | Data is categorical or has no natural order |

### Column Count Guidelines

- **Ideal**: 4–8 columns visible in the final table
- **Maximum**: 10–12 columns before the table becomes hard to scan
- **If more**: Consider splitting into multiple tables, hiding less important columns, or using spanners to create visual groups

## Color Palette Selection

### For Sequential Data (low → high)

Use single-hue palettes for magnitude:
- `"Blues"` — neutral, professional
- `"Greens"` — positive connotation (growth, success rates)
- `"Reds"` or `"Oranges"` — attention/warning (error rates, risk)
- `"Greys"` — subtle background emphasis

### For Diverging Data (negative ↔ positive)

Use two-hue palettes centered on a neutral midpoint:
- `"RdYlGn"` — red=bad, green=good
- `"RdBu"` — red vs blue (anomalies, sentiment)
- `"PuOr"` — purple vs orange (balanced, colorblind-safe)

**Critical: domain range must cover your actual data.** Set `domain=` to span the full range of values in your data (or a symmetric range around zero for diverging palettes). If your data ranges from -30% to +40%, use `domain=[-40, 40]` — not `domain=[-20, 30]` which clips extreme values to the same color as boundary values, making them invisible.

**Always set `truncate=False`** (the default) so out-of-range values still get the most extreme color in the palette rather than disappearing. Values outside the domain should be **more** visually prominent, not less.

**Prefer symmetric domains** for diverging data (e.g., `[-30, 30]` not `[-20, 30]`) so the neutral midpoint aligns with zero.

### For Categorical Data

Use qualitative palettes (no implied order):
- `"Set2"` — muted, colorblind-friendly
- `"Dark2"` — bold, high contrast
- `"Paired"` — for paired categories

### Manual Conditional Styling

For binary good/bad indicators, use explicit colors with `tab_style`:
```python
positive_rows = df[df["value"] >= 0].index.tolist()
negative_rows = df[df["value"] < 0].index.tolist()

gt = (
    gt
    .tab_style(
        style=style.fill(color="#c6efce"),
        locations=loc.body(columns="value", rows=positive_rows)
    )
    .tab_style(
        style=style.fill(color="#ffc7ce"),
        locations=loc.body(columns="value", rows=negative_rows)
    )
)
```

**Never** loop row-by-row calling `tab_style` once per row. Collect row indices into lists first.

## Typography & Spacing

### Bold and Color Text Emphasis

Use **bold text** and **colored text** deliberately to draw the reader's eye to what matters most. This is one of the most powerful tools for making a table scannable — but overuse destroys its impact.

**When to use bold text (`style.text(weight="bold")`):**
- Total/summary rows — the final "Total" or "Average" row should stand out
- Key metrics — if the table's story centers on one number, bold it
- Column headers or labels that need extra emphasis

**When to use colored text (`style.text(color=...)`):**
- Positive/negative indicators — green for gains, red for losses (pair with bold for critical values)
- Threshold alerts — values above or below a meaningful threshold
- Category identification — when color maps to a category and reinforces a grouping

**When NOT to use:**
- Don't bold every cell — if everything is bold, nothing is bold
- Don't color text randomly — every colored cell should answer "why is this highlighted?"
- Don't combine bold + color + fill on the same cell unless it's a critical outlier
- Don't use more than 2-3 text colors in a single table

**Example — highlight extreme values:**
```python
gt = (
    gt
    .tab_style(
        style=style.text(weight="bold", color="#d32f2f"),
        locations=loc.body(columns="value", rows=large_negative_rows)
    )
    .tab_style(
        style=style.text(weight="bold", color="#2e7d32"),
        locations=loc.body(columns="value", rows=large_positive_rows)
    )
)
```

### Font Choices

- Default system fonts work well for most tables
- Use `system_fonts("humanist")` for a warmer, readable feel
- Use `system_fonts("neo-grotesque")` for a clean, modern look
- Set via `opt_table_font()` or `tab_options(table_font_names=...)`

### Sizing

- `table_font_size="14px"` — good default for readability
- `heading_title_font_size="18px"` — title should be noticeably larger
- `source_notes_font_size="11px"` — de-emphasize footnotes

### Padding

- Use `opt_horizontal_padding(scale=2)` for tables with few columns (adds breathing room)
- Use `opt_vertical_padding(scale=0.8)` for dense data tables with many rows
- Default padding works for most 5–15 row tables

## Pre-built Themes

`opt_stylize(style=N, color=C)` provides quick professional looks:

- **Style 1**: Colored heading background, clean body
- **Style 2**: Colored column labels, striped rows
- **Style 3**: Heavy borders, bold structure
- **Style 4**: Minimal, thin lines
- **Style 5**: Colored row groups
- **Style 6**: Full color with all elements styled

Colors: `"blue"`, `"cyan"`, `"pink"`, `"green"`, `"red"`, `"gray"`

Use these as starting points, then override specific elements with `tab_style` or `tab_options`.

## Common Anti-patterns

| Don't | Do instead |
|---|---|
| Show raw float columns without formatting | Apply `fmt_number` with appropriate decimals |
| Display all 20+ columns from the source data | Select 5–8 most relevant, hide the rest |
| Use default column names like `avg_rev_q1_ytd` | Relabel with `cols_label` to human-readable text |
| Apply data_color without a domain | Set `domain=[min, max]` for consistency |
| Create a table without a title | Always use `tab_header(title=...)` |
| Use red/green for the only visual distinction | Ensure colorblind accessibility; use patterns or bold text alongside color |
| Put source info in the title/subtitle | Use `tab_source_note` for citations |
| Show >20 rows without grouping | Use `groupname_col` or limit to top-N with a note |

