---
name: great-tables-ci
description: Use when the user's request involves building any table with `great_tables`, `gt.GT`, `gtsave`, or turning tabular data (CSV, DataFrame, spreadsheet) into a rendered PNG. Drives every table through one deterministic 7-step flowchart — understand data, organize columns, Big Color (≤2 colored measures), heading band, Small-Color checklist, titles/annotations, render+verify — so the same input characteristics always produce the same publication-ready design. Before writing any Python, read `references/REFERENCE.md`: it routes every color, band, polish, and API decision to the exact reference file that pins its value. The mandatory renderer is `gt.gtsave("table.png")`. Invoke before reading the data or writing any Python — the flowchart shapes the whole script. (CI-checked variant.)
---

# Great Tables Skill

Build publication-ready display tables in Python with `great_tables`. This skill is
a **flowchart, not a menu**: for every part of a table there is one deterministic
rule (or one explicit, data-driven branch), so the **same input always produces the
same output**. **Every table reads as one product.**

## Read this before you write ANY Python

Before you write **any** Python, read **`references/REFERENCE.md`**. It is the single
doorway that routes every decision below to the exact reference file holding its
pinned value — palette, hex, domain rule, polish checklist, method signature, worked
example. **Do not skip it.** SKILL.md carries the *procedure and the decision points*;
it deliberately holds **zero** pinned values. Those live only in the references that
`REFERENCE.md` points you to.

## Rule 0 — the user's prompt overrides everything

Every rule below is a **default**. Any explicit instruction in the user's prompt wins
(a requested font, a column's format, "bold the totals," "show all rows"). The
flowchart decides what to do *in the absence of* an instruction; it never overrides
one. When a user instruction conflicts with a default, follow the user and drop the
conflicting default silently — do not fight it or add it back later.

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

The order is fixed: color intent (Step 3) is decided before the quiet polish (Step 5),
and the band (Step 4) can only be decided once Big Color is known.

## Withhold values, forbid guessing — open the file the action needs

SKILL.md names *what* to decide; the *value* you type lives only in a reference file.
Before you type the code below, open the file `REFERENCE.md` routes you to and **copy
the value out of it. Do NOT guess a palette, a hex, a domain, or a signature from
memory.**

- **Before you organize columns** (right after Step 1): open `data.md` and get to
  **one clean, correctly-typed DataFrame** — strip currency/percent strings to floats,
  coerce `object`-dtype numeric columns, fix a non-zero header row, cast SQL `Decimal`s.
  `great_tables` *formats* numbers; it does **not** parse strings, so a `"$1,200"` value
  silently breaks `fmt_*` / `data_color`.
- **Before you write any `data_color(...)`** (Step 3): the exact palette name, hexes,
  and domain live ONLY in the `big_color/<shape>.md` file `REFERENCE.md` names for your
  data shape. Open that file (plus `palettes.md`) and copy them. Do not invent a
  palette or a hex.
- **Before you set the heading band** (Step 4): open `palettes.md` and copy the exact
  band hex — the washed tint if the table has Big Color, the dark DA solid + white text
  if it does not — along with the hue-selection rule. Do not improvise a band color.
- **Before you run the Small-Color polish** (Step 5): open `small_color.md` and run its
  fixed checklist top to bottom. Every neutral hex, the striping gate, the stub tint,
  and the fmt-per-type rules are there. Do not improvise a grey.
- **Before you call any method you are unsure of** (any step): open `api.md` for the
  exact signature, arguments, and defaults. Do not guess an argument name.

If SKILL.md cannot answer it and you may not invent it, the reference **has** to be
opened.

## Global constants (true for every table)

Set once, never vary unless Rule 0 fires. These are **named rules**; their exact
numeric values live in the references.

- **Frame.** A boxed enclosing light border on all four sides + a margin around the
  whole table (never flat/edge-to-edge). The exact border color/width and the `gtsave`
  margin value are in `references/small_color.md`. Rounded corners preferred; a square
  light border is acceptable — the enclosing border + margin is the non-negotiable.
- **Header alignment.** Title + subtitle centered (the default).
- **Font family.** great-tables default. Do **not** set the font unless the user asks.
- **Font size.** Default; shrink as little as possible, only when forced.
- **Font-size fit rule.** When a table renders too big, in this order: (1) give it room
  — raise the `gtsave` width/height; (2) keep it crisp — raise the `gtsave` zoom;
  (3) **only then** reduce font size, by the smallest amount that restores clarity. The
  default zoom and the margin value are in `references/small_color.md`. Relative scale:
  title > subtitle > body > source/caption.

## Correctness gotchas (named rules — the values live in the references)

- **`data_color` domain.** Always set `domain=` to cover the full data range; a
  **signed/diverging** measure's domain must be **symmetric about 0** with
  `truncate=False`. The exact rule and the data-driven bound are in
  `references/big_color/diverging_fill.md`.
- **`fmt_percent` scale.** It expects values in decimal form (`0.15` renders as `15%`);
  if your data is already on a 0–100 scale, pass `scale_values=False`. See `api.md`.
- **Original column names** in `fmt_*` / `data_color` — not the `cols_label` display text.
- **Row indices in `loc.body()`** are 0-based display positions, not the DataFrame index.
- **Method chaining.** Build the whole table in one chained expression; collect row
  indices into lists rather than looping `tab_style` per row.
- **Renderer.** End with **`gt.gtsave("table.png")`** only. `gtsave()` renders
  through headless Chrome, so a launchable **Chrome/Chromium is a prerequisite**
  (assume one is installed; do not provision it). Never fall back to `gt.save()`
  (deprecated), `.as_raw_html()` + a screenshot tool, PIL/Pillow,
  imgkit/wkhtmltoimage/weasyprint, Playwright/Selenium/headless-chrome, or writing
  `table.html`. If rendering fails, **stop and surface the error verbatim** — a
  fallback produces a fake table.
- **Imports.** `from great_tables import GT, md, html, style, loc`.

## Checker loop (required)

This is the **CI-checked variant**: it ships `scripts/` and adds **two mechanical
steps** to the flowchart above — a checker you *run* and helpers you *import*. Every
**design** decision is still yours. The procedure is here; the full rule-id table and
the helper signatures live in **`references/scripts.md`** (open it once).

**The `gt` convention (not optional).** Bind the final table to a **top-level module
variable named `gt`** in `table.py` (`gt = GT(df)...`), then end with
`gt.gtsave("table.png")` as always. The checker execs `table.py`, reads `gt`, and
calls `gt.as_raw_html()` to inspect the rendered DOM; bound to any other name it
reports `gt-missing` and skips every DOM check. Rendering is neutralised while
checking (Chrome is not launched — `gtsave` is stubbed to *record* its kwargs), so
keep the `gtsave` call: it is inspected, it just produces no PNG during the check.

**Run it, then iterate until `PASS`.** After writing `table.py`, run:

```
python gt_check.py table.py
```

It prints a loud banner, then one line per violation:

```
===== gt_check: FAIL (2 issue(s)) =====
  [rule-id] <what you missed> — expected: <what's expected> — read references/<file>
```

Exit code is `0` on `PASS`, `1` on `FAIL`; `INFO` notes are advisory and never fail
it. Every FAIL line ends in **`read references/<file>`** — the one reference that
pins that rule's fix (e.g. `too-many-measures → palettes.md`, `domain-symmetry →
big_color/diverging_fill.md`, `frame-missing`/`striping-gate → small_color.md`).
**Open that file, fix the flagged rule in `table.py`, and re-run — repeat until it
prints `PASS`.** Only then render for real and finish (Step 7). A `PASS` means the
prompt-independent style rules hold; the checker never sees the prompt, so still
audit the render against the request yourself.

**Prefer the thin execution helpers** so the *mechanics* of a decision cannot drift
between runs:

```python
from gt_consistency import PALETTE, frame, finalize, heatmap, band, stripe, stub_tint
```

`heatmap` colors a measure (computes the shared domain, looks up the palette); `band`
applies the exact band hex + the mandatory bottom rule; `frame`/`finalize` apply the
boxed border and the `gtsave` margin/zoom; `stripe`/`stub_tint` apply the pinned
surfaces; `PALETTE` holds every hex and mirrors `palettes.md` (**zero inlined
hexes**). **They choose nothing** — you still decide which columns, sequential vs
diverging, which hue, light vs dark band, and pass each in as an argument. This is
the only place scripts enter the flow.
