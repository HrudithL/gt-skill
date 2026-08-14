"""Ground truth for prompts/medium/towny_top10_by_population.json.

Data: data/towny.csv  (414 Ontario municipalities; land area, population,
      and density across five Census windows from 1996 to 2021).
Story: The 10 largest Ontario municipalities in 2021, with each one's
       density in 2011 vs. 2021, the absolute density change over that
       decade, and the population growth rate for the same period.

Design decisions:

- Row scope: the prompt names "the 10 largest" explicitly, so
  REQUIRED_INSTRUCTIONS pins row_count=10.
- Ranking metric: 2021 population (the "largest ... by population"
  criterion in the prompt).
- Derived columns:
  * `density_change` = density_2021 - density_2011 (absolute change in
    persons/km²; ordinary "went up by X, went down by X" reading).
  * `growth_pct` = (population_2021 - population_2011) / population_2011
    (relative change, matching the towny_growth_trends.py convention
    that "growth" is a rate, not a headcount).
- Stub: `name` (municipality). Unique across the top 10.
- Column layout: a spanner "Population density (persons/km²)" over the
  two Census-year density columns (density_2011, density_2021), matching
  the same spanner pattern towny_growth_trends.py uses for its own
  density block. Adds a spanner-boundary divider on the trailing
  spanned column (density_2021) per house rules.
- Colored measures (two, with distinct hue families to avoid collision):
  * `population_2021`: sequential BLUES -- the ranking hero, plain
    positive magnitude.
  * `growth_pct`: sequential GREENS -- every value in this top-10 slice
    is strictly positive by construction (Toronto grew, Ottawa grew,
    etc.), so the data shape is genuinely sequential, not signed;
    Greens matches the house sequential.positive palette and its
    "more = better" reading of a growth column. `force_sign` is not
    passed because the data doesn't cross zero.
  Density (both Census years, and the delta) stays PLAIN -- these are
  context columns showing "how the population distributes" alongside
  the two colored heroes, per the house "color what the request is
  actually about" restraint rule; the prompt names population and the
  growth rate as the metric hero, and coloring density on top of those
  two would be a third color story without a distinct narrative role.
- Sort: descending by population_2021 (the ranking criterion).
- Header/stub branding: DEEP navy (#08306B) band + washed navy stub --
  decoupled from the Blues/RdYlGn heatmap hues.

`autocolor_text=True` on all `data_color()` calls is spelled out
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
    "population_2021": [
        "population", "2021 population", "population 2021", "pop 2021",
        "pop", "residents",
    ],
    "density_2011": ["2011", "density 2011", "2011 density"],
    "density_2021": ["2021", "density 2021", "2021 density"],
    "density_change": [
        "density change", "change in density", "delta density",
        "2011-2021 density change", "density delta",
    ],
    "growth_pct": [
        "growth", "growth rate", "population growth", "growth pct", "% growth",
        "2011-2021 growth", "growth 2011-2021", "growth 2011-21",
    ],
}

REQUIRED_INSTRUCTIONS = {
    "row_count": 10,
}

CANONICAL_MEASURES = {
    "colored": ["population_2021", "growth_pct"],
    "hero_uncolored": [],
}

SEMANTIC_TYPES = {
    "population_2021": "integer",
    "density_2011": "number",
    "density_2021": "number",
    "density_change": "number",
    "growth_pct": "percent",
}

# ---- Data prep -------------------------------------------------------------
df = pd.read_csv(_ROOT / "data" / "towny.csv")

top = (
    df.dropna(subset=["population_2021", "population_2011", "density_2011", "density_2021"])
      .nlargest(10, "population_2021")
      .loc[:, ["name", "population_2021", "density_2011", "density_2021", "population_2011"]]
      .reset_index(drop=True)
)
top["density_change"] = top["density_2021"] - top["density_2011"]
top["growth_pct"] = (top["population_2021"] - top["population_2011"]) / top["population_2011"]
top = top[[
    "name", "population_2021", "density_2011", "density_2021",
    "density_change", "growth_pct",
]]
top["population_2021"] = top["population_2021"].astype("int64")

# ---- Color domains ---------------------------------------------------------
pop_lo = float(top["population_2021"].min())
pop_hi = float(top["population_2021"].max())

g_lo = float(top["growth_pct"].min())
g_hi = float(top["growth_pct"].max())

# ---- Table -----------------------------------------------------------------
gt = (
    GT(top, rowname_col="name")
    .tab_header(
        title="The 10 Largest Ontario Municipalities, 2021",
        subtitle="Population, population density in 2011 and 2021, absolute density change over the decade, and the corresponding population growth rate",
    )
    .tab_stubhead(label="Municipality")
    .tab_spanner(label="Population density (persons/km²)", columns=["density_2011", "density_2021"])
    .cols_label(
        population_2021="2021 Population",
        density_2011="2011", density_2021="2021",
        density_change=html("Density<br>Δ 2011→2021"),
        growth_pct=html("Population<br>growth 2011→2021"),
    )
    .fmt_integer(columns=["population_2021"], use_seps=True)
    .fmt_number(columns=["density_2011", "density_2021", "density_change"], decimals=1)
    .fmt_percent(columns=["growth_pct"], decimals=1, force_sign=True)
    .sub_missing(
        columns=["population_2021", "density_2011", "density_2021", "density_change", "growth_pct"],
        missing_text="—",
    )
    # Big Color 1/2: population_2021 -- ranking hero, sequential Blues.
    .data_color(
        columns=["population_2021"],
        palette="Blues",
        domain=[pop_lo, pop_hi],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    # Big Color 2/2: growth_pct -- all-positive slice by construction,
    # so sequential Greens (house sequential.positive palette). Not
    # RdYlGn diverging: the check would legitimately flag that as a
    # sequential-vs-diverging shape mismatch on a top-N leaderboard where
    # every row is on the same side of zero.
    .data_color(
        columns=["growth_pct"],
        palette="Greens",
        domain=[g_lo, g_hi],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    .cols_width(cases={
        "name": "150px", "population_2021": "150px",
        "density_2011": "90px", "density_2021": "90px",
        "density_change": "130px", "growth_pct": "150px",
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
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    # Spanner-boundary dividers: leading (before the density block starts)
    # and after the density block ends.
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.body(columns="population_2021"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.column_labels(columns="population_2021"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.body(columns="density_2021"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.column_labels(columns="density_2021"),
    )
    .cols_align(
        align="right",
        columns=["population_2021", "density_2011", "density_2021", "density_change", "growth_pct"],
    )
    .tab_source_note(
        source_note=html(
            "Growth rate = (2021 pop − 2011 pop) ÷ 2011 pop. Brampton grew fastest of the ten "
            "(+25.3% over the decade, density up nearly 500 persons/km²); Mississauga barely "
            "budged (+0.6%). Toronto remains a category of its own — 2.8 M residents, more than "
            "the next three cities combined."
        )
    )
    .tab_source_note(
        source_note=html(
            "Source: Statistics Canada Census of Population, 2011 &amp; 2021, via the "
            "<code>towny</code> dataset (Posit / great_tables sample data)."
        )
    )
)

gt.gtsave(str(_HERE / "towny_top10_by_population.png"), zoom=2.0, expand=8)
