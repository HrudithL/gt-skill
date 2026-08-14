"""Ground truth for prompts/easy/metro_busiest_stations.json.

Data: data/metro.csv  (Paris Métro network: one row per station, with
      the station name, its Métro lines served, and annual passenger
      count. 315 rows total; a few have no reported ridership.)
Story: The 10 busiest Métro stations by annual passenger count, with
       the Métro line(s) each one serves — a "top of the network"
       ridership leaderboard.

Design decisions:

- Row scope: the prompt names "the 10 busiest" explicitly, so
  REQUIRED_INSTRUCTIONS pins row_count=10.
- Stub: station `name`. Confirmed unique across the top 10.
- Colored measure: `passengers` only. It's the "busiest by annual
  passenger count" ranking criterion and the entire point of the table
  — a plain positive magnitude, so sequential Blues. `lines` is
  descriptive text with no magnitude or good/bad polarity, so it
  stays plain (and has no entry in SEMANTIC_TYPES since there is no
  fmt_* call for a text column).
- Sort: descending by passengers (matches "top 10 busiest").
- No grouping or spanner: the prompt names no organizing category.
- Header/stub branding: DEEP navy (#08306B) band + washed navy stub —
  the universal branding.

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
    "lines": ["lines", "metro lines", "métro lines", "line(s)", "lines served", "metro"],
    "passengers": [
        "passengers", "annual passengers", "annual ridership",
        "ridership", "passenger count", "annual passenger count",
    ],
}

# "The 10" is explicit in the prompt.
REQUIRED_INSTRUCTIONS = {
    "row_count": 10,
}

CANONICAL_MEASURES = {
    "colored": ["passengers"],
    "hero_uncolored": [],
}

# Only fmt_*-formatted columns belong here; `lines` is plain text.
SEMANTIC_TYPES = {
    "passengers": "integer",
}

# ---- Data prep -------------------------------------------------------------
df = pd.read_csv(_ROOT / "data" / "metro.csv")

# A handful of stations report no ridership (NaN); nlargest skips NaN by
# default, but drop them explicitly so the row count is unambiguous.
top = (
    df.dropna(subset=["passengers"])
      .nlargest(10, "passengers")
      .loc[:, ["name", "lines", "passengers"]]
      .reset_index(drop=True)
)
top["passengers"] = top["passengers"].astype(int)

# ---- Color domain ----------------------------------------------------------
pax_lo = float(top["passengers"].min())
pax_hi = float(top["passengers"].max())

# ---- Table -----------------------------------------------------------------
gt = (
    GT(top, rowname_col="name")
    .tab_header(
        title="Paris Métro's Busiest Stations",
        subtitle="Annual passenger counts for the 10 highest-ridership stations, with the Métro lines each one serves",
    )
    .tab_stubhead(label="Station")
    .cols_label(lines="Métro Lines", passengers="Annual Passengers")
    .fmt_integer(columns=["passengers"], use_seps=True)
    .sub_missing(columns=["passengers"], missing_text="—")
    # Big Color 1/1: annual passengers -- the "busiest" ranking hero,
    # plain positive magnitude -> sequential Blues.
    .data_color(
        columns=["passengers"],
        palette="Blues",
        domain=[pax_lo, pax_hi],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    .cols_width(cases={"name": "230px", "lines": "140px", "passengers": "160px"})
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
    .cols_align(align="right", columns=["lines", "passengers"])
    # 10 rows, only passengers colored -- body not fully covered, so grey
    # zebra striping is added across both columns.
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    .tab_source_note(
        source_note=html(
            "Mainline-rail terminals dominate the leaderboard — Gare du Nord, Saint-Lazare, "
            "Gare de Lyon, Montparnasse–Bienvenüe, and Gare de l'Est claim the top five spots; "
            "the first non-terminal station, République, ranks sixth."
        )
    )
    .tab_source_note(
        source_note=html(
            "Source: Paris Métro (RATP) network dataset — annual passenger counts per station."
        )
    )
)

gt.gtsave(str(_HERE / "metro_busiest_stations.png"), zoom=2.0, expand=8)
