# Small Color — Compact / Airy Padding

Tune the row and column padding so the table's density matches the amount of data it carries. This is a *color-adjacent* polish: padding changes how much white space surrounds each value, which changes the perceived weight of the whole table.

## When to use

- The table has **many rows (>15)** and default padding makes it feel taller than it needs to be → *compact*.
- The table has **few columns (<5) or few rows (<6)** and default padding leaves it looking cramped in a large container → *airy*.
- You need the table to fit a specific slide or page region and default sizing overshoots or undershoots.

## Recipe — compact (dense data)

```python
from great_tables import GT

gt = (
    GT(df)
    .opt_vertical_padding(scale=0.7)                    # tighter rows
    .opt_horizontal_padding(scale=0.9)                  # slightly tighter columns
    .tab_options(table_font_size="13px")                # optional matching size drop
)
```

## Recipe — airy (small tables)

```python
gt = (
    GT(df)
    .opt_vertical_padding(scale=1.4)
    .opt_horizontal_padding(scale=1.6)
    .tab_options(table_font_size="15px")
)
```

## Rules

- **Scale range 0.7–1.6.** Below 0.7 rows collide; above 1.6 the table becomes a poster.
- **Move vertical and horizontal padding together, in the same direction.** Compact one axis and airing the other looks off-balance.
- **Font size follows padding**: dense tables tolerate 12–13px; airy tables read better at 15–16px. Don't leave a giant 18px font in a compact table.
- **Do not** use padding to hide a data problem (too many rows). Aggregate or filter instead — see `SKILL.md` → Table Length.

## Counts as

One Small Color treatment for a padding/font-size pass.
