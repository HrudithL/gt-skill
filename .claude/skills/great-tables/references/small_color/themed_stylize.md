# Small Color — Themed Baseline (`opt_stylize`)

Use `.opt_stylize(style=N, color=C)` as a fast, cohesive baseline that ships a
colored column-label band, striped body, and matching hairline dividers in one call.
Then layer one or two more Small Color moves on top for a finished look.

## When to use

- The table is a **categorical/textual grid** (a top-N list, a small comparison
  table) where you have no natural numeric column to feed `data_color` — the sort
  of table that otherwise ends up as flat black text on white.
- You want a professional look without hand-tuning six different chrome colors.
- The data itself doesn't have one obviously "hero" column that would carry a Big
  Color treatment on its own.

If the table already commits to a strong Big Color story (a diverging heatmap, a
full-column fill, per-cell status pills), skip `opt_stylize` — it will double up on
chrome color and fight the data-driven fill.

## Recipe

```python
from great_tables import GT

gt = (
    GT(df, groupname_col="Region")
    .tab_header(title="...", subtitle="...")
    .fmt_currency(columns="price", currency="USD", decimals=0)
    .opt_stylize(style=2, color="blue")           # colored header + stripes + dividers
    .tab_options(                                  # then finish the row-group headers
        row_group_background_color="#eef3fa",     # light tint of the theme color
        row_group_font_weight="bold",
    )
)
```

Available styles (all combine well with the six colors):

| `style=` | What it ships |
|---|---|
| 1 | Colored heading background, clean body |
| 2 | Colored column labels, striped rows, light column dividers *(good default)* |
| 3 | Heavy borders, bold structure |
| 4 | Minimal, thin lines |
| 5 | Colored row groups |
| 6 | Full color, all elements styled |

Colors: `"blue"`, `"cyan"`, `"pink"`, `"green"`, `"red"`, `"gray"`.

## Rules

- **Do not stack `opt_stylize` with `opt_row_striping()` or `heading_tint.md`** —
  the theme already includes both, and layering them produces darker-than-intended
  stripes or clashing header tints.
- **Layer `row_group_emphasis.md` on top** whenever `groupname_col=` is set. The
  themes do *not* fully style the group-header row on their own; a bare "Italy" /
  "US" label sitting between striped bodies is the exact "boring" failure mode we
  want to avoid.
- **Match the theme color to any Big Color palette in the same table.** A blue
  `opt_stylize` next to a `Reds` `data_color` fights itself. Pick one color
  family and stay in it.
- **You can still override individual chrome pieces** with `tab_options(...)` after
  the `opt_stylize` call — later calls win. Use this to soften a header that's
  darker than you want, or to swap the stripe color for a warmer near-white.

## Counts as

One Small Color treatment for the whole theme (colored header + stripes + dividers
that come with `opt_stylize`). Add one or two more Small Color moves (typically
`row_group_emphasis.md`, `compact_padding.md`, or `font_family_choice.md`) to reach
the 2–3 required.
