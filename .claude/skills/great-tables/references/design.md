# Great Tables Design Guide

Visual design principles and patterns for building polished, publication-ready tables.

## Core Principles

1. **Tables tell stories** — Every table should have a clear narrative. The title states the takeaway, the subtitle provides context, and the structure guides the reader's eye to what matters.
2. **Less is more** — Hide internal columns, remove visual clutter, use whitespace. A table with 5 well-formatted columns beats one with 15 raw columns.
3. **Format for meaning** — Formatting communicates data type instantly. Currency symbols say "money," percentage signs say "rate." Never show raw floats when a semantic formatter exists.
4. **Group for comprehension** — Spanners and row groups create visual hierarchy. Use them when columns or rows share a logical parent category.
5. **Color with purpose** — Data coloring should encode information (performance, rank, status), not decorate. Every colored cell should answer a question.

## Table Anatomy Decisions

### When to Use Each Structural Element

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
- `"Blues"` — neutral, professional (revenue, population)
- `"Greens"` — positive connotation (growth, success rates)
- `"Reds"` or `"Oranges"` — attention/warning (error rates, risk)
- `"Greys"` — subtle background emphasis

### For Diverging Data (negative ↔ positive)

Use two-hue palettes centered on a neutral midpoint:
- `"RdYlGn"` — red=bad, green=good (returns, performance)
- `"RdBu"` — red vs blue (temperature anomalies, sentiment)
- `"PuOr"` — purple vs orange (balanced, colorblind-safe)

### For Categorical Data

Use qualitative palettes (no implied order):
- `"Set2"` — muted, colorblind-friendly
- `"Dark2"` — bold, high contrast
- `"Paired"` — for paired categories

### Manual Conditional Styling

For binary good/bad indicators, use explicit colors with `tab_style`:
```python
# Green for positive, red for negative — applied in one call
positive_rows = df[df["return"] >= 0].index.tolist()
negative_rows = df[df["return"] < 0].index.tolist()

gt = (
    gt
    .tab_style(
        style=style.fill(color="#c6efce"),
        locations=loc.body(columns="return", rows=positive_rows)
    )
    .tab_style(
        style=style.fill(color="#ffc7ce"),
        locations=loc.body(columns="return", rows=negative_rows)
    )
)
```

**Never** loop row-by-row calling `tab_style` once per row. Collect row indices into lists first.

## Typography & Spacing

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

## Patterns by Table Type

### Financial Tables

- Use `fmt_currency` with explicit `currency=` code
- Use `accounting=True` for tables where negatives appear (shows parentheses)
- Group by time period with `groupname_col` or `tab_spanner`
- Consider `compact=True` for large values (millions/billions)
- Highlight totals row with `tab_style(style=style.text(weight="bold"), locations=loc.body(rows=[last_row]))`

### Scientific/Research Tables

- Use `fmt_scientific` for values spanning many orders of magnitude
- Use unit notation in column labels: `cols_label(speed="Speed ({{m/s}})")`
- Include confidence intervals or error bounds as separate columns under a spanner
- Use `sub_missing(missing_text="—")` for unavailable data points

### Comparison Tables

- Use `data_color` to create heat-map effects across comparable columns
- Set explicit `domain=` to ensure consistent color mapping
- Use `fmt_number` with consistent `decimals=` across all comparable columns
- Consider `opt_row_striping()` for tables with many rows

### Summary/Dashboard Tables

- Use `opt_stylize(style=1, color="blue")` for quick professional theming
- Bold key metrics with `tab_style(style=style.text(weight="bold"), ...)`
- Use `fmt_number(compact=True)` for large numbers (1.2M instead of 1,200,000)
- Add context with sparklines via `fmt_nanoplot` if data supports it

### Time Series Tables

- Use dates as `rowname_col` for chronological data
- Format with `fmt_date(date_style="m_day_year")` for readability
- Use `data_color` on value columns to show trends visually
- Consider whether a chart would serve the user better than a table

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
