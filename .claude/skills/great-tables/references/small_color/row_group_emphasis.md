# Small Color — Row Group Emphasis

Give `groupname_col` header rows a light background fill **and** bold weight so each
section reads as a real break in the table, not as a stray body row.

## When to use

- **Always, whenever the table uses `groupname_col=`.** An unstyled group label sits
  in the flow of body rows and the reader loses the section boundary. This is one of
  the most common reasons a table with real structure still reads as flat.
- The table has 2+ groups and the reader needs to see "everything under Italy" as a
  block before scanning individual rows.

If the table has no `groupname_col`, this technique does not apply — skip it.

## Recipe

```python
from great_tables import GT

gt = (
    GT(df, groupname_col="Region")
    .tab_options(
        row_group_background_color="#f0f0f2",     # near-white grey, or a very light
                                                  # tint of the table's Big Color palette
        row_group_font_weight="bold",             # non-negotiable — the label is a
                                                  # heading, treat it like one
        row_group_border_top_color="#c7ccd3",     # optional: subtle rule above group
        row_group_border_bottom_color="#c7ccd3",  # optional: subtle rule below label
        row_group_padding="6px",                  # a touch more air than a body row
    )
)
```

If the table already carries a brand color (e.g. from `column_labels_background_color`
or a `data_color` palette), it's fine — and often better — to use a very light tint
from the same hue family for `row_group_background_color`:

- Blue-themed table → `"#eef3fa"` group tint
- Green-themed table → `"#eef7ee"` group tint
- Warm/red-themed table → `"#faeeee"` group tint

## Rules

- **Bold font weight is required.** Fill alone reads as noise; bold alone reads as
  a bulleted body row. The pair reads as a section heading.
- **Light fill only.** The group header should feel like a divider, not a data row —
  never fill it with a saturated color. If you need editorial weight, use
  `references/big_color/column_label_emphasis.md` on the *column labels* instead,
  not on group headers.
- **Consistent color across all groups.** Every group in the table gets the same
  fill — do not shade "important" groups differently. That would misuse structural
  chrome as a data channel.
- **Match related chrome.** If you tint the header (`heading_tint.md`) *and* the
  group headers, use the same or a closely related shade so the two structural bands
  read as one system, not two competing tints.

## Counts as

One Small Color treatment.
