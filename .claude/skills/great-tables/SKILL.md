---
name: great-tables
description: Use when the user's request involves building any table with `great_tables`, `gt.GT`, `gtsave`, or turning tabular data (CSV, DataFrame, spreadsheet) into a rendered PNG. Drives every table through one deterministic 7-step flowchart — understand data, organize columns, Big Color (≤2 colored measures), heading band, Small-Color checklist, titles/annotations, render+verify — so the same input characteristics always produce the same publication-ready design. Provides the full API reference (`references/api.md`), the color source-of-truth (`references/palettes.md` — Dark Academia solids, washed tints, neutrals, sequential/diverging), the fixed Small-Color polish checklist (`references/small_color.md`), per-data-shape Big-Color recipes (`references/big_color/`), and archetype examples (`assets/examples/`). The mandatory renderer is `gt.gtsave("table.png")`. Invoke before reading the data or writing any Python — the flowchart shapes the whole script.
---

# Great Tables Skill

Build publication-ready display tables in Python with `great_tables`. This skill is
a **flowchart, not a menu**: for every part of a table there is one deterministic
rule (or one explicit, data-driven branch), so the same input characteristics
always produce the same visual result. Every table reads as one product.

## Rule 0 — the user's prompt overrides everything

Every rule below is a **default**. Any explicit instruction in the user's prompt
wins (a requested font, a column's format, "bold the totals," "show all rows"). The
flowchart decides what to do *in the absence of* an instruction; it never overrides
one. When a user instruction conflicts with a default, follow the user and drop the
conflicting default silently — do not fight it or add it back later.

## The 7-step flowchart

```
1. UNDERSTAND THE DATA   grain? identifiers? measures? categories? units? quality?
                         validate request vs data (blank table if unanswerable)
2. ORGANIZE COLUMNS      show/hide · limit rows · stub (default) · groups (gated)
                         spanners (column groups) · name the hero column
3. BIG COLOR             ≤ 2 colored MEASURES (the hero if only 1); encoding by
                         data shape; gradients use sequential/diverging, everything
                         else uses Dark Academia solids
4. HEADING BAND          any Big Color? → LIGHT band.  none? → DARK saturated band
5. SMALL COLOR           fixed checklist: borders · dividers · striping · stub tint ·
                         fmt_* per column · grey-budget rule
6. TITLES & ANNOTATIONS  title + subtitle (both required) · caption (≥5 rows) +
                         source (when known), stacked footer notes
7. RENDER & VERIFY       gt.gtsave("table.png") · read it back · audit every rule
```

The order is fixed: color intent (Step 3) is decided before the quiet polish
(Step 5), and the band (Step 4) can only be decided once Big Color is known.

### Loading map — what to read, and when

Keep the activation body lean; pull the detail in at the step that needs it.

| At step | If… | Load |
|---|---|---|
| any | unsure of a method's exact signature/args/defaults | `references/api.md` |
| 3 | a measure needs an encoding | `references/palettes.md` **and** the one `references/big_color/<shape>.md` matching the data shape |
| 4 | choosing the band hue | rule is below; hexes from `references/palettes.md` |
| 5 | applying polish | `references/small_color.md` |
| 2 / 5 | the data matches an archetype (financial, time-series, heatmap, ranking, summary, scientific) | `assets/examples/<archetype>/` |
| any (scripted variant) | writing hexes / the frame | `import` from `scripts/gt_consistency.py` (see Fast path) |

## Global constants (true for every table)

Set once, never vary unless Rule 0 fires.

| Constant | Value |
|---|---|
| **Frame** | Boxed: an enclosing light border on all four sides + a margin around the whole table (never flat/edge-to-edge). Margin = `gtsave(expand=…)` (raise from the 5px default to ~15–20). Border = `tab_options(table_border_top/bottom/left/right_color/width)`. Rounded corners preferred (`opt_stylize` is an accepted mechanism); a square light border is acceptable — the enclosing border + margin is the non-negotiable. |
| **Header alignment** | Title + subtitle centered (`heading_align="center"`, the default). |
| **Font family** | great-tables default. Do **not** set `table_font_names` unless the user asks. |
| **Font size** | Default; shrink as little as possible, only when forced. |

**Font-size fit rule.** When a table is too big to render cleanly, in this order:
(1) give it room — raise `gtsave(vwidth=…, vheight=…)`; (2) keep it crisp — raise
`gtsave(zoom=…)` (default `2.0`); (3) **only then** reduce font size, by the
smallest amount that restores clarity. Relative scale when sizes are set:
title > subtitle > body > source/caption.

## Step 1 — Understand the data

Read a sample (`df.shape`, `df.dtypes`, `df.head`, `df.describe()`, `df.isnull().sum()`)
and establish: **what a row is**, the grain, key identifiers, the measures, the
categories, units/scale, ranges, and data quality (nulls, outliers). Watch scale
traps: is `rate` 0.05 (decimal) or 5.0 (percent)? is `revenue` dollars or thousands?

**Validate the request against the data.** If the data cannot answer the request,
stop, tell the user what is missing, write a minimal `table.py` that emits a blank
table, and save a blank `table.png`. **Never fabricate data.**

## Step 2 — Organize columns

1. **Show / hide.** Target **4–8** visible columns (max 10–12). Hide IDs, internals,
   intermediate calculations.
2. **Limit rows.** Target **5–15**. For large data: top-N, aggregate, or a meaningful
   subset. Every row must earn its place.
3. **Stub (`rowname_col`) — the default.** If a column holds row identifiers
   (name/date/ID), make it the stub. Add `tab_stubhead(label=…)` unless self-evident.
4. **Groups (`groupname_col`) — additive, gated.** Add groups **only if** data
   volume/goal warrants it **and** it doesn't conflict with the request. **When
   unsure, do not add groups.** Stub + groups may coexist.
5. **Spanners (`tab_spanner`).** Give logically related columns (facets of one
   measure, a period, a category) a spanner. These boundaries drive Step 5's dividers.
6. **Name the hero.** Which column(s) carry the story? This drives Big-Color
   targeting (Step 3) and, if the hero isn't colored, bold emphasis.

## Step 3 — Big Color: at most 2 colored measures

A **measure** is a distinct quantity encoded by color; it may span **many columns**
when they are facets/repetitions of the same quantity (e.g. density across 6
year-columns is one measure). **Ceiling: at most 2 colored measures.** One measure ⇒
it's the hero and gets colored. Never a third.

**Load `references/palettes.md` plus the matching `references/big_color/<shape>.md`**,
then pick each measure's encoding by data shape:

| The measure is… | Encoding | Palette | Load |
|---|---|---|---|
| Signed (neg/pos, opposite meaning) | diverging fill, symmetric domain | `RdYlGn` (default) | `references/big_color/diverging_fill.md` |
| Ordered magnitude, ≥5 rows | sequential gradient | semantic hue | `references/big_color/column_gradient_fill.md` |
| Matrix / heatmap (facets, one scale) | one gradient shared across facets (single domain) | semantic hue | `references/big_color/column_gradient_fill.md` |
| Top-N / a few "winner" rows | full-row highlight | DA solid | `references/big_color/full_row_highlight.md` |
| Binary / categorical status | status cell fill | DA solids | `references/big_color/status_cell_fill.md` |
| A few outlier cells | bold colored number | DA solid | `references/big_color/bold_colored_number.md` |
| One text column that IS the column | full-column fill | DA solid | `references/big_color/full_column_fill.md` |

Rules:

- **Consistency within a measure:** every column shares the **same palette and the
  same domain** (one `data_color` domain across all facet columns, not per-column).
- **Two sequential measures:** give them **two distinct semantic hue families —
  never the same** (e.g. `Blues` + `Greens`, not `Blues` + `Blues`).
- **Non-gradient Big Color uses the Dark Academia solids** (hue per the DA
  selection rule in `palettes.md`).
- **No-Big-Color branch:** a pure categorical/text table with no magnitude / trend /
  signed / winner story gets **no** color fill — its anchor is the **dark heading
  band** (Step 4). This is the branch that produces classic grouped grids.
- **Hero-not-colored:** if the hero is textual and isn't a colored measure, emphasize
  it with **bold text**. Never stack bold on a filled column.

## Step 4 — Heading band (conditional)

Keyed **only off Big Color** (fills, colored text, highlighted row/column from
Step 3). The quiet washed/grey surfaces of Step 5 do **not** count here.

```
Does the table have ANY Big Color?
  ├─ YES → column-label band = LIGHT (washed-DA tint of the Big-Color hue, or grey)
  └─ NO  → column-label band = DARK saturated (Dark Academia solid, white text;
           hue per the DA selection rule → usually Navy — this band is the anchor)
```

Always keep the column-label **bottom rule** (`#CCCCCC`, 2px) regardless of band.
Spanner labels read **at least as prominent** as the column labels beneath them.

## Step 5 — Small Color (fixed, rule-gated checklist)

No free menu. **Load `references/small_color.md`** and run every item; each is gated
by a rule, and every light surface comes from the washed-DA + grey palette:

- **(a) Cell borders — always.** Light hairline (`#E8E8E8`, 1px) between body rows;
  a slightly stronger rule (`#BDBDBD`) at structural boundaries (totals, group breaks).
- **(b) Column-group dividers.** IF spanners/column groups exist → a light,
  easily-noticeable vertical divider (`#D0D0D0`) **at each group boundary only**.
- **(c) Row striping.** IF **≥10 rows** AND the body is **not** essentially fully
  filled by Big Color → `opt_row_striping()`. Skip otherwise (stripes and fills fight).
- **(d) Stub tint.** IF a stub exists → a light tint (grey by default; washed-DA tint
  when Big Color present). Subject to the grey-budget rule.
- **(e) fmt_* per column.** Match semantic type. Percent 1 decimal; currency 0 dec.
  for whole-dollar, 2 for small money; number = meaningful precision; `use_seps=True`;
  `sub_missing(missing_text="—")`. Units in labels only when the formatter doesn't convey them.
- **(f) Row-group headers.** IF the table uses `groupname_col` → style each group-label
  row: **bold weight + a light tint** (`row_group_background_color`, grey `#F0F0F0` by
  default or the washed-DA tint when Big Color present) + a `#BDBDBD` structural rule.
  Never leave group labels as bare rows; never fill them with a saturated color.
  (mechanism in `references/small_color.md`.)

**Grey-budget rule:** when several large grey areas stack and go monotonous, recolor
the **highest-priority** element (order: `stub → labels → row design`) to the
washed-DA tint of the Big-Color hue. Shift only as many elements as needed.

## Step 6 — Titles & annotations

Four elements with distinct, non-overlapping jobs. Caption and source are both
`tab_source_note` calls in the footer, emitted in this order (each renders on its own
stacked line):

| Element | Required? | Job |
|---|---|---|
| **Title** | Always | The headline naming the table |
| **Subtitle** | Always | Raw understanding of the data **+ how the table is organized** (grouping, dimensions, scope, time range, units). Must **not** merely list columns and must **not** carry the insight. |
| **Caption** | When **≥5 rows** | The **takeaway** — *exactly one sentence* on what the reader should gain. First footer line. |
| **Source** | When stated/implied | Provenance only. Footer, below the caption. |

Subtitle describes *how the table is built and what it shows*; the caption states
*what it means / why you'd read it*. Do not let the subtitle steal the caption's
insight. Either footer note may be omitted independently.

## Step 7 — Render & verify

- End with **`gt.gtsave("table.png")`**. **Never** fall back to `gt.save()` (deprecated),
  `.as_raw_html()` + a screenshot tool, PIL/Pillow, imgkit/wkhtmltoimage/weasyprint,
  Playwright/Selenium/headless-chrome, or writing `table.html`. If rendering fails,
  **stop and surface the error verbatim** — a fallback produces a fake table.
- Read the PNG back and audit against **every** rule:
  - Frame boxed with margin? Header centered? Default font? Resolution clean (raise
    `zoom`/`vwidth` before shrinking text)?
  - ≤2 colored measures, each one palette+domain consistent across its columns? Two
    sequential measures using distinct hue families?
  - Heading band correct per the Big-Color test (Step 4), hue per the DA rule?
  - Every Step-5 item applied per its gate? Light surfaces from the washed-DA+grey
    palette? Grey-budget respected? If `groupname_col` is used, are the group-label
    rows styled (bold + tint + rule) rather than bare?
  - Title + subtitle present with the right roles? Caption **iff** ≥5 rows (one
    sentence, first footer line)? Source **iff** known (below caption)?
- Fix at the **root**, re-render, re-audit until fully conformant.

## Correctness gotchas

- **`data_color` domain**: always set `domain=` to the full data range; diverging →
  **symmetric around 0** (`domain=[-40, 40]`, not `[-20, 30]`); `truncate=False`.
- **`fmt_percent` scale**: values in decimal form (0.15 = 15%); if data is 0–100, use
  `scale_values=False`.
- **Original column names** in `fmt_*`/`data_color` — not the `cols_label` display text.
- **Row indices in `loc.body()`** are 0-based display positions, not DataFrame index.
- **Method chaining**: build the whole table in one chained expression; collect row
  indices into lists rather than looping `tab_style` per row.
- **Imports**: `from great_tables import GT, md, html, style, loc`.

## Fast path

If `scripts/gt_consistency.py` is importable, prefer it over hand-writing hexes and
the frame: `from gt_consistency import PALETTE, frame, finalize`. `PALETTE` holds the
exact hexes from `palettes.md` (`PALETTE["solid"]["navy"]`, `PALETTE["washed"]["navy"]`,
`PALETTE["neutral"]["hairline"]`, …); `frame(gt)` applies the boxed border; and
`finalize(gt, "table.png")` calls `gtsave` with the right margin/zoom defaults. The
script encodes **zero decisions** — every choice still comes from the flowchart
above; it only removes the chance to fat-finger a hex or forget a `gtsave` arg. When
the import isn't present, hand-write the values from `palettes.md`.
