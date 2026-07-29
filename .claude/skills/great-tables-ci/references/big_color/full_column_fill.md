# Big Color — Full Column Fill

Solid background on every body cell in one (or a few) column(s) so it reads as *the* column.

## When to use

- One column carries the primary message and its values are **categorical, ordinal, or otherwise not well-suited to a gradient** (labels, tiers, tags).
- You want the reader's eye to lock onto that column before scanning left/right.
- The fill is a *label*, not a *scale* — the same shade on every cell, not a gradient.

If the column is an ordered numeric measure, use `column_gradient_fill.md` instead so the fill carries magnitude.

## Recipe

```python
from great_tables import GT, style, loc

gt = (
    GT(df)
    .tab_style(
        style=[style.fill(color="#22384F"),          # Dark Academia solid (Navy default)
               style.text(color="#ffffff", weight="bold")],   # white text on the solid
        locations=loc.body(columns="focus_col"),
    )
)
```

## Rules

- **One fill color for the whole column** — don't vary row-by-row (that's `column_gradient_fill` or `status_cell_fill`).
- **Solid Dark Academia hex + white text** (non-gradient Big Color). Navy `#22384F` is the default; harmonize to the table's DA hue per `references/palettes.md` §1 (Forest `#2F4A38`, Oxblood `#5C2E2E`, Espresso `#4A3A2C`, Ochre `#9A7B33`, Tan `#8A7452`). Never a pale/washed tint here — that's for the stub.
- Optionally also fill the column-label header with the same DA solid (pair with `column_label_emphasis`) to extend the emphasis upward.
- **Do not** fill the stub column this way — use the stub tint in `references/small_color.md` instead.

## Counts as

One Big Color treatment, even with bold added.
