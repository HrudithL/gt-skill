# Heatmap

## Intent
Show 25 years of population growth across Ontario's 15 largest cities
as a heatmap, so the reader spots boom/bust patterns at a glance —
which decades each city grew, which it stagnated, and which (if any)
shrank — without having to read every cell.

## Data shape
- Source: `data/towny.csv` (414 Ontario municipalities, 1996–2021 Census)
- Rows: 15 (top by 2021 population)
- Key columns:
  - `name` (str) — city name
  - `population_2021` (int) — anchor column for the leaderboard ordering
  - `pop_change_<start>_<end>_pct` (float, fractional) — inter-Census growth across each of the five Census windows
- Notable nulls / outliers: a couple of cities show a single Census decline (e.g. Sudbury 1996–2001); the diverging palette correctly renders those as red so they stand out.

## Design choices
- **Restrict to top 15 by 2021 population** — the heatmap pattern lives in the eye's ability to scan a small grid; all 414 municipalities would be unreadable.
- **Diverging palette (red → white → green)** — growth-rate is intrinsically signed; a sequential palette would conflate zero with one extreme. RdYlGn is the conventional choice for "bad → neutral → good".
- **Symmetric domain anchored at ±|max|** — `domain=[-abs_max, abs_max]` so 0% always maps to the midpoint regardless of the values present. This is the correctness invariant for diverging color: if the domain were unbounded, a column of all-positive values would map 0% to red and mislead the reader.
- **Heatmap convention documented in the source note** — "red = decline, green = growth, midpoint at 0%". A color-bar would be cleaner but is not native to gt; the explicit note is the next best thing for a reader scanning the table cold.
- **`fmt_percent(decimals=1, force_sign=True)` on cells** — the cells retain their numeric labels so the heatmap is also auditable; `force_sign` gives a redundant directional signal for color-blind readers (the `+`/`−` is independent of hue).
- **Spanner `"Inter-Census growth"`** — groups the five growth columns under one label so the eye parses them as one block, leaving City and 2021 population as the anchor columns on the left.
- **Population formatted with `fmt_integer`** — thousands separator on a seven-digit count.
- **Header carries the time window** — `1996–2021` in the subtitle, so the reader does not have to deduce it from the column labels.

## What was deliberately omitted
- **A literal color-bar legend** — gt does not natively render one; replicating it via tab_style would clutter the footer. The source-note hint plus the cell labels do the same job.
- **Per-city ranking column** — would compete with the heatmap for the reader's eye; the order (by 2021 population) is already an implicit ranking.
- **Province-wide average row** — would force the reader to add a sixteenth row of context; the heatmap is about within-city patterns over time.
- **Land area / density columns** — out of scope for "growth across windows"; would belong in a separate table.

## Anti-patterns avoided
- **No `data_color`** → **diverging palette across all five growth columns**: without color, the heatmap archetype does not exist.
- **Sequential palette on signed data** → **diverging palette centered at 0**: a single-direction ramp would tell the reader that 0% growth is in the middle of the data, not the middle of the meaning.
- **Rainbow / jet palette on a quantitative variable** → **perceptually-ordered RdYlGn**: rainbows have no luminance ordering and are the textbook "do not use" for any continuous quantitative variable. The bad example shows this explicitly on one column.
- **Unbounded `domain`** → **`domain=[-abs_max, abs_max]`**: anchors 0% to the midpoint regardless of the data range.
- **Color without numeric labels** → **`fmt_percent` on top of `data_color`**: the table stays auditable and color-blind-friendly.
- **No source / no gradient legend** → **`tab_source_note` describing the scale**: heatmaps without a legend are illegible.
