"""Ground truth for prompts/easy/countrypops_most_populous_2021.json.

Data: data/countrypops.csv  (annual population figures, 1960-2022, for
      every country in the World Bank series; one row per (country, year)).
Story: The 15 most populous countries as of 2021, ranked by that year's
       population — a "state of the world" snapshot.

Design decisions:

- Row scope: the prompt names "the 15 most populous" explicitly, so
  REQUIRED_INSTRUCTIONS pins row_count=15.
- Stub: `country_name` (unique across the 2021 slice).
- Colored measure: `population` only — plain positive magnitude and the
  literal ranking criterion -> sequential Blues.
- Sort: descending by population.
- Header/stub branding: DEEP navy (#08306B) band + washed navy stub.

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
    "population": [
        "population", "2021 population", "population 2021", "people", "residents",
        "population (2021)",
    ],
}

REQUIRED_INSTRUCTIONS = {
    "row_count": 15,
}

CANONICAL_MEASURES = {
    "colored": ["population"],
    "hero_uncolored": [],
}

SEMANTIC_TYPES = {
    "population": "integer",
}

# ---- Data prep -------------------------------------------------------------
df = pd.read_csv(_ROOT / "data" / "countrypops.csv")

top = (
    df[df["year"] == 2021]
    .dropna(subset=["population"])
    .nlargest(15, "population")
    .loc[:, ["country_name", "population"]]
    .reset_index(drop=True)
)
top["population"] = top["population"].astype("int64")

# ---- Color domain ----------------------------------------------------------
pop_lo = float(top["population"].min())
pop_hi = float(top["population"].max())

# ---- Table -----------------------------------------------------------------
gt = (
    GT(top, rowname_col="country_name")
    .tab_header(
        title="The World's 15 Most Populous Countries in 2021",
        subtitle="Total population as of 2021, ranked from largest to smallest",
    )
    .tab_stubhead(label="Country")
    .cols_label(population="2021 Population")
    .fmt_integer(columns=["population"], use_seps=True)
    .sub_missing(columns=["population"], missing_text="—")
    .data_color(
        columns=["population"],
        palette="Blues",
        domain=[pop_lo, pop_hi],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    .cols_width(cases={"country_name": "230px", "population": "180px"})
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
    .cols_align(align="right", columns=["population"])
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    .tab_source_note(
        source_note=html(
            "China and India together account for over 2.8 billion people — roughly 36% of the "
            "world's 2021 population, and more than the next six countries on this list combined."
        )
    )
    .tab_source_note(
        source_note=html(
            "Source: <code>countrypops</code> dataset — annual country population estimates "
            "from the World Bank (Posit / great_tables sample data)."
        )
    )
)

gt.gtsave(str(_HERE / "countrypops_most_populous_2021.png"), zoom=2.0, expand=8)
