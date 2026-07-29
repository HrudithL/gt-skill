# Big Color — Full Row Highlight

Background fill (optionally bold text) on entire "winner" rows to dominate visual hierarchy.

## When to use

- Ranking/leaderboard where the top 1–3 rows are the message (top-N).
- A single "current"/"featured" row (this quarter, this user, selected item) must be found instantly.
- Highlighted rows are **≤30% of body rows** — any more and the highlight becomes the norm.

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

## Counts as

One Big Color treatment.
