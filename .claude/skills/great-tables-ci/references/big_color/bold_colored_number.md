# Big Color — Bold + Colored Number

Bold + strong color on a few outlier cells so they pop against an otherwise-quiet table.

## When to use

- A small fraction of cells (roughly ≤20% of the rows in the target column) genuinely stand out — extremes, threshold breaches, records.
- You want the table body to stay mostly neutral so that these few cells read as "the answer."
- The rest of the column is not being gradient- or diverging-filled (this technique is the *alternative* to filling the whole column, not an addition to it).

If you want to emphasize every row in the column, use `column_gradient_fill.md` or `diverging_fill.md` instead — this technique loses meaning when overused.

## Recipe

```python
from great_tables import GT, style, loc

threshold_hi = 0.10
threshold_lo = -0.10

hi_rows = df.index[df["return"] >=  threshold_hi].tolist()
lo_rows = df.index[df["return"] <=  threshold_lo].tolist()

gt = (
    GT(df, rowname_col="period")
    .fmt_percent(columns="return", decimals=1, force_sign=True)
    .tab_style(
        style=style.text(weight="bold", color="#2F4A38"),      # Forest solid = positive outliers
        locations=loc.body(columns="return", rows=hi_rows),
    )
    .tab_style(
        style=style.text(weight="bold", color="#5C2E2E"),      # Oxblood solid = negative outliers
        locations=loc.body(columns="return", rows=lo_rows),
    )
)
```

## Rules

- **Collect row indices into a list first**, then one `tab_style` call per style — never loop `tab_style` per row. Cap at ~1/3 of the column or switch to a gradient/diverging fill.
- **Dark Academia solids** (`references/palettes.md` §1): Forest `#2F4A38` = positive/good, Oxblood `#5C2E2E` = negative/bad, Ochre `#9A7B33` = single "warning" tier. No more than 2–3 text colors in one table.
- **`rows=`** takes positional row indices in the displayed table, not DataFrame index values (only match when the index is `0..n-1`).
- Bold-only (no color) variant: use for *importance*, not *direction*.

## Counts as

One Big Color treatment even though it touches multiple cells: the treatment answers a single question ("which values are extreme?").
