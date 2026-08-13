"""Ground truth for prompts/easy/pizzaplace_top_pizzas.json.

Data: data/pizzaplace.csv  (49,574 individual pizza sales across the
      full 2015 calendar year at one hypothetical pizzeria; one row per
      pizza sold, with `name` = the specific pizza variety code such as
      `thai_ckn`/`bbq_ckn`, `size`, `type` [classic/veggie/chicken/
      supreme], and `price`).
Story: The ten best-selling pizzas of the year by TOTAL REVENUE, with
       how many of each were ordered — a menu-performance leaderboard.

Design decisions:

- Row scope: the prompt names "the ten" explicitly, so REQUIRED_
  INSTRUCTIONS pins row_count=10.
- Stub: the pizza's human-readable name. The raw `name` field is a
  code (`thai_ckn`), useless in a display table; a small hand map turns
  it into the actual menu name ("The Thai Chicken Pizza"). No composite
  key is needed — `name` alone identifies a pizza uniquely across all
  sizes/dates, since we aggregate over both.
- Colored measure: revenue only. It's the "best-selling by total
  revenue" hero — the literal ranking criterion — and financial magnitudes
  are the archetypal sequential Blues heatmap subject. Order count stays
  plain (hero_uncolored) — a secondary detail the prompt asks for
  ("along with how many were ordered") but doesn't make the hero of.
- Sort: descending by revenue (matches the "top 10 by revenue" framing).
- No grouping or spanner: the prompt names no organizing category.
- Header/stub branding: DEEP navy (#08306B) band + washed navy stub —
  the same universal branding every table in this project uses.

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
    "revenue": ["revenue", "total revenue", "sales", "total sales", "total"],
    "orders": ["orders", "order count", "number ordered", "units", "quantity", "sold", "count"],
}

# "The ten" is an explicit row count in the prompt.
REQUIRED_INSTRUCTIONS = {
    "row_count": 10,
}

CANONICAL_MEASURES = {
    "colored": ["revenue"],
    "hero_uncolored": ["orders"],
}

SEMANTIC_TYPES = {
    "revenue": "currency",
    "orders": "integer",
}

# ---- Data prep -------------------------------------------------------------
df = pd.read_csv(_ROOT / "data" / "pizzaplace.csv")

# The raw menu code (`thai_ckn`) is not a display string. Small hand map to
# the actual on-menu name; the aggregate below then keys on the humanized
# label so the stub reads like a menu, not a database row.
PIZZA_NAMES = {
    "thai_ckn":    "The Thai Chicken Pizza",
    "bbq_ckn":     "The Barbecue Chicken Pizza",
    "cali_ckn":    "The California Chicken Pizza",
    "classic_dlx": "The Classic Deluxe Pizza",
    "spicy_ital":  "The Spicy Italian Pizza",
    "southw_ckn":  "The Southwest Chicken Pizza",
    "ital_supr":   "The Italian Supreme Pizza",
    "hawaiian":    "The Hawaiian Pizza",
    "four_cheese": "The Four Cheese Pizza",
    "sicilian":    "The Sicilian Pizza",
}

by_pizza = (
    df.groupby("name")
      .agg(orders=("id", "count"), revenue=("price", "sum"))
      .sort_values("revenue", ascending=False)
      .head(10)
      .reset_index()
)
by_pizza["pizza"] = by_pizza["name"].map(PIZZA_NAMES).fillna(by_pizza["name"])
by_pizza = by_pizza[["pizza", "revenue", "orders"]].reset_index(drop=True)

# ---- Color domain ----------------------------------------------------------
rev_lo = float(by_pizza["revenue"].min())
rev_hi = float(by_pizza["revenue"].max())

# ---- Table -----------------------------------------------------------------
gt = (
    GT(by_pizza, rowname_col="pizza")
    .tab_header(
        title="Best-Selling Pizzas of 2015, by Revenue",
        subtitle="Total sales and units ordered for the ten highest-grossing pizzas across the full year",
    )
    .tab_stubhead(label="Pizza")
    .cols_label(revenue="Total Revenue", orders="Pizzas Ordered")
    .fmt_currency(columns=["revenue"], decimals=2)
    .fmt_integer(columns=["orders"])
    .sub_missing(columns=["revenue", "orders"], missing_text="—")
    # Big Color 1/1: revenue — the "by total revenue" ranking hero, plain
    # positive magnitude -> sequential Blues.
    .data_color(
        columns=["revenue"],
        palette="Blues",
        domain=[rev_lo, rev_hi],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    # Orders stays plain -- a secondary count, not a hero.
    .cols_width(cases={"pizza": "270px", "revenue": "150px", "orders": "130px"})
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
    .cols_align(align="right", columns=["revenue", "orders"])
    # 10 rows, only revenue colored (orders is plain) -- body nowhere near
    # fully covered, so grey zebra striping is added.
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    .tab_source_note(
        source_note=html(
            "The chicken specialties dominate the top three spots — the Thai, Barbecue, and California "
            "Chicken pizzas together account for over $127,000 in revenue, well ahead of every classic."
        )
    )
    .tab_source_note(
        source_note=html(
            "Source: <code>pizzaplace</code> dataset — 49,574 pizza sales, calendar year 2015 "
            "(Posit / great_tables sample data)."
        )
    )
)

gt.gtsave(str(_HERE / "pizzaplace_top_pizzas.png"), zoom=2.0, expand=8)
