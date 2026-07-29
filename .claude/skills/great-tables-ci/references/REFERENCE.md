# REFERENCE.md — the router: open the right file before each decision

Execute this checklist top to bottom against your data. For every matching
row, open the file it names and **copy the exact value into your code** —
never retype a palette, hex, or domain from memory.

Paths are relative to this directory (`references/`), except worked examples,
which live in `assets/` at the skill root — a **sibling** of `references/` —
so those paths carry a leading `../` (e.g. `../assets/examples/…`). There is
no `references/assets/`.

---

## 0. Unsure of any method signature/args/defaults — at any step

Open **`api.md`** and copy the exact signature. Mechanical only — every
design decision stays in SKILL.md and the files below.

## 0b. This is the CI-checked variant — it ships `scripts/`

Open **`scripts.md`** for this variant's tooling: when/how to run
**`python gt_check.py table.py`** against your produced `table.py`, how to
read its rule-id output and iterate to `PASS`, the required top-level **`gt`
variable**, and the **`gt_consistency.py` helpers** (`heatmap` / `band` /
`stripe` / `stub_tint`, plus `frame` / `finalize` and `PALETTE`). Mechanical
only — the helpers execute a decision you already made.

## 1. EVERY table — unconditional (Steps 1, 2, 4 & 5)

- **`data.md`** — Step 1, before organizing columns: reach ONE
  correctly-typed DataFrame (strip currency/percent strings, coerce
  `object`-dtype numerics, fix a bad header row, cast SQL `Decimal`s,
  standardize missing values). Skip this and `fmt_*` / `data_color` break
  silently.
- **`small_color.md` → "Deterministic triggers" section — before writing
  `GT(...)` (Step 2).** The stub trigger (PP-13 → `rowname_col=`), grouping
  trigger (PP-1 → `groupname_col=`), and ambiguous-measure rule
  (F-canonical-metric, PP-18) decide **constructor arguments** — resolve
  them at Step 2, not Step 5. Read only that section now; the polish
  checklist (rest of the file) is read later at Step 5.
- **`palettes.md`** — source of truth for every hex: Dark Academia solids,
  their washed tints, the neutral greys, and the sequential/diverging
  palette *names*. Open before writing any color.
- **`small_color.md`** — the fixed Small-Color polish checklist (cell
  borders, column dividers, the row-striping gate, stub tint, `fmt_*` per
  semantic type, the grey-budget rule, row-group emphasis) plus **all
  neutral hexes** and the **frame border color/width + `gtsave`
  margin/zoom values**. Open before Step 5 and before setting the frame; run
  every gated item.

## 2. A numeric magnitude / trend / signed measure is present (Step 3)

**Before writing `data_color(...)`**, find your data shape below, open the
**one** file it names, and copy its palette + domain rule. Also read
`palettes.md` §3 for the palette *name* and the diverging-symmetric-domain
rule.

| Your data shape | Open |
|---|---|
| **Signed** measure (neg/pos, opposite meaning) | `big_color/diverging_fill.md` |
| **Ordered magnitude**, ≥5 rows | `big_color/column_gradient_fill.md` |
| **Matrix / heatmap** (facets sharing one scale) | `big_color/column_gradient_fill.md` |
| **Top-N** "winner" rows | `big_color/full_row_highlight.md` |
| **Binary / categorical status** | `big_color/status_cell_fill.md` |
| A few **outlier cells** | `big_color/bold_colored_number.md` |
| **One text column that IS the column** | `big_color/full_column_fill.md` |

Ceiling: **≤ 2 colored measures**. One measure ⇒ it's the hero and gets
colored. A pure categorical/text table with no magnitude/trend/signed/winner
story gets **no** fill — its anchor is the dark heading band (Step 4). (Hero
text that is not a colored measure gets **bold text**, never a second fill —
no file needed.)

## 3. Choosing the heading band (Step 4)

Open **`big_color/column_label_emphasis.md`** for the band decision itself
(dark-vs-light branch keyed off Big Color), then **`palettes.md`** for the
exact **band hex** — a washed tint of the Big-Color hue if the table has ANY
Big Color, else a **dark DA solid with white text** — and the **DA
hue-selection rule**. Keep the column-label bottom rule regardless of band
(hex in `small_color.md`).

## 4. Your data matches an archetype (Steps 2 & 5)

Open the matching worked example for a full runnable table to pattern-match
against (`../assets/examples/EXAMPLES.md` indexes them all).

| Archetype — use when… | Open |
|---|---|
| Money, prices, signed deltas, percentages | `../assets/examples/financial/` |
| Dates, trends, monthly/yearly aggregation | `../assets/examples/time_series/` |
| Color-encoded data cells | `../assets/examples/heatmap/` |
| Top-N lists, ordered results | `../assets/examples/ranking/` |
| Aggregations, totals, subtotals | `../assets/examples/summary_stats/` |
| Measurements with units, sig figs | `../assets/examples/scientific/` |
