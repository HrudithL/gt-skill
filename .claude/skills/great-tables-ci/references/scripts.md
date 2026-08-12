> Two scripts in `scripts/`: `gt_check.py` (run after writing `table.py`) and
> `gt_consistency.py` (import into `table.py`) — mechanical tooling only.
> Design decisions live in `SKILL.md`, `references/palettes.md`,
> `references/small_color.md`, `references/big_color/`; the scripts execute,
> never choose.

# Scripts — the CI checker and the execution helpers

This variant adds two mechanical steps to the 7-step flowchart, detailed below:
`gt_check.py` (enforces prompt-independent style rules) and `gt_consistency.py`
(executes Step-3/4/5 decisions identically every run).

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

`gt_check.py` inspects your table two ways: it reads `table.py` as **text**
(regex), and it **execs** the file in a fresh namespace to inspect the
**rendered DOM**. To get the DOM it reads a **module-level variable named
`gt`** and calls `gt.as_raw_html()`. So:

- **Bind the final `GT` object to a top-level `gt`** in `table.py`
  (`gt = GT(df)...` then `gt.gtsave("table.png")`). Any other name → the
  checker prints `gt-missing` and every DOM-level check is skipped.
- **Keep the `gt.gtsave("table.png", ...)` call.** Rendering is neutralised
  during the check (`gtsave` is monkeypatched to a no-op that *records its
  kwargs*, `import gtskill_chrome` is stubbed), so the checker can still
  verify `zoom`/`expand` without producing a PNG or launching Chrome.
- The file must **exec cleanly**; a runtime error becomes the `exec-error`
  finding.

### How to read the output

```
===== gt_check: PASS =====
===== gt_check: FAIL (2 issue(s)) =====
  [rule-id] <what you missed> — expected: <what's expected> — read references/<file>
```

- `FAIL` lines print first, then `INFO` notes (advisory only — never affect
  exit code, which is `0` iff there are no `FAIL` findings).
- Each line ends with **`read references/<file>`**: the one focused reference
  that documents the fix for that rule — go open it.
- A **PASS means only that the prompt-independent style rules hold**. The
  checker can't judge instruction-following (which columns to show, how to
  group), so still audit the render against the prompt (Step 7) yourself.

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
| `palette-signedness` | FAIL | A **diverging** palette on **unsigned** data (domain does not straddle 0) | `big_color/diverging_fill.md` |
| `domain-symmetry` | FAIL | A signed diverging `domain=` that is **not symmetric about 0** | `big_color/diverging_fill.md` |
| `domain-present` | FAIL | A literal `data_color(...)` with **no explicit `domain=`** | `big_color/column_gradient_fill.md` |
| `frame-missing` | FAIL | No enclosing boxed frame, or LEFT/RIGHT border **style** left at `none` (color/width alone is invisible) | `small_color.md` |
| `heading-band` | FAIL | No band, a hex other than the fixed branding navy (`#08306B`), column labels not bold, or a band without white label text — 2026-08-12: every table uses the SAME band regardless of Big Color; there is no more light/dark branching | `palettes.md` |
| `render-params` | FAIL | `gtsave` `zoom < 2.0` or `expand <= 5` (INFO if no `gtsave` call is detected) | `small_color.md` |
| `striping-gate` | FAIL | Striping not enabled on a body that is **not genuinely 100% color-filled** — 2026-08-12: striping is the default with no row-count floor; the old `>=10 rows` gate is gone | `small_color.md` |
| `stub-tint` | FAIL | A stub exists but its fill isn't the fixed branding tint (`#EAF0F6`) | `small_color.md` |
| `stripe-color` | FAIL | Row striping is enabled but its background isn't the fixed neutral grey (`#F6F6F6`) | `small_color.md` |
| `force-sign` | FAIL | A percent column whose own data genuinely crosses zero, formatted with `fmt_percent(...)` but no `force_sign=True` | `small_color.md` |
| `hero-not-bold` | FAIL | A column with no `data_color`/`heatmap` fill is bolded across its WHOLE body (a row-scoped highlight, e.g. only a top-N/bottom-N subset, is not this rule's target) | `small_color.md` |
| `orphan-stub` | FAIL | `tab_stubhead(...)` set but no `rowname_col=` in `GT(...)` | `small_color.md` |
| `opt-stylize-banned` | FAIL | `opt_stylize(...)` used as a whole-table styler | `small_color.md` |
| `formatting` | INFO | Numeric `data_color` present but **no** `fmt_*` formatter (numbers may render raw) | `small_color.md` |
| `layout-advisory` | INFO | No `cols_width(cases={...})` call, and/or the standard `tab_options` padding block is incomplete — a consistency nicety, never a hard gate | `small_color.md` |
| `gt-missing` | FAIL | Ran clean, but **no module-level `gt`** to inspect | `small_color.md` |
| `exec-error` | FAIL | `table.py` raised while executing | `small_color.md` |
| `dom-error` | INFO | `gt.as_raw_html()` failed; DOM-level checks skipped (source checks still ran) | `small_color.md` |
| `check-error` | FAIL/INFO | File not found, or an internal checker error (a checker bug, not a table problem) | `small_color.md` |

> **Note (2026-08-12):** a hard ceiling on the number of distinct colored
> measures used to live here and has been REMOVED entirely (not downgraded to
> an advisory) — the project owner rejected any numeric cap outright: color
> the measures that deserve emphasis, with the correct palette for each.
> Nothing in `gt_check.py` reports on colored-measure count any more.

Source-level checks always run; DOM-level checks degrade gracefully — if exec
or `as_raw_html()` fails, that failure is reported as its own finding and the
source-only checks still run.

---

## `gt_consistency.py` — the execution helpers

Import the helpers you need at the top of `table.py`:

```python
from gt_consistency import PALETTE, frame, finalize, heatmap, band, stripe, stub_tint
```

These helpers encode zero design decisions — they only guarantee identical
execution of a decision you already made; every hex/palette NAME comes from
`PALETTE` or is passed in by you. `PALETTE` **mirrors `references/palettes.md`**
(source of truth; `tests/test_palette_parity.py` fails CI on drift). When a
value changes: edit `palettes.md`, then this module — never the reverse.

### `PALETTE`

A nested dict mirroring `palettes.md`:

- `PALETTE["solid"][hue]` — the six Dark Academia **solids** (`navy`, `forest`,
  `oxblood`, `espresso`, `ochre`, `tan`); white text on every solid.
- `PALETTE["washed"][hue]` — the **washed light tint** paired with each solid.
- `PALETTE["neutral"][role]` — structural greys (`label_band`, `row_stripe`,
  `hairline`, `column_label_rule`, `structural_rule`, `vertical_divider`, `na_cell`).
- `PALETTE["sequential"][key]` / `PALETTE["diverging"][key]` — matplotlib/brewer
  palette **NAMES** (passed to `data_color(palette=...)`, not fixed hexes).
- `PALETTE["branding"][role]` — the FIXED, universal header/stub/stripe
  surface (`header`, `stub_tint`, `stripe`) every table now uses (2026-08-12
  redesign), read by `band()` and `stub_tint()` instead of a per-hue lookup.

### `heatmap(gt, columns, *, kind, hue, domain=None)` — Step 3

Colors one measure's column(s) by value. **You** decide `columns`, `kind`,
`hue`; the helper only executes — it does not auto-detect signedness or pick
columns.

- `columns` — str or list; colored **together** under one shared
  domain/palette so facets stay comparable.
- `kind` — `"sequential"` or `"diverging"` (your Step-3 call).
- `hue` — a semantic key resolved through `PALETTE` (sequential: `positive` /
  `warning` / `warning_alt` / `neutral`; diverging: `default` /
  `colorblind_safe`), **or** an explicit matplotlib/brewer palette NAME passed
  straight through.
- `domain` — leave `None` to compute from the GT's own data: symmetric
  `[-M, M]` for diverging, full `[min, max]` for sequential. Pass a list to
  override.

Applies `data_color` with the pinned `na_color`, `truncate=False`,
`autocolor_text=True`. Because the domain is computed, a `heatmap(...)` with
no explicit `domain=` does **not** trip `domain-present` (that rule targets
bare `data_color(...)` only).

```python
gt = heatmap(gt, ["q1", "q2", "q3", "q4"], kind="sequential", hue="neutral")
gt = heatmap(gt, "net_change", kind="diverging", hue="default")   # → [-M, M]
```

### `band(gt, *, shade="dark", hue="navy")` — Step 4

**2026-08-12 redesign:** the header is now a FIXED branding surface — every
table gets the identical deep-navy band (`PALETTE["branding"]["header"]` =
`#08306B`), bold column labels, and white column-label/spanner text,
regardless of Big Color or which measure(s) are heatmapped. `shade`/`hue` are
still accepted (defaulting to `"dark"`/`"navy"`) as a no-op-for-branding
escape hatch for any existing call site — they no longer change the OUTPUT
hex; the band never follows a per-measure heatmap hue. Also applies the
mandatory column-label bottom rule (the 2px `column_label_rule`).

```python
gt = band(gt)                          # fixed navy band, bold labels, white text
gt = band(gt, shade="light", hue="forest")   # same output — shade/hue no longer matter
```

Satisfies `heading-band`'s fixed-hex + bold-label + white-text checks.

### `stripe(gt)` and `stub_tint(gt, *, hue="navy")` — Step 5

- `stripe(gt)` — turns on zebra striping (`opt_row_striping()`) and pins the
  exact stripe hex (`PALETTE["branding"]["stripe"]` = `#F6F6F6`). Satisfies
  the `striping-gate`/`stripe-color` rules.
- `stub_tint(gt, *, hue="navy")` — **2026-08-12 redesign:** tints the stub to
  the fixed branding tint (`PALETTE["branding"]["stub_tint"]` = `#EAF0F6`),
  unconditionally. `hue` is accepted as a no-op-for-branding escape hatch (it
  no longer selects a per-hue washed tint) — the stub is a branding surface,
  same reasoning as `band()`. Satisfies the `stub-tint` rule.

```python
gt = stripe(gt)
gt = stub_tint(gt)                 # or stub_tint(gt, hue="forest") — same #EAF0F6 output
```

### `frame(gt, ...)` and `finalize(gt, ...)` — global constants

- `frame(gt, color=None, width="1px", style="solid")` — the non-negotiable
  boxed enclosing border on all four sides. Sets the side border **style**
  explicitly (great-tables defaults it to `none`), which is what the
  `frame-missing` check requires. Defaults `color` to
  `PALETTE["neutral"]["column_label_rule"]`.
- `finalize(gt, path="table.png", **overrides)` — `gt.gtsave(path, expand=15,
  zoom=2.0)`, letting any override (e.g. `vwidth`/`vheight`) win. These values
  satisfy the `render-params` check. You may instead call `gt.gtsave(...)`
  directly with `expand`/`zoom` at or above those defaults.

```python
gt = frame(gt)
finalize(gt, "table.png")            # or: gt.gtsave("table.png", expand=15, zoom=2.0)
```
