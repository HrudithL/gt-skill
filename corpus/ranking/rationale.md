# Ranking

## Intent
Show "the most powerful production cars in the gtcars dataset" as a
top-10 leaderboard, with the winner visually called out. The implied
audience is an enthusiast scanning a recap — they want the leader,
then the chase pack, and they want enough context (year, country,
drivetrain, price) to recognize each car without clicking through.

## Data shape
- Source: `data/gtcars.csv`
- Rows: 10 (top 10 of 47, sorted by `hp` descending)
- Key columns:
  - `rank` (int) — 1-based position in the ranking
  - `car` (str) — `mfr + " " + model`
  - `year` (int) — model year
  - `ctry_origin` (str) — country of manufacturer
  - `hp` (int) — peak horsepower (the ranking key)
  - `trq` (int, lb-ft) — peak torque
  - `drivetrain` (str) — rwd / awd / 4wd
  - `msrp` (float, USD) — manufacturer suggested retail price
- Notable nulls / outliers: none in the top 10.

## Design choices
- **Sort by `hp` desc, take top 10** — the row order IS the message; an unsorted dump erases the archetype.
- **1-based rank column** — `#` is what readers expect on a leaderboard; 0-based indices read as "row id", not as "position".
- **Compose `car` from `mfr + model`** — keeps the row scannable; two separate columns would force the eye to combine them mentally on every row.
- **Hide uninformative columns** — `trim`, `bdy_style`, `hp_rpm`, `trq_rpm`, `mpg_c`, `mpg_h`, `trsmn` are dropped. Anything that does not help rank or recognize the car is noise.
- **fmt_currency on `msrp`, no decimals** — vehicle prices are quoted in whole dollars in the trade press; cents are spurious precision.
- **`fmt_integer(use_seps=False)` on `year`** — `2,017` is wrong for a year; this is the documented escape.
- **Bold the rank column** — makes the index pop so the reader can navigate the leaderboard quickly.
- **Highlight the #1 row** with a warm pale fill plus bold on `car` and `hp` — the leader gets the visual weight. Pale (not saturated) so it does not crowd the surrounding rows.
- **Numeric right-align, text left-align** — explicit even though it matches the default; survives column-type refactors.
- **Source note** — credits the dataset so the reader can find the same data.

## What was deliberately omitted
- **Logos / images per row** — would require off-disk assets; out of scope and would slow rendering.
- **Bar-in-cell for HP** — the rank ordering already does the comparison work; a second visual channel competes with the leader highlight.
- **A "% gap to leader" column** — interesting but secondary; would add a fourth numeric column for marginal information.
- **Pagination controls** — top-10 fits on one screen; no need to expose the rest of the 47-row dataset here.

## Anti-patterns avoided
- **Unsorted dump of all rows** → **sorted top-10**: the ranking archetype is the sort; without it there is no ranking.
- **Every column shown** → **eight chosen columns**: relevance is curated, not assumed.
- **No `#` column** → **explicit 1-based rank**: leaderboards need their position label.
- **No emphasis on the leader** → **highlighted #1 row**: the eye should land on the winner first.
- **`year` with thousands separator** → **`fmt_integer(use_seps=False)`**: `2,017` is wrong.
- **`mfr` and `model` shown as two columns** → **combined `car` column**: one identity per row.
