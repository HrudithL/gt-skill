# Big Color — Attention-Grabbing Techniques

Big Color techniques encode information visually and pull the reader's eye to the cells or columns that carry the story. Each file in this folder describes **one technique**: what it does, when to reach for it, and the exact code to apply it.

Load only the file(s) for the technique(s) you plan to use. Do not load the whole folder speculatively.

## When to use Big Color

You have already done the data analysis and identified **what matters most in this table** — the column, row, or cell that answers "why is the reader looking at this?". Big Color makes that answer unmissable.

Budget: **1–3 Big Color treatments per table maximum.** More than that and nothing stands out; the table becomes a stained-glass window.

## Technique index

| File | Technique | Reach for it when... |
|---|---|---|
| `full_column_fill.md` | Solid background fill on one or more entire columns | One column is the story and the values are categorical or unordered (a gradient would misleadingly imply order) |
| `column_gradient_fill.md` | `data_color` gradient across an ordered numeric column | The column is an ordered measure with ≥5 rows and relative magnitude is the point |
| `diverging_fill.md` | Red↔neutral↔green (or similar) fill for signed values | The column has both negatives and positives and the sign carries opposite meaning (P&L, YoY, variance) |
| `bold_colored_number.md` | Bold + colored text on individual outlier cells | A small number of cells (extremes, threshold breaches) need to jump off the page |
| `full_row_highlight.md` | Fill + bold on one or a few entire rows | Rank order or a small set of "winner" rows is the message (top-3, current period, etc.) |
| `column_label_emphasis.md` | Strong fill/weight on the column-label row | The header row itself needs to anchor the eye, usually to introduce spanners or brand the table |
| `status_cell_fill.md` | Per-cell fill on a small categorical status column | A column encodes 2–4 discrete states (pass/fail, on/off, tier) and each state needs an instant read |

## Selection workflow

1. Look at the table you're about to build and identify the **one thing** (or two) that matters most.
2. Match it to a row in the table above.
3. Load that single file and follow the recipe.
4. If nothing in the table warrants a Big Color treatment, skip Big Color entirely and go straight to Small Color for polish.
