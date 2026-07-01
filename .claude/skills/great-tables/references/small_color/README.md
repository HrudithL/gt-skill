# Small Color — Subtle Aesthetic Techniques

Small Color techniques do **not** encode information. They quietly make the table feel professional, scannable, and finished, without competing with the data for attention.

Load only the file(s) for the technique(s) you plan to use.

## When to use Small Color

You've already handled the data emphasis (either applied a Big Color treatment or decided none was needed). The table is *correct* but feels stark, dense, or amateurish. Small Color adds polish.

Budget: **2–4 Small Color treatments per table maximum.** Beyond that you're decorating, not designing — the polish becomes noise.

## Generic principles of good vs bad aesthetic choices

**Good Small Color:**

- Barely noticeable in isolation. If a reader has to squint to see whether it's there, it's the right intensity.
- Reinforces structure the reader already perceives (separates stub from data, groups columns under a spanner, distinguishes header from body).
- Uses neutral or very low-saturation hues (near-whites, near-greys, faint versions of the table's brand color).
- Consistent: if you tint one structural row, tint them all the same way.
- Complementary to any Big Color already in the table. Never uses a hue that could be confused with a data-encoding color.

**Bad Small Color:**

- Saturated, bright, or high-contrast — reads as data emphasis when there is none, misleading the reader.
- Applied to only one out of several structurally-parallel elements (one striped row, one bordered column).
- Piled on: stripes + stub tint + heading tint + colored borders + tight padding + custom font all at once — no single element registers.
- Uses the same or adjacent hue as a Big Color treatment in the same table (e.g., pale green row stripes underneath a green `data_color` column — the stripes look like weak data signal).
- Overrides accessibility defaults (e.g., very low-contrast text) in the name of "cleaner" look.

## Technique index

| File | Technique | Reach for it when... |
|---|---|---|
| `row_striping.md` | Alternating pale background on every other body row | ≥10 body rows and the reader needs help tracking a value across a wide row |
| `stub_tint.md` | Very light fill on the stub column | Stub and value columns visually blur together; you want a soft separator |
| `heading_tint.md` | Very light tint on the column-label row | Header row is hard to distinguish from the body but you don't want a loud band |
| `subtle_borders.md` | Restrained border tweaks (thin body hlines, muted colors, header underline) | Table feels floaty or the row/col grid is too heavy by default |
| `light_vertical_dividers.md` | Thin vertical dividers between logical column groups | Multiple spanners or logical column blocks need visual separation |
| `compact_padding.md` | Tighter or looser row/column padding | Table is too dense (>15 rows) or too airy (<6 columns with lots of whitespace) |
| `font_family_choice.md` | Switch to a humanist or neo-grotesque font stack | Default system font feels off-register for the table's tone |

## Selection workflow

1. Look at the current table (mentally or after a first render). Ask: what feels *unfinished*?
2. Pick 2–4 techniques from the index above that directly address that feeling.
3. Apply them at the *quiet* intensity described in each file — if the treatment is loud enough to notice on its own, it's too loud.
4. If Small Color competes with an existing Big Color treatment, back off (reduce count or lower intensity further).
