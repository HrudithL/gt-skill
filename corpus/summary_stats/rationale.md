# Summary stats

## Intent
Give a pizza-shop manager the one-screen monthly review: how much each
category sells, broken out by size, with subtotals per category and a
grand total at the bottom so the headline revenue number is on the
page. The reader is operational, not analytical — they want the
numbers, not the data.

## Data shape
- Source: `data/pizzaplace.csv` (49,574 individual orders)
- Rows: 14 visible (one per (category, size) combination present in the data) + 4 group banners + 1 grand summary
- Key columns:
  - `type` (str) — pizza category; used as the group banner via `groupname_col`
  - `size` (ordered category) — S < M < L < XL < XXL; the row label
  - `orders` (int) — count of transactions
  - `revenue` (float, USD) — sum of price
  - `avg_price` (float, USD) — mean price per pizza
- Notable nulls / outliers: not every category sells every size (XL/XXL only exist for Classic). Those cells simply do not exist as rows, which is cleaner than rendering empty cells.

## Design choices
- **Aggregate to (category, size)** — 49,574 → 14 rows. The archetype is "summary"; serving raw transactions defeats it.
- **`rowname_col="size"` + `groupname_col="type"`** — gives great_tables the structural hint to render group banners and indented size labels, which is the gt-native way to express a two-level row layout.
- **Ordered Categorical on `size`** — `S, M, L, XL, XXL` is the natural progression; without `pd.Categorical(..., ordered=True)` the rows would land alphabetic (`L, M, S, XL, XXL`).
- **Capitalize category labels** — `"Classic"` reads as a noun; `"classic"` reads as an adjective and looks like a typo.
- **`fmt_currency` on revenue and avg price** — the table is for managers; cents matter for receipts.
- **`fmt_integer` on orders** — thousands separators on counts that range up to ~6k.
- **Grand summary row via callable returning `pd.Series`** — `pl.col(...)` expressions only work on polars-backed tables; the callable form is the documented escape for pandas. `avg_price` is intentionally omitted from the summary — a mean-of-means is not meaningful — and renders as the empty `missing_text`.
- **Bold the group banners via `loc.row_groups()`** — visually punctuates the four categories without competing with the body cells.
- **Source note** — credits the dataset.

## What was deliberately omitted
- **A "% of total" column** — would force the reader to read three columns per row instead of two; the grand total at the bottom is enough context to compute the share mentally.
- **Min / max price per group** — collapses category × size to a single price-per-pizza, so range is already implied; adding it would dilute the revenue story.
- **A bar-in-cell on revenue** — visual ranking is not the goal here; an accountant wants the number, not the bar.
- **Time-of-day or day-of-week breakouts** — out of scope for a category-by-size summary; would belong in a separate table.

## Anti-patterns avoided
- **Raw transactions** → **grouped aggregates with grand total**: the archetype is to summarize; not summarizing is the dominant failure.
- **Alphabetic size order** → **explicit ordered Categorical**: `S, M, L, XL, XXL` is the only order a reader will accept.
- **Lowercase category labels** → **capitalized**: titles are nouns.
- **No grand total** → **`grand_summary_rows`**: the headline number must be on the page.
- **`fmt_number` on revenue** → **`fmt_currency`**: money needs a `$`.
- **No row grouping** → **`groupname_col="type"`**: two-level row structure is the gt-native way to express category × size.
