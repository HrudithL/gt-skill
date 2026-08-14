"""Ground truth for prompts/hard/countrypops_decade_growth.json.

Data: data/countrypops.csv  (annual population figures, 1960-2022, for
      every country in the World Bank series; one row per (country, year)).
Story: How the 10 most populous countries in 2020 got there -- their
       population at each decadal checkpoint from 1970 through 2020 and
       the growth percentage between consecutive decades.

Design decisions:

- Row scope: the prompt names "the 10 most populous" explicitly, so
  REQUIRED_INSTRUCTIONS pins row_count=10.
- Selection: top 10 by 2020 population (China, India, US, ...). Ordered
  descending by that 2020 figure (the ranking criterion the prompt
  frames the leaderboard around).
- Decadal checkpoints: 1970, 1980, 1990, 2000, 2010, 2020 -- exactly
  what "decade-by-decade from 1970 through 2020" spells out. Six
  columns.
- Inter-decade growth: 5 percent-change columns (70-80, 80-90, 90-00,
  00-10, 10-20). The measure is genuinely SIGNED across this slice --
  Russia lost 900K people between 1990 and 2000 (post-Soviet
  emigration) and Japan lost 1.8M between 2010 and 2020 (aging
  demographics); a "most populous" filter doesn't rule out shrinking
  countries because it's a snapshot cutoff, not a monotone-growth
  filter. So the growth block gets DIVERGING RdYlGn with a symmetric
  domain and `force_sign=True` on the fmt_percent call, not sequential
  Greens.
- Stub: `country_name`.
- Population scale: raw figures are 100M-1.4B; display as MILLIONS
  (float, one decimal) for readability, matching sp500_monthly_
  performance.py's own "billions of shares" scaling convention.
- Column layout: two spanners over the two paired blocks (matches the
  same two-spanner pattern towny_growth_trends.py uses for its
  density-and-inter-Census-change block). Spanner-boundary dividers
  applied per house rules.
- Colored measures (two, sharing one hue family per block):
  * Six `pop_YYYY_m` columns: SHARED sequential Blues (one domain
    across all six for a consistent visual scale, matching towny_
    growth_trends.py's own six-Census-year density block).
  * Five `growth_YY_YY` columns: SHARED DIVERGING RdYlGn (positive =
    good, no reverse). Symmetric domain [-M, M] with M =
    max(abs(min), abs(max)) per the house diverging default.
- Sort: descending by pop_2020_m.
- Header/stub branding: DEEP navy (#08306B) band + washed navy stub.

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

_DECADES = [1970, 1980, 1990, 2000, 2010, 2020]
# Kept as LITERAL lists (not list-comprehensions computed from _DECADES) so
# `_list_var_map` in runner/convergence.py can resolve `columns=_POP_COLS`
# in the data_color calls back to the actual column names -- the parser
# only reads simple list-literal assignments.
_POP_COLS = [
    "pop_1970_m", "pop_1980_m", "pop_1990_m",
    "pop_2000_m", "pop_2010_m", "pop_2020_m",
]
_GROWTH_COLS = [
    "growth_70_80", "growth_80_90", "growth_90_00",
    "growth_00_10", "growth_10_20",
]

# ---- Ground-truth comparator metadata --------------------------------------
LABEL_SYNONYMS = {
    "pop_1970_m": ["1970", "population 1970", "1970 pop"],
    "pop_1980_m": ["1980", "population 1980", "1980 pop"],
    "pop_1990_m": ["1990", "population 1990", "1990 pop"],
    "pop_2000_m": ["2000", "population 2000", "2000 pop"],
    "pop_2010_m": ["2010", "population 2010", "2010 pop"],
    "pop_2020_m": ["2020", "population 2020", "2020 pop"],
    "growth_70_80": ["1970-1980", "1970–1980", "70-80", "70s"],
    "growth_80_90": ["1980-1990", "1980–1990", "80-90", "80s"],
    "growth_90_00": ["1990-2000", "1990–2000", "90-00", "90s"],
    "growth_00_10": ["2000-2010", "2000–2010", "00-10", "2000s"],
    "growth_10_20": ["2010-2020", "2010–2020", "10-20", "2010s"],
}

REQUIRED_INSTRUCTIONS = {
    "row_count": 10,
}

CANONICAL_MEASURES = {
    "colored": [
        "pop_1970_m", "pop_1980_m", "pop_1990_m",
        "pop_2000_m", "pop_2010_m", "pop_2020_m",
        "growth_70_80", "growth_80_90", "growth_90_00",
        "growth_00_10", "growth_10_20",
    ],
    "hero_uncolored": [],
}

SEMANTIC_TYPES = {
    "pop_1970_m": "number", "pop_1980_m": "number", "pop_1990_m": "number",
    "pop_2000_m": "number", "pop_2010_m": "number", "pop_2020_m": "number",
    "growth_70_80": "percent", "growth_80_90": "percent", "growth_90_00": "percent",
    "growth_00_10": "percent", "growth_10_20": "percent",
}

# ---- Data prep -------------------------------------------------------------
df = pd.read_csv(_ROOT / "data" / "countrypops.csv")

# Top 10 by 2020 population (the ranking criterion).
top10_codes = (
    df[df["year"] == 2020]
      .dropna(subset=["population"])
      .nlargest(10, "population")
      [["country_name", "country_code_3", "population"]]
      .rename(columns={"population": "pop_2020"})
      .reset_index(drop=True)
)

# Pull the decadal checkpoint values for each of those countries.
wide = (
    df[df["year"].isin(_DECADES) & df["country_code_3"].isin(top10_codes["country_code_3"])]
    .pivot_table(
        index=["country_name", "country_code_3"],
        columns="year",
        values="population",
        aggfunc="first",
    )
    .reset_index()
)

# Preserve the top-10 ordering (descending by 2020 population).
wide = top10_codes[["country_name", "country_code_3"]].merge(wide, on=["country_name", "country_code_3"])

# Scale to millions (float, one decimal); more legible than 10-digit ints.
for y in _DECADES:
    wide[f"pop_{y}_m"] = wide[y] / 1e6

# Inter-decade growth (fractional; fmt_percent renders "+123.4%").
for a, b in zip(_DECADES[:-1], _DECADES[1:]):
    col = f"growth_{a % 100:02d}_{b % 100:02d}"
    wide[col] = (wide[b] - wide[a]) / wide[a]

final = wide[["country_name"] + _POP_COLS + _GROWTH_COLS].reset_index(drop=True)

# ---- Color domains ---------------------------------------------------------
pop_lo = float(np.nanmin(final[_POP_COLS].to_numpy()))
pop_hi = float(np.nanmax(final[_POP_COLS].to_numpy()))

g_lo = float(np.nanmin(final[_GROWTH_COLS].to_numpy()))
g_hi = float(np.nanmax(final[_GROWTH_COLS].to_numpy()))
g_m = max(abs(g_lo), abs(g_hi))

# ---- Table -----------------------------------------------------------------
gt = (
    GT(final, rowname_col="country_name")
    .tab_header(
        title="Population Trajectories of the 10 Most Populous Countries, 1970-2020",
        subtitle="Population at each decadal checkpoint (in millions) and the growth percentage between consecutive decades, ranked by 2020 population",
    )
    .tab_stubhead(label="Country")
    .tab_spanner(label="Population (millions)", columns=_POP_COLS)
    .tab_spanner(label="Inter-decade growth", columns=_GROWTH_COLS)
    .cols_label(
        pop_1970_m="1970", pop_1980_m="1980", pop_1990_m="1990",
        pop_2000_m="2000", pop_2010_m="2010", pop_2020_m="2020",
        growth_70_80="70-80", growth_80_90="80-90", growth_90_00="90-00",
        growth_00_10="00-10", growth_10_20="10-20",
    )
    .fmt_number(columns=_POP_COLS, decimals=1)
    .fmt_percent(columns=_GROWTH_COLS, decimals=1, force_sign=True)
    .sub_missing(columns=_POP_COLS + _GROWTH_COLS, missing_text="—")
    # Big Color 1/2: population -- shared sequential Blues, single domain
    # across all six decades for a consistent visual scale (matches
    # towny_growth_trends.py's six-Census-year density block).
    .data_color(
        columns=_POP_COLS,
        palette="Blues",
        domain=[pop_lo, pop_hi],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    # Big Color 2/2: inter-decade growth -- SHARED DIVERGING RdYlGn,
    # symmetric domain. Data crosses zero (Russia lost pop 1990-2000,
    # Japan 2010-2020), so this is genuinely a signed measure.
    .data_color(
        columns=_GROWTH_COLS,
        palette="RdYlGn",
        domain=[-g_m, g_m],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    .cols_width(cases={
        "country_name": "180px",
        **{c: "80px" for c in _POP_COLS},
        **{c: "85px" for c in _GROWTH_COLS},
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
        column_labels_padding_horizontal="5px",
        data_row_padding="5px",
        data_row_padding_horizontal="5px",
        source_notes_padding="6px",
    )
    .tab_style(style=style.text(color="white"), locations=loc.column_labels())
    .tab_style(style=style.fill(color="#EAF0F6"), locations=loc.stub())
    .cols_align(align="right", columns=_POP_COLS + _GROWTH_COLS)
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    # Spanner-boundary divider: between the pop and growth blocks.
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.body(columns="pop_2020_m"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.column_labels(columns="pop_2020_m"),
    )
    .tab_source_note(
        source_note=html(
            "China and India each added the population of a small country in every single "
            "decade -- but their growth rates halved over the period (China from +19.9% in the "
            "1970s to +5.5% in the 2010s). Nigeria alone accelerated: it grew faster in the "
            "2010s (+29.5%) than any other country on the list."
        )
    )
    .tab_source_note(
        source_note=html(
            "Source: <code>countrypops</code> dataset -- annual country population estimates "
            "from the World Bank (Posit / great_tables sample data)."
        )
    )
)

gt.gtsave(str(_HERE / "countrypops_decade_growth.png"), zoom=2.0, expand=8)
