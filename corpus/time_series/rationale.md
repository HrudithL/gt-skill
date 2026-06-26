# Time series

## Intent
Summarize the trajectory of New York City air quality across the summer
of 1973 so an environmental reporter can lead a season-in-review with
one image. The reader should see month-to-month direction in ozone, the
within-month volatility (sparkline), and the supporting weather
conditions, all sorted in calendar order.

## Data shape
- Source: `data/airquality.csv`
- Rows: 5 (one per month, May through September, aggregated from 153 daily observations)
- Key columns:
  - `month_label` (str) — `"May"`, `"June"`, …
  - `ozone_mean` (float, ppb) — monthly mean of daily Ozone
  - `ozone_delta` (float, ppb) — month-over-month change in mean ozone
  - `ozone_trend` (str of space-separated daily values) — fed to `fmt_nanoplot` for the sparkline
  - `temp_mean` / `wind_mean` / `solar_mean` — monthly conditions
- Notable nulls / outliers: Ozone has missing days; dropped before
  building the sparkline series so `fmt_nanoplot` does not error.

## Design choices
- **Aggregate to monthly** — five rows over the five months in the data, not 153 raw daily rows. The story is seasonal; the row IS the time-series unit.
- **Calendar-ordered, human-named months** — `"May"` … `"September"`, not `5` … `9`. Numeric month codes force the reader to translate.
- **Sparkline via `fmt_nanoplot`** — inline daily-ozone plot per month, so the reader gets shape next to summary. Chose nanoplot over a side-bar chart because the trend belongs in the row, not in a separate visual.
- **Month-over-month delta** — `force_sign=True` so the `+` / `−` is the directional signal; pairs with the sparkline (shape) for the "what changed and how" view.
- **Spanner labels** — `"Ozone (ppb)"` and `"Conditions"` group three columns each so the reader parses the units once.
- **`html` cells for unit symbols** — `°F`, `W/m²`, `Δ`. Inline HTML keeps the units typographically correct without resorting to plain `deg F`.
- **`sub_missing` em-dash** — May has no prior month, so its delta is `NaN`. `—` reads as "not applicable" rather than as zero or as a blank.
- **One decimal on means** — half a ppb is below instrument resolution; more decimals would be spurious precision.
- **Source note** — names the agency and the window so the table is citable when detached from the prompt.

## What was deliberately omitted
- **A `Day` column** — sub-monthly resolution lives in the sparkline; printing daily rows would dilute the seasonal story.
- **Year column** — the dataset is from 1973 only; redundant on every row.
- **Coloring** — the sparkline already shows direction. Coloring the delta column on top would over-encode the same signal.
- **A separate ozone-vs-WHO-standard reference** — out of scope for "summer in review"; would shift the table into policy commentary.

## Anti-patterns avoided
- **Daily rows in CSV order** → **5 monthly aggregates in calendar order**: the bad version dumps 20 rows the reader cannot scan; the good version is the season at a glance.
- **Raw integer month codes** → **named months**: `Month=7` forces a mental lookup that `"July"` removes.
- **No trend indicator** → **inline sparkline + signed delta**: trend is the point of a time series; omitting it defeats the archetype.
- **No header, no source note** → **`tab_header` + `tab_source_note`**: a chart without provenance cannot be cited.
- **`fmt_number` on a numeric month column** → **`map` to month names before plotting**: formatters cannot fix a semantically wrong column type.
