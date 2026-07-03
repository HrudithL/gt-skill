# Small Color — Light Vertical Dividers

Add thin vertical borders between logical column groups (spanners, or blocks of related columns) so the reader sees the column structure at a glance.

## When to use

- The table has **≥2 spanners** and the columns under each spanner should read as a unit.
- There are logical column groups even without spanners (e.g., "inputs" | "outputs" | "metadata") and the reader benefits from a visual seam.
- Existing horizontal-only borders make the table feel like unstructured columns.

## Recipe

```python
from great_tables import GT, style, loc

gt = (
    GT(df)
    .tab_spanner(label="Inputs",  columns=["a", "b"])
    .tab_spanner(label="Outputs", columns=["c", "d"])
    # Vertical rule between the two spanner groups: put a right border on the
    # last column of the first group.
    .tab_style(
        style=style.borders(sides="right", color="#e5e7eb", weight="1px"),
        locations=loc.body(columns="b"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#c7ccd3", weight="1px"),
        locations=loc.column_labels(columns="b"),
    )
)
```

## Rules

- **Thin (1px) and low-saturation.** Neutral greys (`#c7ccd3`–`#e5e7eb`) are the safe default; a very light tint of the table's brand color (e.g. `#d5e0ec` for a blue-themed table) is also acceptable and helps the divider feel part of the theme instead of applied on top of it. Anything mid-saturation or thicker than 1.5px becomes a Big Color structural bar.
- **Match the divider in both the header and body** so the seam runs the full height of the table. A seam only in the body reads as a rendering bug.
- **One divider per logical seam.** Do not add a vertical rule between every column — that's a spreadsheet, not a table.
- **Do not** add vertical dividers under a heatmap or column-gradient — the fill already separates columns visually and adding rules crowds the cells.

## Counts as

One Small Color treatment for the whole set of dividers in a table.
