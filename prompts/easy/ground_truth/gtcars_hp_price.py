"""Ground truth for prompts/easy/gtcars_hp_price.json.

Data: data/gtcars.csv  (47 specific car trims/configurations; one row per
      mfr+model+trim combination -- horsepower, torque, mpg, drivetrain,
      transmission, country of origin, and MSRP)
Story: Every gt_cars trim, showing just the two measures the prompt names --
       horsepower and price -- ranked from most to least expensive.

Design decisions (documented here since none of these are dictated by the
prompt's own wording):

- Row scope: the prompt has no limiting language ("top N", a filter, a make)
  -- it just says "the gt cars" -- so all 47 rows are shown. 47 is simply
  how many rows the CSV happens to have, not something the prompt demanded,
  so REQUIRED_INSTRUCTIONS below does NOT set row_count.
- Stub: mfr + model. Checked directly against the data (see the groupby in
  the commit that added this file) -- every (mfr, model) pair in gtcars.csv
  is already unique across all 47 rows, so no trim suffix is needed to
  disambiguate; adding one would just add stub-label noise for zero
  disambiguation benefit.
- Colored measure: msrp only. Financial rule -- money gets the sequential
  Blues heatmap treatment only when it's the hero measure the request is
  about, and here price is one of exactly two things asked for, making it
  a natural single hero rather than a secondary detail. hp gets bold text
  instead of a second fill (the same "hero, uncolored" pattern the ceiling
  rule points to) -- coloring both would still be within the <=2 ceiling,
  but two heatmaps competing for attention buys nothing over one clear
  gradient + one bold column when there's no third dimension (e.g. a
  country/body-style split) that would make two independent color stories
  useful.
- Sort: descending by msrp. No sort is requested, but since price is the
  chosen color hero, ranking by it makes the Blues gradient read top-to-
  bottom as a visual ramp (darkest at the top) rather than a scattered
  pattern -- the same "pick one defensible ranking and say why" transparency
  towny_growth_trends.py uses for its own ranking choice.
- No grouping/spanner: the prompt names exactly two measures and nothing
  about a category split (make, body style, country, drivetrain) -- adding
  one would be inventing structure the prompt never asked for.
"""
from pathlib import Path

import pandas as pd
from great_tables import GT, loc, style

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent.parent

# ---- Ground-truth comparator metadata --------------------------------------
# Read directly by scripts/gt_compare.py via module import. Keep these as
# literal dict/list assignments (no computation) so they're both a plain-text
# answer key a human can review and something a script can load without exec
# risk beyond what already happens to render the table.

# Acceptable label synonyms per underlying data column. Wording is free; the
# label just has to name the right concept. Keys are the SOURCE CSV column
# name(s) the label is standing in for. "car" (the derived mfr+model stub)
# is deliberately absent -- it's the stub, not a `cols_label`-driven column,
# the same treatment towny_growth_trends.py gives its own `name` stub.
LABEL_SYNONYMS = {
    "hp": ["horsepower", "hp"],
    "msrp": ["price", "msrp", "sticker price"],
}

# The prompt ("Show me a table of the gt cars with their horsepower and
# price") makes no explicit structural demand -- no row count, no requested
# grouping, no requested sort order -- so this is intentionally empty.
REQUIRED_INSTRUCTIONS = {}

# Keyword-presence check for the caption/subtitle overlap rule. Verified
# against the actual rendered text below (case-insensitive substring): the
# caption's unique insight is the Bentley/Corvette price-vs-horsepower
# divergence, which the subtitle (a plain "sorted by MSRP" description)
# never states.
CAPTION_KEYWORDS = {
    "caption_should_mention": ["bentley", "corvette", "don't move together"],
    "subtitle_should_not_duplicate": ["bentley", "corvette", "don't move together"],
}

# Underlying SOURCE CSV column(s) that are the canonical colored measure(s),
# used for value-based matching -- NOT the rendered column name/label.
CANONICAL_MEASURES = {
    "colored": ["msrp"],
    "hero_uncolored": ["hp"],
}

# Semantic type per rendered column, for the fmt_* correctness check.
SEMANTIC_TYPES = {
    "hp": "integer",
    "msrp": "currency",
}

# ---- Data prep -------------------------------------------------------------
df = pd.read_csv(_ROOT / "data" / "gtcars.csv")

# "car" = mfr + model. Confirmed unique across all 47 rows (no mfr/model
# pair repeats even though several manufacturers have multiple trims of the
# same model elsewhere in the wider dataset universe) -- see the design note
# above.
df["car"] = df["mfr"] + " " + df["model"]

cars = (
    df[["car", "hp", "msrp"]]
    .sort_values("msrp", ascending=False)
    .reset_index(drop=True)
)

# ---- Color domain -----------------------------------------------------------
msrp_lo = float(cars["msrp"].min())
msrp_hi = float(cars["msrp"].max())

# ---- Table -------------------------------------------------------------------
gt = (
    GT(cars, rowname_col="car")
    .tab_header(
        title="GT Cars: Horsepower and Price",
        subtitle="All 47 makes and models in the gtcars dataset, sorted from highest to lowest MSRP",
    )
    .tab_stubhead(label="Car")
    .cols_label(hp="Horsepower", msrp="Price (MSRP)")
    .fmt_integer(columns=["hp"])
    .fmt_currency(columns=["msrp"], decimals=0)
    .sub_missing(columns=["hp", "msrp"], missing_text="—")
    # Big Color 1/2 (of an allowed 2; only 1 used here) -- price, sequential
    # Blues, since MSRP is the chosen hero measure (see design note above).
    .data_color(
        columns=["msrp"],
        palette="Blues",
        domain=[msrp_lo, msrp_hi],
        na_color="#808080",
        truncate=False,
    )
    # Hero, uncolored measure -- horsepower gets bold text rather than a
    # second fill, per the same "hero, uncolored" pattern towny_growth_
    # trends.py uses for its own rank/total_growth_pct columns.
    .tab_style(style=style.text(weight="bold"), locations=loc.body(columns=["hp"]))
    # Column-label band -- accent_tint navy (matches the msrp heatmap's
    # Blues family, per the DA hue-selection rule: match an existing
    # heatmap's hue first). Frame + hairlines are the global constants.
    .tab_options(
        column_labels_background_color="#C9E0F0",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
        column_labels_border_bottom_style="solid",
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        table_border_top_style="solid", table_border_top_color="#CCCCCC", table_border_top_width="1px",
        table_border_bottom_style="solid", table_border_bottom_color="#CCCCCC", table_border_bottom_width="1px",
        table_border_left_style="solid", table_border_left_color="#CCCCCC", table_border_left_width="1px",
        table_border_right_style="solid", table_border_right_color="#CCCCCC", table_border_right_width="1px",
    )
    # Stub tint -- the quieter washed navy, one tier down from the louder
    # band above it (same band/stub hierarchy towny_growth_trends.py uses).
    .tab_style(style=style.fill(color="#EAF0F6"), locations=loc.stub())
    .cols_align(align="right", columns=["hp", "msrp"])
    # No striping: with only two body columns (hp bold, msrp colored) the
    # body is already fully accounted for by color/bold -- striping and
    # fills would just fight each other visually, per the house striping
    # gate ("skip when the body isn't already essentially fully covered").
    .tab_source_note(
        source_note=(
            "Price and horsepower don't move together: the Bentley Continental GT costs more "
            "than the Chevrolet Corvette Z06 despite having 150 fewer horsepower (500 vs. 650 hp)."
        )
    )
    .tab_source_note(source_note="Source: gtcars dataset (Posit / great_tables sample data).")
)

gt.gtsave(str(_HERE / "gtcars_hp_price.png"), zoom=2.0, expand=15)
