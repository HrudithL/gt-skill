# Scientific

## Intent
Give an atmospheric chemist a reference card: rate constants for
ten common trace gases reacting with the hydroxyl radical (OH) at
298 K, with the units, the precision, and the uncertainty needed to
quote a number in another study. The reader is technical and expects
scientific-notation values, unit-bearing headers, and explicit
significant figures.

## Data shape
- Source: `data/reactions.csv`
- Rows: 10 (curated subset: methane through isoprene, sorted by k(298 K) ascending)
- Key columns:
  - `cmpd_name` (str) — common name; capitalized for display
  - `cmpd_formula` (str) — molecular formula (rendered as-is; no inline subscript markup in the source)
  - `cmpd_mwt` (float, g/mol) — molecular weight
  - `OH_k298` (float, cm³ molecule⁻¹ s⁻¹) — rate constant at 298 K, spanning 10⁻¹⁵ → 10⁻¹⁰
  - `OH_uncert` (float, fractional) — relative uncertainty (0.10 = ±10%)
- Notable nulls / outliers: a few compounds lack a quoted uncertainty; those render as `—`.

## Design choices
- **Sort ascending by `OH_k298`** — slow → fast walks the reader through reactivity in a natural reading order; eyes land on the slowest (methane) and end on the most reactive (isoprene).
- **`fmt_scientific(n_sigfig=3)` on the rate constant** — values span five orders of magnitude; only scientific notation can show them without truncation. Three significant figures matches the precision of the source compilation.
- **Units embedded in column headers** — `M_w (g mol⁻¹)`, `k(298 K)` with the CGS unit declared in the subtitle. Putting units in headers (not in cells) is the convention for scientific tables and is what makes them quotable.
- **`html(...)` for unit typography** — `cm³`, `s⁻¹`, `mol⁻¹` use proper superscripts/subscripts. Plain `cm^3 s^-1` reads as code, not chemistry.
- **`fmt_percent(decimals=0)` on uncertainty** — the source quotes uncertainty to whole percent; rendering `0.10` as `10%` is what a chemist expects.
- **`sub_missing` em-dash on uncertainty** — `—` reads as "not reported", which is the truth; blank or `0%` would mislead.
- **Compact data shape** — five columns, ten rows. A reference card is dense by design; this is not the place for spanners or grouping.
- **Source note** — credits IUPAC; without the provenance the numbers are not citable.

## What was deliberately omitted
- **Three other oxidant columns (O3, NO3, Cl)** — would quadruple the columns for marginal information; the OH reaction is the dominant atmospheric loss for most of these compounds, so the card focuses there.
- **Arrhenius A and Ea columns** — the audience reading at 298 K wants the room-temperature constant; temperature-extrapolation parameters belong in a separate table.
- **Lifetime estimates (derived from k and an assumed [OH])** — they would require committing to an OH concentration that is itself a chosen assumption; out of scope for a primary-data card.
- **SMILES / InChI keys** — useful for cheminformatics readers but visually heavy; an interested reader can join back to the source CSV.

## Anti-patterns avoided
- **`fmt_number(decimals=4)` on 10⁻¹⁵ values** → **`fmt_scientific(n_sigfig=3)`**: rounding tiny numbers to four decimals destroys them.
- **No units in headers** → **units in headers via `html(...)`**: cm³ molecule⁻¹ s⁻¹ vs `numbers` makes the column quotable.
- **Decimal uncertainty (0.10)** → **percent (10%)**: matches how the source publishes the value.
- **Random row order** → **sorted by k(298 K)**: reactivity is the story; the sort IS the narrative.
- **No header, no source note** → **`tab_header` + `tab_source_note` crediting IUPAC**: scientific values must trace back to a compilation.
