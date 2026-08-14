"""Ground truth for prompts/hard/towny_density_quintiles.json.

Data: data/towny.csv  (414 Ontario municipalities; land area, population,
      density across five Census windows from 1996 to 2021).
Story: Split all municipalities into five quintiles by 2021 population
       density -- from Q1 (least dense, sparsely-populated townships)
       to Q5 (Toronto and its immediate GTA neighbours) -- and show how
       each quintile's total population evolved from 1996 to 2021, the
       resulting growth rate, and how many municipalities fall into
       each quintile.

Design decisions:

- Quintile definition: `pd.qcut(density_2021, q=5, labels=Q1..Q5)`.
  Transparent, reproducible, and produces roughly equal-sized bins (a
  few off-by-one because 414 doesn't divide evenly by 5).
- Row scope: exactly 5 rows as a direct mathematical consequence of
  "five quintiles"; REQUIRED_INSTRUCTIONS pins row_count=5.
- Stub: `quintile` label (Q1..Q5).
- Colored measures (two, distinct families):
  * `pop_2021`: sequential Blues -- the "how many people live in this
    density band today" hero.
  * `growth_pct`: sequential Greens -- every quintile grew between 1996
    and 2021 by construction of picking Ontario as the study area (all
    positive), so the semantic is sequential positive magnitude, not a
    diverging signed measure.
  `pop_1996` stays plain (context; the "then" side of the 25-year
  comparison, colored in the "now" side above). `n` stays plain (bin
  count, not a color hero).
- Sort: Q1 -> Q5 ascending density (a natural reading for a quintile
  breakdown).
- Header/stub branding: DEEP navy (#08306B) band + washed navy stub.

`autocolor_text=True` on both `data_color()` calls is spelled out
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
    "n": ["municipalities", "n", "count", "number of municipalities", "n municipalities"],
    "pop_1996": ["1996", "population 1996", "1996 population", "pop 1996"],
    "pop_2021": ["2021", "population 2021", "2021 population", "pop 2021"],
    "growth_pct": [
        "growth", "growth rate", "growth pct", "% growth",
        "1996-2021 growth", "population growth", "growth 1996-2021",
    ],
}

REQUIRED_INSTRUCTIONS = {
    "row_count": 5,
}

CANONICAL_MEASURES = {
    "colored": ["pop_2021", "growth_pct"],
    "hero_uncolored": [],
}

SEMANTIC_TYPES = {
    "n": "integer",
    "pop_1996": "integer",
    "pop_2021": "integer",
    "growth_pct": "percent",
}

# ---- Data prep -------------------------------------------------------------
df = pd.read_csv(_ROOT / "data" / "towny.csv")

df = df.dropna(subset=["density_2021", "population_1996", "population_2021"])
df["quintile"] = pd.qcut(df["density_2021"], q=5, labels=["Q1", "Q2", "Q3", "Q4", "Q5"])

by_q = (
    df.groupby("quintile", observed=True)
      .agg(
          n=("name", "count"),
          pop_1996=("population_1996", "sum"),
          pop_2021=("population_2021", "sum"),
      )
      .reset_index()
)
by_q["quintile"] = by_q["quintile"].astype(str)
by_q["growth_pct"] = (by_q["pop_2021"] - by_q["pop_1996"]) / by_q["pop_1996"]
by_q["pop_1996"] = by_q["pop_1996"].astype("int64")
by_q["pop_2021"] = by_q["pop_2021"].astype("int64")

# ---- Color domains ---------------------------------------------------------
p_lo = float(by_q["pop_2021"].min())
p_hi = float(by_q["pop_2021"].max())

g_lo = float(by_q["growth_pct"].min())
g_hi = float(by_q["growth_pct"].max())

# ---- Table -----------------------------------------------------------------
gt = (
    GT(by_q, rowname_col="quintile")
    .tab_header(
        title="Ontario Population Growth by Density Quintile, 1996-2021",
        subtitle="Ontario municipalities split into five equal-count bins by 2021 population density -- total population in 1996 and 2021, the resulting growth rate, and how many municipalities fall into each bin",
    )
    .tab_stubhead(label="Density Quintile")
    .cols_label(
        n="Municipalities",
        pop_1996="1996 Population",
        pop_2021="2021 Population",
        growth_pct=html("Growth<br>1996→2021"),
    )
    .fmt_integer(columns=["n", "pop_1996", "pop_2021"], use_seps=True)
    .fmt_percent(columns=["growth_pct"], decimals=1)
    .sub_missing(columns=["n", "pop_1996", "pop_2021", "growth_pct"], missing_text="—")
    # Big Color 1/2: 2021 population -- Blues sequential.
    .data_color(
        columns=["pop_2021"],
        palette="Blues",
        domain=[p_lo, p_hi],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    # Big Color 2/2: growth rate -- Greens sequential (all quintiles
    # grew; no diverging behavior).
    .data_color(
        columns=["growth_pct"],
        palette="Greens",
        domain=[g_lo, g_hi],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    .cols_width(cases={
        "quintile": "170px", "n": "130px",
        "pop_1996": "160px", "pop_2021": "160px", "growth_pct": "140px",
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
    .cols_align(align="right", columns=["n", "pop_1996", "pop_2021", "growth_pct"])
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    .tab_source_note(
        source_note=html(
            "Quintiles are equal-count bins of 2021 population density (pd.qcut, q=5); ~82 "
            "municipalities per bin. Growth concentrates sharply in the densest quintiles — Q5 "
            "grew 37% over the 25-year span (nearly 3 M more residents), while Q1's ~106,000 "
            "rural residents in 1996 held essentially flat at +2.0%."
        )
    )
    .tab_source_note(
        source_note=html(
            "Source: Statistics Canada Census of Population, 1996 &amp; 2021, via the "
            "<code>towny</code> dataset (Posit / great_tables sample data)."
        )
    )
)

gt.gtsave(str(_HERE / "towny_density_quintiles.png"), zoom=2.0, expand=8)
