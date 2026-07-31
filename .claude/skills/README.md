# Great Tables Skill

Turn a CSV — or any tabular data — and a plain-language request into a
publication-ready table image. No design decisions are left to chance:
every table is driven through the same fixed flowchart, so the same kind of
data always comes out looking like the same product.

## The problem it solves

Ask a model to "make this a nice table" and you get a menu problem: pick a
palette, pick a band color, decide on stripes — and the same request asked
twice comes back styled two different ways. This skill replaces the menu
with a **flowchart**. For every part of a table there is one deterministic
rule, or one explicit, data-driven branch:

```
1. UNDERSTAND THE DATA   grain, identifiers, measures, categories, quality
2. ORGANIZE COLUMNS      show/hide · limit rows · stub (default) · groups
3. BIG COLOR             ≤ 2 colored measures, encoding chosen by data shape
4. HEADING BAND          light band if Big Color exists, dark if it doesn't
5. SMALL COLOR           fixed checklist: borders, dividers, striping, stub
                         tint, per-column formatting
6. TITLES & ANNOTATIONS  title + subtitle (required), caption, source —
                         each with one distinct job
7. RENDER & VERIFY       render, read the image back, audit every rule above
```

Every concrete value a table needs — a hex code, a color domain, a render
margin, a method signature — is pinned in exactly one reference file, and a
single router file is the only thing that names which one to open. The
top-level instructions carry **zero pinned values** on purpose, so nothing
gets "remembered" — and re-guessed differently — from one table to the next.

## Why it's cheap to run

The always-read instructions are small on purpose: about 200 lines total
(the flowchart plus its router). Everything else — palettes, formatting
rules, per-data-shape color treatments, the full API reference — lives
behind that router and is opened only on demand. A typical table reads the
data-cleaning rules, the palette file, and the one color-treatment file that
matches its data shape; the other color-treatment files, and usually the API
reference too, are never opened at all. In practice, a table touches roughly
600–900 lines out of the ~1,700 available — a fraction of the skill, not all
of it.

That discipline shows up as real cost, not just tidiness: reading the data,
deciding the design, writing the table script, and rendering + self-checking
the final image runs **$0.10–$0.21 per table** (mean $0.15) and **2.5K–7.8K
output tokens**, measured on a small, inexpensive model.

## Why it's consistent

Consistency here isn't a claim, it's a measured property: the same prompt,
run independently and repeatedly against a fresh agent each time, produces
tables whose design decisions agree with each other at these rates:

| Design decision | Agreement across independent, repeated generations |
|---|---|
| Column-group dividers placed correctly | 100% |
| Row grouping added only when warranted | 100% |
| Stub column choice | 90% |
| Boxed frame present | 87% |
| Caption present when the rule requires one | 87% |
| Row striping | 85% |
| Heading-band shade (light vs. dark) | 80% |
| Heading-band hue, source note, palette choice | 70–80% |

Composited into a single per-table score, independent generations of the
same prompt land at **0.74 on average (range 0.66–0.94)** across a
five-prompt corpus spanning finance, environment, demographics, and ranking
data. The decisions that are purely mechanical (dividers, grouping) are
essentially always identical; the ones that involve a genuine judgment call
on ambiguous data (exact hue, whether a source is knowable) show the most
legitimate spread — which is exactly where variation *should* live.

## Two ways to ship it

- **Prose flowchart** — the rules above, followed directly from the written
  instructions.
- **CI-checked variant** — the same flowchart, plus a standalone checker the
  agent runs against its own generated script and iterates against before
  declaring the table finished. It mechanically verifies the
  prompt-independent style rules (borders, dividers, stub tint,
  per-column formatting, source notes) that don't require judgment to
  confirm.

## What you get

A rendered table image and the script that produced it — nothing
hand-tweaked afterward. The same input characteristics (a ranked list, a
time series, a matrix of measures, a signed change) are always recognized
and always resolved the same way, so a set of tables built from this skill
reads as one coherent product instead of a pile of one-off designs.
