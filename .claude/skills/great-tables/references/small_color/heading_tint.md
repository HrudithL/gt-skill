# Small Color — Heading Tint

Apply a *very* light background fill to the column-label row so the header separates from the body without becoming a loud band.

## When to use

- The column-label row is hard to distinguish from the first body row at a glance.
- You want the polish of a defined header without the editorial weight of `column_label_emphasis.md` (the Big Color equivalent).
- The table doesn't already use `opt_stylize()` or another theme that colors the header.

If the header needs to be a strong visual anchor (branded look, defining spanners), use Big Color's `column_label_emphasis.md` instead.

## Recipe

```python
from great_tables import GT

gt = (
    GT(df)
    .tab_options(
        column_labels_background_color="#f4f5f7",       # near-white cool grey
        column_labels_font_weight="bold",               # keep the labels readable
        column_labels_border_bottom_color="#d0d4da",    # subtle rule under the header
    )
)
```

## Rules

- **Near-white tint only** — pale grey, or a very light tint of a color already used elsewhere in the table (e.g. `#eef3fa` for a blue-themed table, `#eef7ee` for a green-themed one). If the tint is clearly a mid-saturation color, it's Big Color — either commit to `column_label_emphasis.md` or back off.
- **Bold font weight is fine** and often improves readability; it doesn't count against the color budget.
- **Add a slightly-darker bottom border** under the header at the same time — the border + tint pair gives the header a "seat" without needing a strong fill. If the tint is a color, use a slightly-darker shade of the same hue for the border.
- **Do not** also tint the stub, source note, and totals row with different pale shades. Pick one polish move and let it echo elsewhere (e.g., stub tint uses the *same* near-white as the header tint, not a different one).

## Counts as

One Small Color treatment. If the matching bottom border is part of a broader `subtle_borders.md` pass, that border still counts under `subtle_borders`, not separately.
