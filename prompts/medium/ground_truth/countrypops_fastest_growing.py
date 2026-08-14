"""Ground truth for prompts/medium/countrypops_fastest_growing.json.

Data: data/countrypops.csv  (annual population figures, 1960-2022, for
      every country in the World Bank series; one row per (country, year)).
Story: The 15 countries that grew fastest between 2000 and 2020, of
       those with at least one million residents in 2000 — a
       "small-country artefact" filter applied deliberately, since a
       country with 50,000 residents doubling in size shouldn't
       leaderboard against a nation of 40 million adding 15%.

Design decisions:

- Row scope: the prompt names "the 15 fastest-growing" explicitly, so
  REQUIRED_INSTRUCTIONS pins row_count=15.
- Growth metric: relative change `(pop_2020 - pop_2000) / pop_2000`.
  "Fastest-growing" in ordinary usage means highest RELATIVE growth
  rate (matches the towny_growth_trends.py canonical convention), NOT
  absolute headcount added — a country adding 5 million residents from
  a base of 50 million is growing more slowly than one adding 2 million
  from a base of 3 million.
- Filter: pop_2000 >= 1,000,000. The prompt states this explicitly
  ("of countries with at least one million residents in 2000"). Applied
  before ranking so tiny-baseline curiosities (Andorra, Monaco,
  small-island territories) don't dominate the leaderboard.
- Stub: `country_name`. Unique across the top 15.
- Colored measure: `growth_pct` only. All 15 rows here have strictly
  POSITIVE growth by construction (a "fastest-growing" leaderboard),
  so the semantic is a plain positive magnitude -> sequential GREENS
  (the house sequential.positive palette; matches the same
  more-is-more encoding used on gtcars_most_efficient's mpg column).
  pop_2000 and pop_2020 stay plain — they're context, not the "growth"
  hero.
- Sort: descending by growth_pct.
- Header/stub branding: DEEP navy (#08306B) band + washed navy stub —
  decoupled from the Greens heatmap hue.

`autocolor_text=True` on the `data_color()` call is spelled out
explicitly even though it's great_tables' own default, for the same
self-documenting-intent reason `na_color`/`truncate` are always spelled
out here.
"""
from pathlib import Path

import pandas as pd
from great_tables import GT, html, loc, style

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent.parent

# ---- Ground-truth comparator metadata --------------------------------------
LABEL_SYNONYMS = {
    "pop_2000": ["2000", "population 2000", "pop 2000", "2000 population"],
    "pop_2020": ["2020", "population 2020", "pop 2020", "2020 population"],
    "growth_pct": [
        "growth", "growth rate", "growth pct", "% growth", "growth %",
        "population growth", "2000-2020 growth", "growth 2000-2020",
    ],
}

REQUIRED_INSTRUCTIONS = {
    "row_count": 15,
}

CANONICAL_MEASURES = {
    "colored": ["growth_pct"],
    "hero_uncolored": [],
}

SEMANTIC_TYPES = {
    "pop_2000": "integer",
    "pop_2020": "integer",
    "growth_pct": "percent",
}

# ---- Data prep -------------------------------------------------------------
df = pd.read_csv(_ROOT / "data" / "countrypops.csv")

pop2000 = df[df["year"] == 2000][["country_name", "country_code_3", "population"]].rename(
    columns={"population": "pop_2000"}
)
pop2020 = df[df["year"] == 2020][["country_code_3", "population"]].rename(
    columns={"population": "pop_2020"}
)
merged = pop2000.merge(pop2020, on="country_code_3", how="inner").dropna(
    subset=["pop_2000", "pop_2020"]
)
merged["growth_pct"] = (merged["pop_2020"] - merged["pop_2000"]) / merged["pop_2000"]

top = (
    merged[merged["pop_2000"] >= 1_000_000]
    .nlargest(15, "growth_pct")
    .loc[:, ["country_name", "pop_2000", "pop_2020", "growth_pct"]]
    .reset_index(drop=True)
)
top["pop_2000"] = top["pop_2000"].astype("int64")
top["pop_2020"] = top["pop_2020"].astype("int64")

# ---- Color domain ----------------------------------------------------------
g_lo = float(top["growth_pct"].min())
g_hi = float(top["growth_pct"].max())

# ---- Table -----------------------------------------------------------------
gt = (
    GT(top, rowname_col="country_name")
    .tab_header(
        title="Fastest-Growing Countries, 2000–2020",
        subtitle="Population in 2000 and 2020 for the 15 countries with the highest growth rate over the period, of countries with at least one million residents in 2000",
    )
    .tab_stubhead(label="Country")
    .cols_label(
        pop_2000="2000 Population",
        pop_2020="2020 Population",
        growth_pct="Growth Rate",
    )
    .fmt_integer(columns=["pop_2000", "pop_2020"], use_seps=True)
    .fmt_percent(columns=["growth_pct"], decimals=1)
    .sub_missing(columns=["pop_2000", "pop_2020", "growth_pct"], missing_text="—")
    # Big Color 1/1: growth_pct -- all-positive slice by construction,
    # semantic is a plain positive magnitude -> sequential Greens (the
    # house sequential.positive palette).
    .data_color(
        columns=["growth_pct"],
        palette="Greens",
        domain=[g_lo, g_hi],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    .cols_width(cases={
        "country_name": "270px",
        "pop_2000": "160px", "pop_2020": "160px", "growth_pct": "140px",
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
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    .tab_style(style=style.text(color="white"), locations=loc.column_labels())
    .tab_style(style=style.fill(color="#EAF0F6"), locations=loc.stub())
    .cols_align(align="right", columns=["pop_2000", "pop_2020", "growth_pct"])
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    .tab_source_note(
        source_note=html(
            "Growth rate = (2020 pop − 2000 pop) ÷ 2000 pop; the ≥1 M-in-2000 filter keeps "
            "tiny-baseline curiosities off the leaderboard. Sub-Saharan Africa and the Gulf "
            "dominate — the UAE nearly tripled, and 8 of the 15 countries roughly doubled in "
            "population over just two decades."
        )
    )
    .tab_source_note(
        source_note=html(
            "Source: <code>countrypops</code> dataset — annual country population estimates "
            "from the World Bank (Posit / great_tables sample data)."
        )
    )
)

gt.gtsave(str(_HERE / "countrypops_fastest_growing.png"), zoom=2.0, expand=8)
