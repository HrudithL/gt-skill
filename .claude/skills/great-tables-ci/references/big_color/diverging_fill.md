# Big Color — Diverging Fill

Apply `data_color` with a diverging palette to a signed numeric column so that negatives and positives get opposite hues around a neutral midpoint.

## When to use

- Signed values (returns, P&L, YoY change, budget variance, deltas) where +/- carry **opposite meaning**, with 0 (or an explicit midpoint) as the natural neutral.
- One-directional data ("more = more" only) → use `column_gradient_fill.md` instead. A diverging palette on **unsigned** data is WRONG (see "Do NOT" below).

## Palette (pinned)

- **`RdYlGn` — default for any signed measure.** Deterministic; do not substitute a custom hex list. **Orientation** depends on which sign is *unfavorable* — resolve with the test below, don't assume.
- `RdBu` / `PuOr` — colorblind-safe alternatives when accessibility is a hard requirement.

### Orientation — which sign is red (computable, not a judgment call)

`RdYlGn` reads red→yellow→green from low→high. The only question: is **positive** the good (green) or bad (red) end?

- **Positive-is-bad?** True when **more = worse**: cost/spend **variance vs budget** or **over-budget** amount, **error**/**defect** count/rate, **latency/response time/delay**, **downtime**, **waste/scrap**, **churn**, **complaints**, **overrun** — i.e. rising values are the thing you want to *reduce*.
- **Resolution:**
  - positive-is-bad ⇒ **`palette="RdYlGn", reverse=True`** (green=negative=favorable, red=positive=unfavorable).
  - every other signed measure (**default** — returns, P&L, gain/loss, YoY growth, net delta, positive=good) ⇒ **`palette="RdYlGn"`** (no `reverse`; green=positive, red=negative).

The symmetric data-driven domain `[-M, M]`, `M = max(|min|, |max|)`, is **identical**
in both branches — only the palette direction flips, so `0` still sits at the neutral
midpoint. If unsure which side is unfavorable, state the chosen orientation in a source
note so the choice is reproducible.

## Recipe

```python
import numpy as np
from great_tables import GT

# SYMMETRIC, DATA-DRIVEN domain across ALL facet columns of this ONE measure.
cols = ["return"]                                        # every column that IS this measure
lo = float(np.nanmin(df[cols].to_numpy()))
hi = float(np.nanmax(df[cols].to_numpy()))
M  = max(abs(lo), abs(hi))                               # M = max(|min|, |max|)

gt = (
    GT(df, rowname_col="period")
    .fmt_percent(columns=cols, decimals=1, force_sign=True)
    .data_color(
        columns=cols,
        palette="RdYlGn",                            # signed default; RdBu / PuOr = colorblind-safe alts
        reverse=False,                               # positive=good default; set reverse=True for positive-is-bad (see Orientation)
        domain=[-M, M],                              # SYMMETRIC so 0 sits at the palette midpoint (identical in both orientations)
        truncate=False,                              # extreme outliers keep the strongest hue
    )
)
```

## Rules

- **Symmetric, data-driven domain — always `[-M, M]` where `M = max(|min|, |max|)`**
  computed over **all facet columns** of the measure. Compute it from the frame; never
  hand-pick a round bound. The domain is symmetric so `0` lands exactly on the palette
  midpoint and a +5% gain and a −5% loss render at equal saturation.
- **`force_sign=True`** in the formatter — sign shouldn't have to be inferred from color alone.
- **Don't also color the text** red/green on top of the fill — pick fill *or* colored-bold-text, not both. (Colored bold text for outliers only: use `bold_colored_number.md`, skip the fill.)
- **Leave `truncate=False`** (default) so extreme outliers still get the strongest hue.

## Do NOT (these are WRONG — the two failure modes)

- **Asymmetric domain** (e.g. `domain=[-30, 15]`) — WRONG. `0` must sit at the palette
  midpoint; an off-center domain shifts the neutral point, so equal-magnitude gains and
  losses render at different saturations and the red/green split lies about the data.
- **A diverging palette on UNSIGNED data** (e.g. `RdYlGn` on a price or volume) — WRONG.
  Diverging implies a good-vs-bad axis around a midpoint that does **not** exist for a
  pure magnitude; use a **sequential** gradient (`column_gradient_fill.md`) instead.

## Counts as

One Big Color treatment.
