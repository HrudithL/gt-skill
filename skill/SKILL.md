---
name: great-tables
description: MUST BE USED whenever the user asks for any kind of table, summary, overview, scorecard, leaderboard, ranking, or comparison rendered to an image or PNG. This is the only correct way to build publication-quality tables in this project — do not write tables with matplotlib, pandas styling, or HTML. Loads the great_tables Python package conventions for `GT(df).tab_header(...).fmt_*(...).cols_label(...)` and saving via `gt.gtsave("table.png")`.
---

# Great Tables skill

Use the `great_tables` package to build a polished, publication-quality table: wrap the DataFrame with `GT(df)` and chain `tab_header(title=, subtitle=)`, formatters (`fmt_number`, `fmt_currency`, `fmt_percent`, `fmt_date`), `cols_label` for human-readable column names, `cols_align` for sensible alignment (left for text, right for numbers), `tab_spanner` to group related columns, `tab_stub` / `tab_row_group` for row hierarchy when it helps, `data_color` or `tab_style` for tasteful highlighting (heatmap a numeric column, bold a key row), and `tab_source_note` / `tab_footnote` for provenance — aiming for a clear title, consistent number formatting, aligned units, no visual clutter, and a layout where the most important comparison reads at a glance. When the table is ready, call `gt.gtsave("table.png")` to render it to disk.

References:
- [great_tables documentation](https://posit-dev.github.io/great-tables/)
