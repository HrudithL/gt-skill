"""Ground truth for prompts/hard/gtcars_country_matrix.json.

Data: data/gtcars.csv  (47 gt-car trims: mfr, model, hp, msrp,
      drivetrain, transmission, country of origin).
Story: A "state of the industry" per-country cross-tab -- for each of the
       five countries that appear in the dataset, average and maximum
       horsepower, average and maximum MSRP, and how many specific cars
       come from that country.

Design decisions:

- Row scope: one row per country of origin. The data happens to have 5
  countries (Italy, UK, US, Japan, Germany). REQUIRED_INSTRUCTIONS is
  empty rather than pinning row_count=5 -- the count is a data
  property, not a prompt demand.
- Stub: `ctry_origin`.
- Column layout: two spanners over the two paired hp / msrp columns
  (matches the same "average + max" pattern towny_growth_trends.py
  uses for its Census-year density block). Spanner-boundary dividers
  applied per house rules.
- Colored measures (three, well within the house "no numeric cap"
  rule):
  * `avg_hp` and `max_hp`: SHARED sequential Blues -- both are the same
    measure (horsepower) at different aggregation levels, so they share
    one domain across both columns for a consistent visual scale.
  * `avg_msrp` and `max_msrp`: SHARED sequential Greens -- money hero
    for this "country comparison" cross-tab. Greens (not Blues) to
    avoid a hue collision with the hp block above; the currency
    domain is distinct from HP and financial magnitudes get a
    distinct hue for that reason. Domain shared across both columns
    for the same consistent-scale reason as the hp pair.
  `n_cars` (count) stays plain (a scale metric, not a color hero).
- Sort: descending by avg_msrp -- "priciest country of origin first"
  makes the story read from top to bottom.
- Header/stub branding: DEEP navy (#08306B) band + washed navy stub --
  decoupled from the Blues/Greens heatmap hues.

`autocolor_text=True` on both `data_color()` calls is spelled out
explicitly even though it's great_tables' own default, for the same
self-documenting-intent reason `na_color`/`truncate` are always spelled
out here.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from great_tables import GT, html, loc, style

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent.parent

# ---- Ground-truth comparator metadata --------------------------------------
LABEL_SYNONYMS = {
    "n_cars": ["cars", "n cars", "count", "number of cars", "n"],
    "avg_hp": ["avg hp", "average hp", "mean hp", "avg horsepower", "avg. horsepower"],
    "max_hp": ["max hp", "peak hp", "highest hp", "max horsepower"],
    "avg_msrp": ["avg msrp", "average msrp", "mean msrp", "avg price", "avg. price"],
    "max_msrp": ["max msrp", "peak msrp", "highest msrp", "max price"],
}

REQUIRED_INSTRUCTIONS = {}

CANONICAL_MEASURES = {
    "colored": ["avg_hp", "max_hp", "avg_msrp", "max_msrp"],
    "hero_uncolored": [],
}

SEMANTIC_TYPES = {
    "n_cars": "integer",
    "avg_hp": "integer",
    "max_hp": "integer",
    "avg_msrp": "currency",
    "max_msrp": "currency",
}

# ---- Data prep -------------------------------------------------------------
df = pd.read_csv(_ROOT / "data" / "gtcars.csv")

by_country = (
    df.groupby("ctry_origin")
      .agg(
          n_cars=("model", "count"),
          avg_hp=("hp", "mean"),
          max_hp=("hp", "max"),
          avg_msrp=("msrp", "mean"),
          max_msrp=("msrp", "max"),
      )
      .sort_values("avg_msrp", ascending=False)
      .reset_index()
)

# ---- Color domains ---------------------------------------------------------
hp_cols = ["avg_hp", "max_hp"]
hp_lo = float(np.nanmin(by_country[hp_cols].to_numpy()))
hp_hi = float(np.nanmax(by_country[hp_cols].to_numpy()))

msrp_cols = ["avg_msrp", "max_msrp"]
msrp_lo = float(np.nanmin(by_country[msrp_cols].to_numpy()))
msrp_hi = float(np.nanmax(by_country[msrp_cols].to_numpy()))

# ---- Table -----------------------------------------------------------------
gt = (
    GT(by_country, rowname_col="ctry_origin")
    .tab_header(
        title="GT Cars by Country of Origin",
        subtitle="Average and peak horsepower, average and peak MSRP, and total cars in the dataset for each country of origin, ranked by average price",
    )
    .tab_stubhead(label="Country")
    .tab_spanner(label="Horsepower", columns=hp_cols)
    .tab_spanner(label="MSRP", columns=msrp_cols)
    .cols_label(
        n_cars="Cars",
        avg_hp="Avg", max_hp="Peak",
        avg_msrp="Avg", max_msrp="Peak",
    )
    .fmt_integer(columns=["n_cars", "avg_hp", "max_hp"])
    .fmt_currency(columns=["avg_msrp", "max_msrp"], decimals=0)
    .sub_missing(columns=["n_cars", "avg_hp", "max_hp", "avg_msrp", "max_msrp"], missing_text="—")
    # Big Color 1/2: HP pair -- shared sequential Blues domain across
    # both columns for a consistent visual scale.
    .data_color(
        columns=hp_cols,
        palette="Blues",
        domain=[hp_lo, hp_hi],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    # Big Color 2/2: MSRP pair -- shared sequential Greens domain.
    # Greens (not Blues) to avoid a hue collision with the HP block.
    .data_color(
        columns=msrp_cols,
        palette="Greens",
        domain=[msrp_lo, msrp_hi],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    .cols_width(cases={
        "ctry_origin": "160px", "n_cars": "80px",
        "avg_hp": "110px", "max_hp": "110px",
        "avg_msrp": "140px", "max_msrp": "140px",
    })
    .tab_options(
        column_labels_background_color="#08306B",
        column_labels_font_weight="bold",
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
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="6px",
        data_row_padding="5px",
        data_row_padding_horizontal="6px",
        source_notes_padding="6px",
    )
    .tab_style(style=style.text(color="white"), locations=loc.column_labels())
    .tab_style(style=style.fill(color="#EAF0F6"), locations=loc.stub())
    .cols_align(align="right", columns=["n_cars", "avg_hp", "max_hp", "avg_msrp", "max_msrp"])
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    # Spanner-boundary dividers: leading (before HP block) and
    # between-groups (between HP and MSRP blocks).
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.body(columns="n_cars"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.column_labels(columns="n_cars"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.body(columns="max_hp"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.column_labels(columns="max_hp"),
    )
    .tab_source_note(
        source_note=html(
            "Italy tops both price columns by a wide margin — its 15 cars average over $312,000, "
            "capped by the Ferrari LaFerrari at $1.4 M. Germany contributes the most cars (16) "
            "but the lowest average price and horsepower, reflecting its broader range of "
            "middle-market grand tourers."
        )
    )
    .tab_source_note(
        source_note=html(
            "Source: <code>gtcars</code> dataset (Posit / great_tables sample data), 2014-2017 model years."
        )
    )
)

gt.gtsave(str(_HERE / "gtcars_country_matrix.png"), zoom=2.0, expand=8)
