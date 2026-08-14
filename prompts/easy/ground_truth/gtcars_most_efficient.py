"""Ground truth for prompts/easy/gtcars_most_efficient.json.

Data: data/gtcars.csv  (47 gt-car trims: performance specs, drivetrain,
      transmission, country of origin, MSRP, and city/highway MPG).
Story: The 10 most fuel-efficient cars in the dataset, ranked by combined
       city+highway MPG, with each car's horsepower and country of origin
       — an "efficiency vs. output" tradeoff view.

Design decisions:

- Row scope: the prompt names "the 10 most" explicitly, so
  REQUIRED_INSTRUCTIONS pins row_count=10.
- Efficiency metric: `mpg_combined = (mpg_c + mpg_h) / 2`. The prompt says
  "combined city and highway MPG"; the natural definition is the mean of
  the two figures (the EPA "combined" figure is a weighted mean, but
  the raw dataset has no separate combined column, so the plain mean is
  the honest transparent choice and it's stated in the source note).
- Stub: `car` = mfr + model (matches gtcars_hp_price.py / gtcars_top10_by
  _country.py conventions; every mfr+model pair in the top 10 is unique).
- Colored measure: `mpg_combined` only — plain positive magnitude and the
  literal ranking criterion. Fuel efficiency has an inherent "more is
  better" direction, so sequential GREENS (not Blues) — matches the
  house palette's `sequential.positive` = Greens convention.
- `hp` is HERO_UNCOLORED — a secondary numeric measure the prompt names
  explicitly ("along with their horsepower"), which stays plain per the
  house rule (a hero_uncolored measure never gets bold or a fill).
- `ctry_origin` stays plain text (descriptive attribute).
- Sort: descending by mpg_combined.
- Header/stub branding: DEEP navy (#08306B) band + washed navy stub —
  branding is decoupled from the Greens heatmap hue.

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
    "mpg_combined": [
        "combined mpg", "mpg", "combined", "combined fuel economy",
        "mpg (combined)", "combined city/highway mpg", "fuel economy",
    ],
    "hp": ["hp", "horsepower", "power"],
    "ctry_origin": ["country", "country of origin", "origin", "made in"],
}

REQUIRED_INSTRUCTIONS = {
    "row_count": 10,
}

CANONICAL_MEASURES = {
    "colored": ["mpg_combined"],
    "hero_uncolored": ["hp"],
}

SEMANTIC_TYPES = {
    "mpg_combined": "number",
    "hp": "integer",
}

# ---- Data prep -------------------------------------------------------------
df = pd.read_csv(_ROOT / "data" / "gtcars.csv")

df["mpg_combined"] = (df["mpg_c"] + df["mpg_h"]) / 2
df["car"] = df["mfr"] + " " + df["model"]

top = (
    df.dropna(subset=["mpg_combined"])
    .nlargest(10, "mpg_combined")
    .loc[:, ["car", "mpg_combined", "hp", "ctry_origin"]]
    .reset_index(drop=True)
)
top["hp"] = top["hp"].astype(int)

# ---- Color domain ----------------------------------------------------------
mpg_lo = float(top["mpg_combined"].min())
mpg_hi = float(top["mpg_combined"].max())

# ---- Table -----------------------------------------------------------------
gt = (
    GT(top, rowname_col="car")
    .tab_header(
        title="The 10 Most Fuel-Efficient GT Cars",
        subtitle="Combined city/highway MPG for the most efficient cars in the gtcars dataset, with each car's horsepower and country of origin",
    )
    .tab_stubhead(label="Car")
    .cols_label(mpg_combined="Combined MPG", hp="Horsepower", ctry_origin="Country")
    .fmt_number(columns=["mpg_combined"], decimals=1)
    .fmt_integer(columns=["hp"])
    .sub_missing(columns=["mpg_combined", "hp"], missing_text="—")
    # Big Color 1/1: combined MPG -- inherent "more is better" direction,
    # so sequential GREENS (matches the house sequential.positive palette).
    .data_color(
        columns=["mpg_combined"],
        palette="Greens",
        domain=[mpg_lo, mpg_hi],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    # hp stays plain text -- hero_uncolored per the house rule (no bold,
    # no fill), matching gtcars_hp_price.py's own treatment of horsepower.
    .cols_width(cases={
        "car": "230px", "mpg_combined": "140px", "hp": "120px", "ctry_origin": "110px",
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
    .cols_align(align="right", columns=["mpg_combined", "hp"])
    .cols_align(align="left", columns=["ctry_origin"])
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    .tab_source_note(
        source_note=html(
            "Combined MPG is the mean of the dataset's city and highway figures. "
            "German engineering dominates — 9 of the 10 most efficient cars come from Germany, "
            "led by the BMW i8's hybrid drivetrain at 28.5 combined MPG."
        )
    )
    .tab_source_note(
        source_note=html(
            "Source: <code>gtcars</code> dataset (Posit / great_tables sample data), 2014-2017 model years."
        )
    )
)

gt.gtsave(str(_HERE / "gtcars_most_efficient.png"), zoom=2.0, expand=8)
