> Load this file to understand the two scripts this (CI-checked) variant ships in
> `scripts/`: the `gt_check.py` checker you run after writing `table.py`, and the
> `gt_consistency.py` execution helpers you import inside it. This is mechanical
> tooling detail only — every *design* decision still lives in `SKILL.md`,
> `references/palettes.md`, `references/small_color.md`, and `references/big_color/`.
> The scripts choose nothing; they only execute a decision you already made.

# Scripts — the CI checker and the execution helpers

This variant adds two mechanical steps to the 7-step flowchart. Every design
decision is still yours; these scripts only make the *mechanics* reproducible and
tell you, before you render, which flowchart rule you missed.

- **`scripts/gt_check.py`** — a standalone CI style-checker you **run** as a
  subcommand after writing `table.py`. It never sees the user's prompt, so it only
  enforces the **prompt-independent** style rules the flowchart pins down.
- **`scripts/gt_consistency.py`** — a library you **import** inside `table.py`. It
  holds `PALETTE` (every hex) plus thin helpers that execute a Step-3/4/5 decision
  identically every run.

---

## `gt_check.py` — the CI checker

### Invocation

```bash
python gt_check.py table.py          # human report; exit 0 = PASS, 1 = FAIL
python gt_check.py table.py --json    # also dump a machine-readable summary
```

Run it from the directory that holds `table.py`. It is **never imported** by
`table.py`; you run it, read the report, fix the flagged rules, and re-run.

### The `gt` top-level-variable convention (mandatory)

`gt_check.py` inspects your table two ways: it reads `table.py` as **text** (regex),
and it **execs** the file in a fresh namespace to inspect the **rendered DOM**. To
get the DOM it reads a **module-level variable named `gt`** and calls
`gt.as_raw_html()`. So:

- **Bind the final `GT` object to a top-level `gt`** in `table.py`
  (`gt = GT(df)...` then `gt.gtsave("table.png")`). If the table is bound to any
  other name, the checker prints the `gt-missing` finding and every DOM-level check
  is skipped.
- **Keep the `gt.gtsave("table.png", ...)` call.** Rendering is neutralised during
  the check (Chrome is not launched — `gtsave` is monkeypatched to a no-op that
  *records its kwargs*), so the checker can still verify `zoom`/`expand` without
  producing a PNG. `import gtskill_chrome` is also stubbed, so it can never fail
  during the check.
- The file must **exec cleanly**; a runtime error becomes the `exec-error` finding.

### How to read the output

A loud one-line banner, then one line per violation:

```
===== gt_check: PASS =====
===== gt_check: FAIL (2 issue(s)) =====
  [rule-id] <what you missed> — expected: <what's expected> — read references/<file>
```

- **`FAIL` lines print first, then `INFO` notes** (tagged `(info)`).
- **Exit code** is `0` when there are no `FAIL`-level findings, `1` otherwise.
  `INFO` notes never change the exit code — they are advisory.
- Each line ends with **`read references/<file>`** (an openable path): the **one
  focused reference** that documents the fix for that rule. A failing check tells you
  exactly which reference to open — go open it.
- A **PASS means only that the prompt-independent style rules hold**. The checker
  cannot judge instruction-following (which columns to show, how to group), so still
  audit the render against the prompt (Step 7) yourself.

### The iterate-until-PASS loop (required)

```
write table.py  →  python gt_check.py table.py  →  FAIL?
                        │                              │
                        │ PASS                         ▼
                        ▼                     open each referenced file,
                 render + finish              fix that rule in table.py,
                                              re-run gt_check.py
                                                   (repeat until PASS)
```

Only render for real and finish **after** the checker prints `PASS`.

### Rule ids → the reference each one routes you to

Every rule maps to the single reference file that pins its fix (this is the
`read references/<file>` at the end of each line).

| Rule id | Level | What it catches | Read |
|---|---|---|---|
| `too-many-measures` | FAIL | More than 2 colored measures (`data_color`/`heatmap` targets, or DOM-colored columns) | `palettes.md` |
| `palette-signedness` | FAIL | A **diverging** palette on **unsigned** data (domain does not straddle 0) | `big_color/diverging_fill.md` |
| `domain-symmetry` | FAIL | A signed diverging `domain=` that is **not symmetric about 0** | `big_color/diverging_fill.md` |
| `domain-present` | FAIL | A literal `data_color(...)` with **no explicit `domain=`** | `big_color/column_gradient_fill.md` |
| `frame-missing` | FAIL | No enclosing boxed frame, or LEFT/RIGHT border **style** left at `none` (color/width alone is invisible) | `small_color.md` |
| `heading-band` | FAIL | No band, wrong **shade** for the Big-Color state (light w/ Big Color, dark w/o), a non-palette hex, or a dark band without white labels | `palettes.md` |
| `render-params` | FAIL | `gtsave` `zoom < 2.0` or `expand <= 5` (INFO if no `gtsave` call is detected) | `small_color.md` |
| `striping-gate` | FAIL | ≥10 body rows, body **not** fully color-filled, but striping not enabled | `small_color.md` |
| `orphan-stub` | FAIL | `tab_stubhead(...)` set but no `rowname_col=` in `GT(...)` | `small_color.md` |
| `opt-stylize-banned` | FAIL | `opt_stylize(...)` used as a whole-table styler | `small_color.md` |
| `formatting` | INFO | Numeric `data_color` present but **no** `fmt_*` formatter (numbers may render raw) | `small_color.md` |
| `gt-missing` | FAIL | Ran clean, but **no module-level `gt`** to inspect | `small_color.md` |
| `exec-error` | FAIL | `table.py` raised while executing | `small_color.md` |
| `dom-error` | INFO | `gt.as_raw_html()` failed; DOM-level checks skipped (source checks still ran) | `small_color.md` |
| `check-error` | FAIL/INFO | File not found, or an internal checker error (a checker bug, not a table problem) | `small_color.md` |

Source-level checks always run; DOM-level checks degrade gracefully — if exec or
`as_raw_html()` fails, that failure is reported as its own finding and the
source-only checks still run.

---

## `gt_consistency.py` — the execution helpers

Import the helpers you need at the top of `table.py`:

```python
from gt_consistency import PALETTE, frame, finalize, heatmap, band, stripe, stub_tint
```

These helpers **encode zero design decisions**. Each takes your flowchart decision
as an argument and only guarantees that two runs which made the *same* decision
execute it **identically**, so the *mechanics* can no longer drift between runs.
Every hex or palette NAME they emit is read from `PALETTE` or passed in by you —
none is inlined. `PALETTE` **mirrors `references/palettes.md`** (the single source of
truth), and `tests/test_palette_parity.py` fails CI if the two ever diverge. So when
a value changes, change `palettes.md`, then this module — never the reverse.

### `PALETTE`

A nested dict mirroring `palettes.md`:

- `PALETTE["solid"][hue]` — the six Dark Academia **solids** (`navy`, `forest`,
  `oxblood`, `espresso`, `ochre`, `tan`); white text on every solid.
- `PALETTE["washed"][hue]` — the **washed light tint** paired with each solid.
- `PALETTE["neutral"][role]` — structural greys (`label_band`, `row_stripe`,
  `hairline`, `column_label_rule`, `structural_rule`, `vertical_divider`, `na_cell`).
- `PALETTE["sequential"][key]` / `PALETTE["diverging"][key]` — matplotlib/brewer
  palette **NAMES** (passed to `data_color(palette=...)`, not fixed hexes).

### `heatmap(gt, columns, *, kind, hue, domain=None)` — Step 3

Colors one measure's column(s) by value. **You** decide `columns`, `kind`, `hue`;
the helper only executes. It does **not** auto-detect signedness or pick columns.

- `columns` — str or list; colored **together** under one shared domain/palette so
  facets stay comparable.
- `kind` — `"sequential"` or `"diverging"` (your Step-3 call).
- `hue` — a semantic key resolved through `PALETTE` (sequential: `positive` /
  `warning` / `warning_alt` / `neutral`; diverging: `default` / `colorblind_safe`),
  **or** an explicit matplotlib/brewer palette NAME passed straight through.
- `domain` — leave `None` to compute from the GT's own data: symmetric `[-M, M]`
  for diverging, full `[min, max]` for sequential. Pass a list to override.

Applies `data_color` with the pinned `na_color`, `truncate=False`,
`autocolor_text=True`. Because the domain is computed, a `heatmap(...)` with no
explicit `domain=` does **not** trip `domain-present` (that rule targets bare
`data_color(...)` only).

```python
gt = heatmap(gt, ["q1", "q2", "q3", "q4"], kind="sequential", hue="neutral")
gt = heatmap(gt, "net_change", kind="diverging", hue="default")   # → [-M, M]
```

### `band(gt, *, shade, hue)` — Step 4

Applies the heading band **and** the mandatory column-label bottom rule (the 2px
`column_label_rule` — present under any band).

- `shade` — `"light"` or `"dark"` (your Step-4 call).
- `hue` — a solid/washed key (`navy` … `tan`) or `"grey"`.
- **light** → `column_labels_background_color` = the washed tint (or the neutral grey
  label band for `hue="grey"`). **dark** → the DA solid **plus white column-label
  text** (and white spanner labels), applied via `tab_style` because great-tables has
  no `tab_options` option for column-label text color.

```python
gt = band(gt, shade="light", hue="forest")   # table has Big Color
gt = band(gt, shade="dark", hue="navy")       # no Big Color → dark anchor band
```

### `stripe(gt)` and `stub_tint(gt, *, hue)` — Step 5

- `stripe(gt)` — turns on zebra striping (`opt_row_striping()`) and pins the exact
  stripe hex (`PALETTE["neutral"]["row_stripe"]`). Satisfies the `striping-gate` rule.
- `stub_tint(gt, *, hue)` — tints the stub background: `hue="grey"` → the neutral
  label-band grey; any DA hue → its washed tint.

```python
gt = stripe(gt)
gt = stub_tint(gt, hue="forest")
```

### `frame(gt, ...)` and `finalize(gt, ...)` — global constants

- `frame(gt, color=None, width="1px", style="solid")` — the non-negotiable boxed
  enclosing border on all four sides. Sets the side border **style** explicitly
  (great-tables defaults it to `none`), which is what the `frame-missing` check
  requires. Defaults `color` to `PALETTE["neutral"]["column_label_rule"]`.
- `finalize(gt, path="table.png", **overrides)` — `gt.gtsave(path, expand=15,
  zoom=2.0)`, letting any override (e.g. `vwidth`/`vheight`) win. These values
  satisfy the `render-params` check. You may instead call `gt.gtsave(...)` directly
  with `expand`/`zoom` at or above those defaults.

```python
gt = frame(gt)
finalize(gt, "table.png")            # or: gt.gtsave("table.png", expand=15, zoom=2.0)
```
