# REFERENCE.md — the router: open the right file before each decision

SKILL.md sent you here **before you write any Python**. This is a checklist you
*execute*, not an index you skim. Run it top to bottom against **your** data; for
every row that matches, open the file it names and **copy the exact value out of that
file into your code**. Do not retype a palette, hex, or domain from memory — SKILL.md
holds none of them on purpose. Filenames live here and nowhere else, so you never have
to point past this file.

Paths below are relative to the skill's `references/` directory (this file's own
directory). The worked examples are the one exception: they live at the skill root in
`assets/` — a **sibling** of `references/`, not inside it — so every example path is
written with a leading `../` (i.e. `../assets/examples/…`, which resolves from
`references/`). There is no `references/assets/`.

---

## 0. Unsure of any method signature/args/defaults — at any step

Open **`api.md`** and copy the exact signature. Mechanical API detail only; every
design decision stays in SKILL.md and the files below.

## 1. EVERY table — unconditional (Steps 1, 2, 4 & 5)

- **`data.md`** — the data-cleaning sub-step (Step 1, **before you organize columns**):
  get to ONE correctly-typed DataFrame. Strip currency/percent strings to floats, coerce
  `object`-dtype numerics, fix a non-zero header row, cast SQL `Decimal`s, standardize
  missing values. `great_tables` formats numbers, it does not parse strings — skip this
  and `fmt_*` / `data_color` break silently.
- **`small_color.md` → "Deterministic triggers" section — BEFORE you write the
  `GT(...)` constructor (Step 2).** The stub trigger (PP-13 → `rowname_col=`), the
  grouping trigger (PP-1 → `groupname_col=`), and the ambiguous-measure rule
  (F-canonical-metric, PP-18) all decide **constructor arguments**, so resolve them when
  you organize columns (Step 2), **not** at Step 5. Read that one section now; the rest
  of `small_color.md` (the polish checklist) is read later, at Step 5 (next bullet).
- **`palettes.md`** — the single source of truth for every hex: Dark Academia solids,
  their washed light tints, the neutral greys, and the sequential/diverging palette
  *names*. Open it before you write any color at all.
- **`small_color.md`** — the fixed Small-Color polish checklist (cell borders, column
  dividers, the row-striping gate, stub tint, `fmt_*` per semantic type, row-group
  emphasis, the compact-layout padding values) plus **all neutral hexes** and the
  **frame border color/width + the `gtsave` margin/zoom values**. Open it before
  Step 5 and before you set the frame; run every gated item.

## 2. A numeric magnitude / trend / signed measure is present (Step 3)

**Before you write `data_color(...)`**, find your data shape below, open the **one**
file it names, and copy that file's palette + domain rule. Also read `palettes.md` §3
for the palette *name* and the diverging-symmetric-domain rule.

| Your data shape | Open |
|---|---|
| **Signed** measure (neg/pos, opposite meaning) | `big_color/diverging_fill.md` |
| **Ordered magnitude**, ≥5 rows | `big_color/column_gradient_fill.md` |
| **Matrix / heatmap** (facets sharing one scale) | `big_color/column_gradient_fill.md` |
| **Top-N** "winner" rows | `big_color/full_row_highlight.md` |
| **Binary / categorical status** | `big_color/status_cell_fill.md` |
| A few **outlier cells** | `big_color/bold_colored_number.md` |
| **One text column that IS the column** | `big_color/full_column_fill.md` |

Which measures earn fill: one qualifying measure ⇒ it's the hero and gets colored.
When several qualify, `big_color/column_gradient_fill.md`'s priority ladder picks
which earn a full heatmap fill first and which instead step down to bold text/text
color (the color-restraint principle, `small_color.md`). A pure categorical/text
table with no magnitude/trend/signed/winner story gets **no** fill — its anchor is
the branding heading band (Step 4), which every table gets regardless. (A measure
the request names that does not earn a fill renders **fully plain** — no fill, no
bold — see `small_color.md`.)

## 2b. Column placement for the primary heatmapped measure (Step 2)

Once you know which measure will carry the table's primary heatmap fill, keep it at
an **outer edge** — immediately after the stub, or as the last column(s) — never
buried in the middle. Columns providing context/inputs a reader needs first precede
columns reporting a derived/resulting outcome, so an outcome-type measure naturally
lands at the right edge, while a measure that IS the subject's defining fact lands
at the left edge (right after the stub). Use **`api.md`**'s `cols_move` /
`cols_move_to_start` / `cols_move_to_end` entries as the mechanism.

## 3. Choosing the heading band (Step 4)

Open **`palettes.md`**'s branding tier for the fixed **band hex**, weight, and label
text color — the same on every table, unconditionally, regardless of whether (or
what) the body heatmaps. Keep the column-label bottom rule regardless of band (hex
in `small_color.md`). `big_color/column_label_emphasis.md` has the mechanics.

## 4. Titles & annotations (Step 6)

**Before writing the footer**, open **`small_color.md` → "(f) Titles &
annotations"**: the footer is **two separate `tab_source_note(...)` calls**
(an analytical caption + a source/provenance note), not one combined line —
and a named-but-uncolored measure stays fully plain text, no
`style.text(weight="bold")`, no fill.

## 5. Your data matches an archetype (Steps 2 & 5)

Open the matching worked example for a full runnable table to pattern-match against
(`../assets/examples/EXAMPLES.md` indexes them all).

| Archetype — use when… | Open |
|---|---|
| Money, prices, signed deltas, percentages | `../assets/examples/financial/` |
| Dates, trends, monthly/yearly aggregation | `../assets/examples/time_series/` |
| Color-encoded data cells | `../assets/examples/heatmap/` |
| Top-N lists, ordered results | `../assets/examples/ranking/` |
| Aggregations, totals, subtotals | `../assets/examples/summary_stats/` |
| Measurements with units, sig figs | `../assets/examples/scientific/` |
