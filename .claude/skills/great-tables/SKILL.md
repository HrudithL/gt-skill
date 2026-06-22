---
name: great-tables
description: Produce a polished, publication-ready table image (PNG) from a CSV or other tabular data file using the Python `great_tables` package. Invoke this skill for ANY request that asks to make, build, render, show, display, or visualize a table from data — including financial, scientific, summary, or comparison tables. Do not write `great_tables` code without loading this skill first.
---

# Great Tables Skill

Build publication-ready display tables in Python using the `great_tables` package.

## Workflow

1. **Inspect the data** — Read a sample (head + dtypes + shape) to understand columns, types, nulls, scale, and units.
2. **Plan the table** — Decide: which columns to show/hide, how to format each one, whether to use spanners, row groups, a header/subtitle, source notes, or data coloring. Consider what story the table tells.
3. **Write idiomatic code** — Produce a single Python script using method chaining. Import from `great_tables` and `pandas` (or `polars`).
4. **Run and verify** — Execute the script, confirm the PNG was produced and looks correct. If errors occur, fix and re-run.
5. **Commit** — Write the final script to `table.py` and rendered image to `table.png` in the working directory.

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
- **`tab_source_note`** — Add when data has a clear source or needs citation.

## Gotchas

- **Save method**: Use `gt.save("table.png")` — NOT `gt.gtsave()`. The `.save()` method is the correct Python API.
- **Absolute paths**: When the working directory might differ from where the script runs, use absolute paths for both input data and output PNG.
- **Column names in `fmt_*`**: Use the *original DataFrame column names*, not the labels set by `cols_label()`. Labels are display-only.
- **Row indices in `loc.body()`**: Use integer indices (0-based position in the displayed table), NOT DataFrame index values.
- **`tab_spanner` column order**: Columns under a spanner are gathered together by default (`gather=True`). If you don't want reordering, set `gather=False`.
- **`data_color` domain**: Always set `domain=` explicitly when using `data_color()` to avoid inconsistent coloring across tables. Use `na_color=` for missing values.
- **Method chaining**: Build the entire table in one chained expression. Avoid mutating the GT object in a loop (use `tab_style` with row lists instead of one call per row).
- **`fmt_percent` input scale**: Values should already be in decimal form (0.15 = 15%). If your data is already 0–100, use `scale_values=False`.
- **Imports**: Always import `style` and `loc` from `great_tables` if using `tab_style` or `data_color`. Common: `from great_tables import GT, md, html, style, loc`.
- **`cols_label` syntax**: Use keyword arguments (`cols_label(col_name="Label")`) or a dict (`cols_label(cases={"col_name": "Label"})`). The dict form is required when column names have special characters.
- **PNG rendering**: `gt.save()` requires `selenium` or the `webdriver-manager` package for PNG output. If unavailable, fall back to `gt.save("table.html")` and note the limitation.

## When to Load References

- Read [references/api.md](references/api.md) when you need exact method signatures, parameter names, or less-common methods (e.g., `opt_*`, `cols_width`, `cols_align`, `tab_stubhead`).
- Read [references/design.md](references/design.md) when you need guidance on visual design choices — color palettes, when to use data coloring, typography, or layout patterns for specific table types (financial, scientific, comparison).