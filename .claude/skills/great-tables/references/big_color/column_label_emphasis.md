# Big Color — Column Label Emphasis

Apply a strong background fill (and/or heavier weight, larger size, transformed case) to the column-label row so that the header anchors the eye and defines the table's shape at first glance.

## When to use

- The table has **spanners** or many columns and the reader needs the header to structure everything below.
- You want a "branded" or editorial look where the header row is a clear band across the top.
- The body of the table is intentionally quiet (no fills, no gradients) and needs a top anchor.
- Structural clarity in the header is more important than the individual cells below.

If you only want a *subtle* header tint for polish, use Small Color's `heading_tint.md` instead — that's the quiet-tier version of this technique.

## Recipe

```python
from great_tables import GT

gt = (
    GT(df)
    .tab_options(
        column_labels_background_color="#1f3b57",       # dark, saturated band
        column_labels_font_weight="bold",
        column_labels_text_transform="uppercase",       # optional editorial touch
        column_labels_border_bottom_color="#1f3b57",
    )
)
```

For a single-column emphasis (highlight just one column's header, e.g. the "answer" column):

```python
from great_tables import style, loc

gt = gt.tab_style(
    style=[style.fill(color="#1f3b57"), style.text(color="#ffffff", weight="bold")],
    locations=loc.column_labels(columns="focus_col"),
)
```

## Rules

- **Dark fill + light text**, or **light fill + dark bold text** — pick one direction and stay with it. Do not do dark-on-dark or light-on-light.
- **The header emphasis must match or exceed spanner emphasis.** If you have spanners and you loud-fill the column labels, the spanners need at least the same visual weight (bolder, matching fill, or a slightly darker shade). See `SKILL.md` → Spanner Labels.
- **One strong header treatment per table.** Don't also loud-color the row-group labels, source note, and stub — the header alone should own the "structural loud" slot.
- **Stub column labels are part of the header.** If you fill the header, either include the stubhead in the same fill or explicitly leave it blank; a mismatched stubhead cell reads as a bug.

## Counts as

One Big Color treatment. If you *also* fill spanner cells to match, that's still one treatment (they're the same structural band).
