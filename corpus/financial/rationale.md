# Financial

## Intent
Give a reader the 2015 year-in-review for the S&P 500 in one screen:
where the index closed each month, the intraday range, the monthly
return, and the running year-to-date return. The implied audience is
someone scanning year-end coverage who needs to answer "was it a good
year, and which months did the work?" without opening a spreadsheet.

## Data shape
- Source: `data/sp500.csv`
- Rows: 12 (one row per month of 2015, aggregated from 252 trading days)
- Key columns:
  - `month_label` (str) — `"Jan 2015"` style month-year label
  - `close` (float, USD) — last close of the month
  - `high` / `low` (float, USD) — intraday extremes within the month
  - `mom_return` (float, fraction) — close-over-prior-month-close
  - `ytd_return` (float, fraction) — close-over-2014-12-31-close
- Notable nulls / outliers: none. January's MoM uses Dec 2014 close as
  baseline, not NaN, so the first row is meaningful.

## Design choices
- **Title vs subtitle split** — title is `"S&P 500 — 2015 Year in Review"`, subtitle carries the column-level description, because tab_header gives the typographic weight the eye expects (title bold, subtitle muted) without manual styling.
- **Currency columns use `fmt_currency`** — not `fmt_number` with a manual `$` prefix, because `fmt_currency` renders the symbol, thousands separator, and decimals as one locale-aware unit and avoids breaking under RTL display.
- **Returns use `fmt_percent(force_sign=True)`** — the leading `+` on positive months is the at-a-glance up/down signal. Without it, the reader has to compare each value to zero by hand.
- **Spanners on Price and Return** — groups the two return columns under one label so the reader parses "Return" once and the two price extremes plus close fall under "Price ($)". Reduces header-line cognitive load.
- **Up/down coloring via `tab_style` + `loc.body`** — green for non-negative, red for negative, applied to both return columns. Chose `tab_style` over `data_color` because the signal is binary (direction), not continuous (magnitude); a gradient would over-encode.
- **Right-aligned numerics, left-aligned month** — explicit, even though great_tables defaults to right for numerics. Survives refactors that change column dtypes.
- **Source note** — credits the data so the table is interpretable out of context. Required for any financial table that may circulate detached from its original page.

## What was deliberately omitted
- **Volume column** — irrelevant to a "year in review" headline; including it would dilute the narrative and force a fourth spanner.
- **Open price column** — close-to-close is what investor coverage anchors on; intraday open is a different story (gap analysis).
- **Sparklines** — would re-encode the monthly trajectory already visible from MoM/YTD; an extra glyph for no marginal information.
- **Bolding the best/worst month** — the eye finds extremes from the +/- signs and color; adding bold competes with that signal.

## Anti-patterns avoided
- **fmt_number on currency** → **fmt_currency**: a `2043.94` without a `$` could be any quantity; with `$2,043.94` the units are unambiguous.
- **Returns shown as decimal fractions (0.013)** → **fmt_percent with force_sign**: human readers think in "+1.30%", not "0.013".
- **No coloring on direction** → **green/red via tab_style**: turns a 12-row scan into a one-glance read of up vs down months.
- **Raw dataframe column names (`mom_return`, `ytd_return`)** → **cols_label re-labeling to `"MoM"`, `"YTD"`**: the table is for humans, not for the dataframe author.
- **No header, no source note** → **tab_header + tab_source_note**: a financial table without provenance is not citable.
