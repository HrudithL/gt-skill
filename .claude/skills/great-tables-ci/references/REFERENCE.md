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
  semantic type, row-group emphasis, the compact-layout padding values) plus
  **all neutral hexes** and the **frame border color/width + `gtsave`
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
| **Top-N** "winner" rows *highlighted within a larger table* | `big_color/full_row_highlight.md` |
| **Binary / categorical status** | `big_color/status_cell_fill.md` |
| A few **outlier cells** | `big_color/bold_colored_number.md` |
| **One text column that IS the column** | `big_color/full_column_fill.md` |

**"Top-N" means highlighting a small subset of winner rows inside a table that also
shows other, non-winning rows** — not "the request already filtered the data down to
only the top N" (`nlargest(10, ...)`, "the 10 most expensive X"). Once the displayed
table's whole row set already IS the winners, there's no larger context left to stand
out from (every row would get the fill, blowing past that file's own `≤30%` cap), and
the ranking measure itself still needs its magnitude shown row-to-row — that's **Ordered
magnitude** above, regardless of the request's own "top N" wording.

Which measures earn fill: one qualifying measure ⇒ it's the hero and gets
colored. When several qualify, `big_color/column_gradient_fill.md`'s priority
ladder picks which measures are ranked highest (deterministic); how many of
them actually earn a full fill is a judgment call weighing the request's core
ask against table noise — there is no numeric cap. A pure categorical/text
table with no magnitude/trend/signed/winner story gets **no** fill — its
anchor is the branding heading band (Step 4), which every table gets
regardless. A measure that qualifies but doesn't make the cut, or that turns
out to be a near-redundant restatement of another colored measure, renders
**fully plain at the measure level** — no whole-column fill, no whole-column
bold, no whole-column text-color treatment — see `small_color.md`. (This is a
whole-measure rule: it does not forbid the few-outlier-CELLS technique in
`big_color/bold_colored_number.md` above, which bolds a handful of individual
cells within an otherwise-plain column.)

## 2b. Column placement for the primary heatmapped measure (Step 2)

Once you know which measure will carry the table's primary heatmap fill,
prefer an **outer edge** for it — immediately after the stub, or as the last
column(s). This is a strong preference, not an absolute: a table with
multiple qualifying measures may reasonably place one of them a column or two
inside the edge if that better serves the table's narrative order. Don't
force a reordering that fights the data's natural grouping just to satisfy
this rule. Columns providing context/inputs a reader needs first precede
columns reporting a derived/resulting outcome, so an outcome-type measure
naturally lands at the right edge, while a measure that IS the subject's
defining fact lands at the left edge (right after the stub) — decide which
edge by this narrative sequencing. Use **`api.md`**'s `cols_move` /
`cols_move_to_start` / `cols_move_to_end` entries as the mechanism.

## 3. Choosing the heading band (Step 4)

Open **`palettes.md`**'s branding tier for the fixed **band hex**, weight, and
label text color — the same on every table, unconditionally, regardless of
whether (or what) the body heatmaps. Keep the column-label bottom rule
regardless of band (hex in `small_color.md`). `big_color/column_label_emphasis.md`
has the mechanics.

## 4. Titles & annotations (Step 6)

**Before writing the footer**, open **`small_color.md` → "(f) Titles &
annotations"**: the footer is **two separate `tab_source_note(...)` calls**
(an analytical caption + a source/provenance note), not one combined line —
and a named-but-uncolored measure stays fully plain text at the measure level, no
whole-column `style.text(weight="bold")`, no whole-column fill (the few-outlier-cells
exception is in §2 above / `big_color/bold_colored_number.md`).

## 5. Your data matches an archetype (Steps 2 & 5)

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
