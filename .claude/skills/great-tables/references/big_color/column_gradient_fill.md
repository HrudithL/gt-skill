# Big Color — Column Gradient Fill

Apply `data_color` to an ordered numeric column so that each cell's background encodes its magnitude on a sequential palette. The column becomes a mini-heatmap.

## Trigger (computable — not optional)

**IF an ordered numeric magnitude is present over ≥5 rows ⇒ it IS a colored measure**
(the hero, if it is the only one). This is a deterministic branch, **not** a judgment
call — do not leave the magnitude uncolored, and do not ask "should this be colored?"
The ≥5-row magnitude answers it: yes. (Below 5 rows a gradient reads as random pastel —
use a targeted highlight instead; see the last rule.)

## When to use

- The column is an **ordered numeric measure** (revenue, volume, score, count, rate).
- The table has **≥5 rows** so the gradient has enough steps to read.
- Relative magnitude — not just the raw number — is part of the story.
- The values have a natural direction (higher = better, higher = worse, or purely neutral quantity).

If the column has both negatives and positives with opposite meaning, use `diverging_fill.md` instead.

## Recipe

```python
from great_tables import GT

# DATA-DRIVEN domain, shared across ALL facet columns of this ONE measure.
# Never a per-column domain, never a round guess — compute it from the frame.
cols = ["measure"]                              # every column that IS this measure
lo = float(df[cols].min().min())                # min across all facet columns
hi = float(df[cols].max().max())                # max across all facet columns

gt = (
    GT(df, rowname_col="entity")
    .fmt_number(columns=cols, decimals=1)
    .data_color(
        columns=cols,
        palette="Blues",         # hue by semantic — palettes.md §3 lookup (neutral magnitude → Blues, always)
        domain=[lo, hi],         # explicit, ONE shared domain over all facet columns — never omit
        truncate=False,          # outliers keep the extreme color, never disappear
        na_color="#808080",      # NA/empty neutral (palettes.md §2)
    )
)
```

## Rules

- **Domain = `[min, max]` across ALL facet columns of the measure — one shared domain.**
  Compute `lo`/`hi` from the frame (`df[cols].min().min()` / `.max().max()`); the bound
  must be **DATA-DRIVEN**, never a round guess. If the measure spans several facet
  columns, they share this **single** domain (not a per-column domain), so equal values
  read as equal color across the block. A too-narrow domain flattens the extremes; a
  too-wide domain washes out the middle.
- **Palette by semantic — pin it from `palettes.md` §3, not by aesthetic.** It is a
  lookup, not a choice: neutral magnitude (money/price/volume/count/population) → `Blues`
  (always); good-direction ("more is better") → `Greens`; warning/worse → `Reds`
  (`Oranges` only as the documented alternate). This kills the Blues-vs-Greens coin-flip.
- **Do not gradient-fill the stub or identifier columns** — the gradient must apply to the measure only.
- **Leave `truncate=False`** (default). If an outlier appears later it should still get the extreme color, not disappear.
- **Do not** also bold or color the text of the same cells — the fill already carries the signal. Layering both crowds the cell.
- **≥5 rows** or skip: a 3-row gradient reads as random pastel; use a targeted highlight instead.

## Counts as

One Big Color treatment. If you also add a totals row that participates in the gradient, that's still one treatment.
