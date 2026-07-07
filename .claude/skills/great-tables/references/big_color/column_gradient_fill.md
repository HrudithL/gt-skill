# Big Color — Column Gradient Fill

Apply `data_color` to an ordered numeric column so that each cell's background encodes its magnitude on a sequential palette. The column becomes a mini-heatmap.

## When to use

- The column is an **ordered numeric measure** (revenue, volume, score, count, rate).
- The table has **≥5 rows** so the gradient has enough steps to read.
- Relative magnitude — not just the raw number — is part of the story.
- The values have a natural direction (higher = better, higher = worse, or purely neutral quantity).

If the column has both negatives and positives with opposite meaning, use `diverging_fill.md` instead.

## Recipe

```python
from great_tables import GT

lo, hi = float(df["measure"].min()), float(df["measure"].max())

gt = (
    GT(df, rowname_col="entity")
    .fmt_number(columns="measure", decimals=1)
    .data_color(
        columns="measure",
        palette="Blues",         # Greens = good-direction, Reds/Oranges = warning, Blues = neutral
        domain=[lo, hi],         # explicit — never omit
        na_color="#808080",      # NA/empty neutral (palettes.md §2)
    )
)
```

## Rules

- **Always compute `domain` from the data** (`min()`/`max()`), never guess a round number. A too-narrow domain flattens the extremes; a too-wide domain washes out the middle.
- **Palette by meaning, not aesthetic**: `Greens` for good-direction measures, `Reds`/`Oranges` for warning/risk, `Blues` for neutral quantity. See `SKILL.md` → Color Palette Selection.
- **Do not gradient-fill the stub or identifier columns** — the gradient must apply to the measure only.
- **Leave `truncate=False`** (default). If an outlier appears later it should still get the extreme color, not disappear.
- **Do not** also bold or color the text of the same cells — the fill already carries the signal. Layering both crowds the cell.
- **≥5 rows** or skip: a 3-row gradient reads as random pastel; use a targeted highlight instead.

## Counts as

One Big Color treatment. If you also add a totals row that participates in the gradient, that's still one treatment.
