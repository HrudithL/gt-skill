---
name: great-tables
description: Build publication-quality data tables as rendered PNG images using the great_tables (gt) Python package, applying a consistent house style every time -- theming, row striping, heatmap/data-color treatments, titles, subtitles, source notes, and footnotes. Use this skill whenever the user wants a polished, presentation-ready, or "pretty" table rather than a plain markdown table, regardless of whether the data comes from a DataFrame already in memory, a CSV/Excel file, a SQL query result, or messy/raw data that needs cleaning first. Trigger this whenever the user mentions "great_tables", a "gt table", a styled/formatted/publication-quality table, a table with a heatmap or color-coded cells, or asks to turn a dataset/spreadsheet/query result into a table image or graphic for a slide, report, or doc. Always produces an image via gtsave() when this skill is used -- never just a markdown table.
---

# Great Tables (gt): consistent, publication-quality tables

## Why this skill exists

A markdown table is fine for scanning data in chat. `great_tables` (imported as
`gt`) produces something you'd actually put in a report, deck, or dashboard --
real typography, color, and structure rendered into an image. The API itself
isn't hard to call. The hard part is making the same good design decisions
*every single time*: which columns get which formatting, whether a heatmap
earns its place, what the title should say, whether there's a source note.
This skill exists so those decisions get made once (in the bundled house-style
module) and reused, so table #47 looks as considered as table #1 -- not a
random walk through gt's very large option space.

Treat every output as something that will sit next to a professionally made
table. That means: no raw `snake_case` column headers, no unexplained numbers
without units or currency symbols, no table without a title, and no heatmap
without a legible domain.

## Setup (do this once per session, before the first `gtsave()`)

`gtsave()` renders through a real, invisible headless Chrome browser under the
hood (via the `nokap` package) -- that's what makes the PNG look exactly like
the styled HTML. This means an actual Chrome/Chromium binary has to exist on
the system, and plenty of sandboxes/containers have neither one nor root
access to install one the normal way.

Before running any script that ends in `gtsave()`, run:

```bash
source scripts/setup_gt_chrome.sh
```

Use `source`, not `bash` -- it exports `CHROME_PATH` and `LD_LIBRARY_PATH` into
the current shell, and those need to still be set when the Python process
that calls `gtsave()` starts. Then run the table script in that same shell
call (e.g. `source scripts/setup_gt_chrome.sh && python3 build_table.py`).

The script is idempotent and fast (well under a second) once a working
browser has been found -- it only does the heavier work of installing a
Playwright-managed Chromium and patching in missing shared libraries (both
without needing root) the first time nothing usable is found. If it ultimately
fails, it prints where its log files are; read those before improvising a
different fix.

Also make sure the Python side is installed: `pip install great_tables pandas
--break-system-packages` (add `polars` too if you'd rather use that; gt works
with either). Only add `--break-system-packages` if pip complains about an
externally-managed environment.

## Workflow

### 1. Get to one clean DataFrame, whatever the source

gt takes a pandas or polars DataFrame -- the work before that point is making
sure it's a *clean* one:

- **Already a DataFrame**: check dtypes before formatting. A column that
  *looks* numeric but got read in as text (common after a `.csv` round-trip)
  will silently fail or misbehave in `fmt_number`/`fmt_currency`/`data_color`.
- **CSV/Excel file**: load it, then actively look for the usual mess --
  currency strings like `"$1,200.50"` that need stripping to floats before
  `fmt_currency` can format them (gt formats numbers, it doesn't parse
  currency strings), percent strings like `"12%"` needing conversion to
  `0.12`, inconsistent date formats, stray whitespace in string columns,
  and a header row that isn't actually row 0.
- **SQL query result**: usually already well-typed, but check for `None`/NULL
  handling and whether numeric precision (e.g. `Decimal` types) needs casting
  to float for gt's formatters.
- **Messy/raw data generally**: decide deliberately what happens to missing
  values (see step 5) rather than silently dropping rows -- dropping changes
  what the table is claiming to show.

Do this cleanup in pandas/polars *before* handing the DataFrame to `GT()`.
Trying to fix data problems with gt's text-transform methods after the fact
is far more brittle.

### 2. Decide the table's structure before styling it

Before touching color or theme, decide:

- **Title and subtitle** (`tab_header`) -- every table gets one. Write a
  title that says what the table *is* (not just relabeling the file), and use
  the subtitle for scope/timeframe/qualifier. Never ship a table with no
  title because the request didn't explicitly ask for one -- infer it from
  context the same way a human analyst would caption their own chart.
- **Row labels / groups** -- if one column is a natural row identifier (a
  name, an ID), consider `rowname_col=` to move it into the stub. If rows
  fall into natural categories, `groupname_col=` creates real row groups
  instead of leaving the category as just another column.
- **Spanners** (`tab_spanner`) -- if several columns are sub-parts of one
  concept (e.g. `q1_actual`/`q1_target` both under "Q1"), group them under a
  spanner instead of leaving the relationship implicit in the column names.
- **Source note and footnotes** -- add a `tab_source_note` describing where
  the data came from (system name, file, date range) whenever that's known.
  If a specific cell or column needs a caveat (an estimate, a restated
  figure), use `tab_footnote` rather than cramming it into the column label.

### 3. Format every column deliberately

Never leave a numeric column in its raw display form. Match the formatter to
what the number *means*, not just its dtype -- see
`references/formatting_decisions.md` for the full decision guide (currency
vs. plain number vs. percent, decimal-place conventions, date/time formats,
booleans, and how to relabel columns out of raw `snake_case`). The short
version: money gets `fmt_currency`, ratios/rates get `fmt_percent`, counts get
`fmt_integer`, and every column header gets a human label via `cols_label()`
(or the `humanize_labels()` helper below) -- a reader should never see a
column literally called `yoy_chg` or `col_3`.

### 4. Apply the house style

Import the bundled helpers instead of hand-rolling theme calls:

```python
from gt_house_style import apply_house_style, add_heatmap, humanize_labels, HOUSE_STYLE
```

- `humanize_labels(gt_tbl, df, overrides={...})` -- turns raw column names
  into title-cased labels, with `overrides=` for anything that needs a
  specific label (units, acronyms, currency symbols).
- `add_heatmap(gt_tbl, df, columns, kind="auto")` -- colors cells by value
  with a sensible, explicit domain (computed from the real data, not gt's
  full auto-range) and picks a colorblind-friendly sequential palette for
  magnitude-only data or a diverging one for signed data (% change,
  profit/loss) automatically. Only reach for a heatmap where it earns its
  place -- a heatmap on a column of unique IDs or on a table with three rows
  adds noise, not signal.
- `apply_house_style(gt_tbl)` -- applies the shared color/border preset, row
  striping, font stack, and header alignment. Call this *last*, after content
  is in place. Override individual arguments (e.g. `color="green"` for a
  growth-themed table) when the request calls for it -- the defaults in
  `HOUSE_STYLE` are a starting point, not a constraint.

See `references/api_cheatsheet.md` for the full, verified signatures of every
gt method mentioned in this file (formatters, `data_color`, `opt_stylize`,
`opt_table_font`, `gtsave`, and the `loc`/`style` classes for one-off cell
styling beyond what the house-style helpers cover).

### 5. Handle missing values on purpose

Call `.sub_missing(missing_text="—")` (or reuse `HOUSE_STYLE["missing_text"]`)
so blanks read as "intentionally not available" instead of an empty box that
looks broken. Do this for the whole table unless specific columns need
different missing-value text (e.g. "N/A" vs. "TBD" carry different meanings).

### 6. Export

Every table-building script should end with a `gtsave()` call to a `.png`
(use `.pdf` only if the user specifically wants print/vector output):

```python
gt_tbl.gtsave("output.png", zoom=2, expand=10)
```

`zoom=2` gives a retina-quality image (the house default worth using almost
always); bump `expand` for tables with a lot of whitespace-sensitive styling,
or leave it at the gt default of `5` for compact tables. Run the script with
`scripts/setup_gt_chrome.sh` sourced beforehand (step 0) -- without it,
`gtsave()` raises a Chrome-not-found error in any environment without a
browser already configured.

## Full worked example

```python
import pandas as pd
from great_tables import GT, md
from gt_house_style import apply_house_style, add_heatmap, humanize_labels

df = pd.DataFrame({
    "region": ["North", "South", "East", "West"],
    "revenue": [120_000, 95_000, 143_000, 88_000],
    "yoy_change": [0.12, -0.05, 0.22, -0.15],
})

tbl = (
    GT(df)
    .tab_header(
        title="Regional Performance",
        subtitle=md("Revenue and year-over-year change, **Q2 2026**"),
    )
    .fmt_currency(columns="revenue", decimals=0)
    .fmt_percent(columns="yoy_change", decimals=1)
    .sub_missing(missing_text="—")
    .tab_source_note(source_note="Source: internal sales system, extracted 2026-07-09.")
)
tbl = humanize_labels(tbl, df, overrides={"yoy_change": "YoY Change"})
tbl = add_heatmap(tbl, df, "yoy_change")
tbl = apply_house_style(tbl)

tbl.gtsave("regional_performance.png", zoom=2, expand=10)
```

Run it as:

```bash
source scripts/setup_gt_chrome.sh && python3 build_table.py
```

## Bundled resources

- `scripts/setup_gt_chrome.sh` -- provisions a working headless Chrome for
  `gtsave()` with no root required; source it before running any gt script.
- `scripts/gt_house_style.py` -- `apply_house_style()`, `add_heatmap()`,
  `humanize_labels()`, and the `HOUSE_STYLE` design-token dict. Import this in
  every table script rather than re-deciding the look each time.
- `references/api_cheatsheet.md` -- verified signatures for gt's header/body/
  footer methods, every `fmt_*` formatter, `data_color`, the `opt_*` theming
  methods, `tab_style`/`loc`/`style` for custom cell styling, and `gtsave`.
- `references/formatting_decisions.md` -- the decision guide for which
  formatter fits which kind of column, sequential vs. diverging heatmaps,
  when to use a stub/row-groups/spanners, and common messy-data pitfalls
  (currency strings, percent strings, inconsistent dtypes) with fixes.