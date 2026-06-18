---
name: great-tables
description: Produce a polished, publication-ready table image (PNG) from a CSV or other tabular data file using the Python `great_tables` package. Invoke this skill for ANY request that asks to make, build, render, show, display, or visualize a table from data — including financial, scientific, summary, or comparison tables. Do not write `great_tables` code without loading this skill first.
---

# Great Tables

When the user asks for a table, first read a sample of the data file to understand its columns and types, then write a single Python script (using `pandas` to load the data and `from great_tables import GT, md, html`) that constructs a `GT` table, applies the right `fmt_*` method for each column's data type (`fmt_currency` for money, `fmt_date` / `fmt_datetime` for dates, `fmt_number` / `fmt_integer` for numerics, `fmt_percent` for rates), adds a clear `tab_header(title=..., subtitle=...)`, groups related columns with `tab_spanner` when natural, hides clutter columns with `cols_hide`, renames columns to human labels with `cols_label`, and saves the final image with `gt.save("table.png")`. Write the script to `table.py` in the current working directory, run it with `python table.py`, confirm `table.png` was produced, and stop once the table renders cleanly.

References:
- [Great Tables docs](https://posit-dev.github.io/great-tables/)