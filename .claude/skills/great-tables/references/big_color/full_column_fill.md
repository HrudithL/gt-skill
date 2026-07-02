# Big Color — Full Column Fill

Apply a solid background color to every body cell in one (or a small number of) column(s) so that the column reads as *the* column in the table.

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
        style=style.fill(color="#eef4fb"),          # pale, saturated enough to notice
        locations=loc.body(columns="focus_col"),
    )
    .tab_style(
        style=style.text(weight="bold"),            # optional: reinforce the column
        locations=loc.body(columns="focus_col"),
    )
)
```

## Rules

- **One fill color for the whole column.** Do not vary it row-by-row — that's a different technique (`column_gradient_fill` or `status_cell_fill`).
- **Pale, not saturated.** A saturated fill fights with the text on top and blows the color budget. Aim for a fill where black body text still reads cleanly.
- **Match the fill hue to the column's meaning** using the palette guidance in `SKILL.md` (green = positive measure, red/orange = risk/warning, blue = neutral).
- **Also fill the column-label header** for that column if you want the emphasis to extend into the header — pair with the `column_label_emphasis` technique on just that column.
- **Do not** fill the stub column this way. Stub is structural — use Small Color's `stub_tint` instead.

## Counts as

One Big Color treatment (even if you also bold the text — bold + fill on the same target answers one question).
