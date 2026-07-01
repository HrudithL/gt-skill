# Small Color — Stub Tint

Apply a very light background fill to the stub column (the column set via `rowname_col=`) so the row labels visually separate from the value columns.

## When to use

- The table has a `rowname_col` and the stub visually blurs into the first value column.
- No Big Color treatment is already touching the stub or the leftmost data column.
- The reader will use the stub as a lookup key ("find the row for X, then read across").

## Recipe

```python
from great_tables import GT, style, loc

gt = (
    GT(df, rowname_col="entity")
    .tab_style(
        style=style.fill(color="#f7f7f9"),              # near-white grey
        locations=loc.stub(),
    )
)
```

Optionally match the stubhead (the column-label cell above the stub):

```python
gt = gt.tab_style(
    style=style.fill(color="#f7f7f9"),
    locations=loc.column_labels(columns="entity"),      # if the stub column still appears in column_labels
)
```

## Rules

- **Near-white grey.** Same intensity guidance as row striping — barely perceptible.
- **Do not fill the stub with a saturated color.** That's a Big Color move (`full_column_fill.md`) and would misuse the stub as a data column.
- **Do not** combine with row striping unless you've tested that the stripe and the tint don't cross at an ugly darker shade in the striped stub cells. Usually pick one or the other.
- Consider slight bold weight on the stub text if the labels are the primary lookup key — bold text on the stub is a typographic move, not a color one, and doesn't count against the Small Color budget.

## Counts as

One Small Color treatment.
