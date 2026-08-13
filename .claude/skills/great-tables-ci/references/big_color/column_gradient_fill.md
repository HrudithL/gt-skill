# Big Color — Column Gradient Fill

Apply `data_color` to an ordered numeric column so each cell's background encodes its magnitude on a sequential palette (mini-heatmap).

## Trigger (computable — not optional)

**IF an ordered numeric magnitude is present over ≥5 rows ⇒ it QUALIFIES as a colored
measure** (the hero, if it is the only one that qualifies). Deterministic, not a judgment
call. (Below 5 rows a gradient reads as random pastel — it does not qualify; use
`big_color/full_row_highlight.md` instead, see the last rule.)

"Qualifies" is not the same as "earns a full heatmap fill." There is no numeric cap
on colored measures — color what the request is actually about, with the correct
palette for each (the ranking below decides which measures that is). A measure that
qualifies but isn't part of what the request is about renders fully plain at the
measure level: no whole-column fill, no whole-column bold, no whole-column
text-color treatment — its magnitude is carried by the number alone. (This doesn't
ban `bold_colored_number.md`'s separate technique of bolding a handful of individual
outlier cells in an otherwise-plain column — that's a few-cells technique, not a
whole-measure consolation.) This applies regardless of how many other measures
already carry a color fill.

## Which measures earn the full fill first (deterministic priority)

Rank every qualifying measure by this order (total and computable, so two runs on the
same prompt+data reach the same ranking):

1. **Prompt-named / emphasised measures first**, in the order they appear in the
   prompt. A measure the user explicitly names, asks to "show/highlight/compare", or
   puts in the title outranks any unnamed one.
2. **Then leftmost-first by DataFrame column order.** Among measures with equal prompt
   priority (e.g. none named, or several named at once), the one whose column appears
   earlier (smallest column index) wins.

The ranking above is fully deterministic — two runs on the same prompt+data always
reach the same order. How many top-ranked measures actually earn a full fill is a
judgment call: weigh how many measures the request's core ask is actually about
against whether a 3rd or 4th fill would make the table read as noise. There is no
fixed count and no numeric cap. A measure that doesn't make the cut renders fully
plain at the measure level — no whole-column fill, no whole-column bold, no
whole-column text-color treatment — its magnitude is carried by the number alone
(again, this doesn't affect `bold_colored_number.md`'s few-outlier-cells technique).
A measure that spans several facet columns (a matrix/heatmap block) counts as **one**
measure in this ranking.

## When to use

- The column is an **ordered numeric measure** (revenue, volume, score, count, rate).
- The table has **≥5 rows** so the gradient has enough steps to read.
- Relative magnitude — not just the raw number — is part of the story.
- The values have a natural direction (higher = better, higher = worse, or purely neutral quantity).

If the column has both negatives and positives with opposite meaning, use `diverging_fill.md` instead.

## Recipe

```python
import numpy as np
from great_tables import GT

# DATA-DRIVEN domain, shared across ALL facet columns of this ONE measure.
# Never a per-column domain, never a round guess — compute it from the frame.
# Backend-neutral: .to_numpy() + np.nanmin/nanmax return a scalar on BOTH pandas and
# polars. (df[cols].min().min() returns a 1-row frame on polars and breaks float(...).)
cols = ["measure"]                              # every column that IS this measure
lo = float(np.nanmin(df[cols].to_numpy()))     # min across all facet columns
hi = float(np.nanmax(df[cols].to_numpy()))     # max across all facet columns

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
  Compute with the backend-neutral `float(np.nanmin(df[cols].to_numpy()))` /
  `float(np.nanmax(df[cols].to_numpy()))` (see recipe comments); DATA-DRIVEN, never a
  round guess, never per-column.
- **Palette by semantic — pin it from `palettes.md` §3, not by aesthetic.** Neutral
  magnitude (money/price/volume/count/population) → `Blues` (always); good-direction
  ("more is better") → `Greens`; warning/worse → `Reds` (`Oranges` only as the documented
  alternate).
- **Do not gradient-fill the stub or identifier columns** — the gradient must apply to the measure only.
- **Leave `truncate=False`** (default) — outliers keep the extreme color.
- **Do not** also bold or color the text of the same cells — the fill alone carries the signal.
- **≥5 rows** or skip — use `big_color/full_row_highlight.md` instead.

## Counts as

One Big Color treatment. If you also add a totals row that participates in the gradient, that's still one treatment.
