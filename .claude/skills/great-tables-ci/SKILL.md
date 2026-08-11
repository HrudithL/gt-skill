---
name: great-tables-ci
description: Use when building a table with `great_tables`, `gt.GT`, or `gtsave`, or turning tabular data (CSV, DataFrame, spreadsheet) into a rendered PNG. Deterministic 7-step flowchart — understand data, organize columns, Big Color (≤2 colored measures), heading band, Small-Color checklist, titles/annotations, render+verify. Read `references/REFERENCE.md` before writing any Python; it routes every color/band/polish/API decision to the exact value that pins it. The mandatory renderer is `gt.gtsave("table.png")`. Invoke before reading the data or writing any Python. CI-checked variant.
---

# Great Tables Skill

Build publication-ready display tables in Python with `great_tables`. This is a
**flowchart, not a menu** — one deterministic rule per decision, so the **same
input always produces the same output**, and **every table reads as one product**.

## Read this before you write ANY Python

Before writing **any** Python, read **`references/REFERENCE.md`** — the doorway
that routes every decision below to the exact reference file holding its pinned
value (palette, hex, domain rule, polish checklist, signature, worked example).
**Do not skip it.** SKILL.md holds the procedure and decision points only; it
carries **zero** pinned values.

## Rule 0 — the user's prompt overrides everything

Every rule below is a **default**; an explicit instruction in the user's prompt
wins (a requested font, a column's format, "bold the totals," "show all rows").
The flowchart decides only in the *absence* of an instruction — it never
overrides one. On conflict, follow the user and silently drop the conflicting
default.

## The 7-step flowchart

```
1. UNDERSTAND THE DATA   grain? identifiers? measures? categories? units? quality?
                         clean → ONE correctly-typed DataFrame (references/data.md)
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

## Step 7 is a full manual audit — `gt_check.py` does not cover these items

Before you consider the table done, re-check every item below by eye against the
rendered PNG. `gt_check.py` mechanically enforces the ≤2-colored-measure ceiling
and the frame; it does **not** currently check hairlines, column dividers, stub
tint, or the footer's two-call convention (an earlier version of this checklist
claimed it did — that was wrong, and mechanical checks for these are a real but
separate follow-up, not something to assume exists today):

- **Body-row hairlines** — a separate `great_tables` option family from the outer
  frame; `great_tables` renders a hairline by default, so the actual thing to
  verify is that its color is pinned to the house/washed-neutral tone (see
  `small_color.md` (a)), not left at the raw library gray.
- **Column dividers** at each spanner seam, when 2+ column groups exist.
- **The footer's two-call convention** (`small_color.md` (f)): an analytical
  caption AND a separate source note, not one combined line, on any table with
  ≥5 rows.
- **Hero-uncolored measures must be bold, not bare** — this one needs the
  prompt (which measure is the request's actual topic), so no mechanical check
  could verify it even if one existed. If the request names 2+ measures and you
  colored both because both fit under the ceiling, that's still wrong — re-read
  Step 3's ceiling, color the one that's the request's actual topic, and
  `style.text(weight="bold")` the other.

Small polish matters as much as Big Color — audit all of these by eye every time,
don't rely on a checker that doesn't exist yet to catch them for you.

## Withhold values, forbid guessing — open the file the action needs

SKILL.md names *what* to decide; the *value* lives only in the reference file
`REFERENCE.md` routes you to. Copy it — never guess a palette, hex, domain, or
signature from memory.

- **Before you organize columns** (right after Step 1): open `data.md` to reach
  **one clean, correctly-typed DataFrame** — strip currency/percent strings to
  floats, coerce `object`-dtype numeric columns, fix a non-zero header row, cast
  SQL `Decimal`s. `great_tables` *formats* numbers, it does not parse strings; a
  `"$1,200"` value silently breaks `fmt_*`/`data_color`.
- **Before you write any `data_color(...)`** (Step 3): the palette name, hexes,
  and domain live only in the `big_color/<shape>.md` file `REFERENCE.md` names
  for your data shape (plus `palettes.md`). Copy them.
- **Before you set the heading band** (Step 4): open `palettes.md` for the exact
  band hex — washed tint if Big Color is present, dark DA solid + white text if
  not — and the hue-selection rule.
- **Before you run the Small-Color polish** (Step 5): open `small_color.md` and
  run its fixed checklist top to bottom — every neutral hex, the striping gate,
  the stub tint, the fmt-per-type rules.
- **Before you call any method you are unsure of** (any step): open `api.md` for
  the exact signature, arguments, and defaults.

If SKILL.md cannot answer it and you may not invent it, open the reference.

## Global constants (true for every table)

Set once, never vary unless Rule 0 fires. These are **named rules**; exact
numeric values live in the references.

- **Frame.** Boxed light border on all four sides + margin around the whole
  table (never flat/edge-to-edge). Border color/width and the `gtsave` margin
  value are in `references/small_color.md`. Rounded corners preferred; a square
  border is acceptable — the enclosing border + margin is the non-negotiable.
- **Header alignment.** Title + subtitle centered (the default).
- **Font family.** great-tables default. Do **not** set the font unless the
  user asks.
- **Font size.** Default; shrink as little as possible, only when forced.
- **Font-size fit rule.** When a table renders too big, in this order: (1) give
  it room — raise the `gtsave` width/height; (2) keep it crisp — raise the
  `gtsave` zoom; (3) **only then** reduce font size, by the smallest amount that
  restores clarity. The default zoom and margin value are in
  `references/small_color.md`. Relative scale: title > subtitle > body >
  source/caption.

## Correctness gotchas (named rules — the values live in the references)

- **`data_color` domain.** Always set `domain=` to cover the full data range; a
  **signed/diverging** measure's domain must be **symmetric about 0** with
  `truncate=False`. The exact rule and data-driven bound are in
  `references/big_color/diverging_fill.md`.
- **`fmt_percent` scale.** Expects values in decimal form (`0.15` renders as
  `15%`); if your data is already on a 0–100 scale, pass `scale_values=False`.
  See `api.md`.
- **Original column names** in `fmt_*`/`data_color` — not the `cols_label`
  display text.
- **Row indices in `loc.body()`** are 0-based display positions, not the
  DataFrame index.
- **Method chaining.** Build the whole table in one chained expression; collect
  row indices into lists rather than looping `tab_style` per row.
- **Renderer.** End with **`gt.gtsave("table.png")`** only. `gtsave()` renders
  through headless Chrome, so a launchable **Chrome/Chromium is a prerequisite**
  (assume one is installed; do not provision it). Never fall back to
  `gt.save()` (deprecated), `.as_raw_html()` + a screenshot tool, PIL/Pillow,
  imgkit/wkhtmltoimage/weasyprint, Playwright/Selenium/headless-chrome, or
  writing `table.html`. If rendering fails, **stop and surface the error
  verbatim** — a fallback produces a fake table.
- **Imports.** `from great_tables import GT, md, html, style, loc`.

## Checker loop (required)

This is the **CI-checked variant**: it ships `scripts/` and adds **two
mechanical steps** to the flowchart above — a checker you *run* and helpers you
*import*. Every **design** decision is still yours. The procedure is here; the
full rule-id table and the helper signatures live in **`references/scripts.md`**
(open it once).

**The `gt` convention (not optional).** Bind the final table to a **top-level
module variable named `gt`** in `table.py` (`gt = GT(df)...`), then end with
`gt.gtsave("table.png")` as always. The checker execs `table.py`, reads `gt`,
and calls `gt.as_raw_html()` to inspect the rendered DOM; bound to any other
name it reports `gt-missing` and skips every DOM check. Rendering is
neutralised while checking (Chrome is not launched — `gtsave` is stubbed to
*record* its kwargs), so keep the `gtsave` call: it is inspected, it just
produces no PNG during the check.

**Run it, then iterate until `PASS`.** After writing `table.py`, run:

```
python gt_check.py table.py
```

It prints a loud banner, then one line per violation:

```
===== gt_check: FAIL (2 issue(s)) =====
  [rule-id] <what you missed> — expected: <what's expected> — read references/<file>
```

Exit code is `0` on `PASS`, `1` on `FAIL`; `INFO` notes are advisory and never
fail it. Every FAIL line ends in **`read references/<file>`** — the one
reference that pins that rule's fix (e.g. `too-many-measures → palettes.md`,
`domain-symmetry → big_color/diverging_fill.md`, `frame-missing`/
`striping-gate → small_color.md`). **Open that file, fix the flagged rule in
`table.py`, and re-run — repeat until it prints `PASS`.** Only then render for
real and finish (Step 7). A `PASS` means the prompt-independent style rules
hold; the checker never sees the prompt, so still audit the render against the
request yourself.

**Prefer the thin execution helpers** so the *mechanics* of a decision cannot
drift between runs:

```python
from gt_consistency import PALETTE, frame, finalize, heatmap, band, stripe, stub_tint
```

`heatmap` colors a measure (computes the shared domain, looks up the palette);
`band` applies the exact band hex + the mandatory bottom rule; `frame`/
`finalize` apply the boxed border and the `gtsave` margin/zoom; `stripe`/
`stub_tint` apply the pinned surfaces; `PALETTE` holds every hex and mirrors
`palettes.md` (**zero inlined hexes**). **They choose nothing** — you still
decide which columns, sequential vs diverging, which hue, light vs dark band,
and pass each in as an argument. This is the only place scripts enter the flow.
