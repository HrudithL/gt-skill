# Big Color — Full Row Highlight

Background fill (optionally bold text) on entire "winner" rows to dominate visual hierarchy.

## When to use

- Ranking/leaderboard where the top 1–3 rows are the message, WITHIN a larger table (top-N-among-many).
- A single "current"/"featured" row (this quarter, this user, selected item) must be found instantly.
- **The table itself has fewer than 5 rows total** (small by nature, or filtered down that far) — too few for `column_gradient_fill.md`'s gradient to read as anything but random pastel (its own `≥5 rows` gate's documented fallback). Filling every row is correct here, not a ≤30% violation — that guidance is about carving a subset out of a larger table.
- Otherwise: highlighted rows are **≤30% of body rows** — any more and the highlight becomes the norm.

If you're trying to encode magnitude across all rows, use `column_gradient_fill.md`. If the emphasis is per-cell (only certain values in a column), use `bold_colored_number.md`.

## Recipe

```python
from great_tables import GT, style, loc

top_rows = df.nsmallest(3, "rank").index.tolist()   # rank=1 is best

gt = (
    GT(df, rowname_col="rank")
    .tab_style(
        style=[style.fill(color="#9A7B33"),          # Dark Academia solid (Ochre = premium/awards)
               style.text(color="#ffffff", weight="bold")],   # white text on the solid
        locations=loc.body(rows=top_rows),
    )
)
```

## Rules

- **Fill spans all columns** — omit `columns=` in `loc.body()` so the whole row gets the fill.
- **Solid hex + white text** (non-gradient Big Color, never a pale tint — that's Small-Color). Ochre `#9A7B33` = featured/winner/premium; Oxblood `#5C2E2E` = bad (violation, losing entry); Navy `#22384F` = neutral default. Pick hue per DA hue-selection rule in `references/palettes.md` §1.
- **Do not** stack on a column gradient or diverging fill — the treatments compete. Pick one.
- **≤30% of rows, unless the table has fewer than 5 rows total** (see "When to use" above). Above that row count, more than ≤30% means recoloring the table, not highlighting it.

## Counts as

One Big Color treatment.
