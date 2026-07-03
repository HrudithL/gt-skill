# Small Color — Subtle Borders

Tune the borders (body horizontal lines, header underline, source-note separator) so the table's grid supports the eye without becoming a spreadsheet.

## When to use

- The default borders feel too heavy (dark, thick) and the table looks like a raw dump.
- The table feels *floaty* — rows have no visual guide connecting them.
- You want a subtle rule under the header or above the totals row without a full-fill treatment.

## Recipe

```python
from great_tables import GT

gt = (
    GT(df)
    .tab_options(
        # Body horizontal lines — thin, muted
        table_body_hlines_style="solid",
        table_body_hlines_color="#e5e7eb",
        table_body_hlines_width="1px",
        # Header underline
        column_labels_border_bottom_color="#c7ccd3",
        # Source note separator
        source_notes_font_size="11px",
    )
)
```

To emphasize a totals row with only a top border (no fill), pair with:

```python
from great_tables import style, loc

gt = gt.tab_style(
    style=style.borders(sides="top", color="#4a4a4a", weight="1.5px"),
    locations=loc.body(rows=[totals_row_index]),
)
```

## Rules

- **Low-saturation, not necessarily grey.** Neutral greys (`#c7ccd3`–`#e5e7eb`) are the safe default. A muted tint of a color already used elsewhere in the table (e.g. a light blue border on a blue-themed table, matching what `opt_stylize(color="blue")` produces) is also fine — it makes the chrome feel intentional rather than applied on top. Avoid mid-saturation or brand-primary borders; those are Big Color territory.
- **1px, occasionally 1.5px.** Anything thicker than 2px is Big Color territory and should be justified by structure (e.g., separating body from totals).
- **Prefer removing borders over adding them** if the table already has enough structure — e.g., set `table_body_hlines_style="none"` for tables with clear row striping.
- **Consistency**: if you set body hlines to a specific grey, use the same grey (or one shade darker) for the header underline. Do not mix unrelated grey values.

## Counts as

One Small Color treatment for the whole border pass (body lines + header underline + optional totals rule).
