"""Ground truth for prompts/medium/pizzaplace_category_performance.json.

Data: data/pizzaplace.csv  (49,574 individual pizza sales across 2015 at
      one hypothetical pizzeria; one row per pizza sold, with `type` in
      {classic, chicken, supreme, veggie} identifying the category).
Story: Sales performance broken out by the four pizza categories --
       total revenue, order count, and average price for each.

Design decisions:

- Row scope: no explicit row count in the prompt; the data happens to
  have exactly 4 categories. REQUIRED_INSTRUCTIONS is empty rather than
  set to row_count=4 -- the count is a data property, not a prompt demand.
- Stub: `type` (category label). Uniqueness by definition.
- Colored measure: revenue -- the "performance" hero and the ranking
  criterion, plain positive magnitude -> sequential Blues.
- Hero_uncolored: orders + avg_price. Both are numeric measures the
  prompt names explicitly but neither is the color hero, so they render
  plain (per the house "hero_uncolored measures stay plain" rule).
- Sort: descending by revenue.
- Header/stub branding: DEEP navy (#08306B) band + washed navy stub.

No summary row: `grand_summary_rows()` in great_tables 0.22.0 doesn't
support `columns=` (raises NotImplementedError), and the totals across
a 4-row table this small are trivially readable from the body itself
anyway.

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
    "type": ["type", "category", "pizza type", "pizza category"],
    "revenue": ["revenue", "total revenue", "sales", "total sales"],
    "orders": ["orders", "order count", "number of orders", "count", "pizzas sold"],
    "avg_price": ["avg price", "average price", "avg. price", "mean price", "price"],
}

# The prompt names no explicit row count — 4 categories is a property of
# the data, not something the prompt demanded.
REQUIRED_INSTRUCTIONS = {}

CANONICAL_MEASURES = {
    "colored": ["revenue"],
    "hero_uncolored": ["orders", "avg_price"],
}

SEMANTIC_TYPES = {
    "revenue": "currency",
    "orders": "integer",
    "avg_price": "currency",
}

# ---- Data prep -------------------------------------------------------------
df = pd.read_csv(_ROOT / "data" / "pizzaplace.csv")

CATEGORY_LABELS = {
    "classic": "Classic",
    "chicken": "Chicken",
    "supreme": "Supreme",
    "veggie":  "Veggie",
}

by_cat = (
    df.groupby("type")
      .agg(orders=("id", "count"), revenue=("price", "sum"), avg_price=("price", "mean"))
      .sort_values("revenue", ascending=False)
      .reset_index()
)
by_cat["type"] = by_cat["type"].map(CATEGORY_LABELS).fillna(by_cat["type"])

total_orders = int(df.shape[0])
total_revenue = float(df["price"].sum())

# ---- Color domain ----------------------------------------------------------
rev_lo = float(by_cat["revenue"].min())
rev_hi = float(by_cat["revenue"].max())

# ---- Table -----------------------------------------------------------------
gt = (
    GT(by_cat, rowname_col="type")
    .tab_header(
        title="2015 Pizza Sales by Category",
        subtitle="Total revenue, order count, and average price for each of the four pizza categories",
    )
    .tab_stubhead(label="Category")
    .cols_label(revenue="Total Revenue", orders="Orders", avg_price="Avg. Price")
    .fmt_currency(columns=["revenue", "avg_price"], decimals=2)
    .fmt_integer(columns=["orders"], use_seps=True)
    .sub_missing(columns=["revenue", "orders", "avg_price"], missing_text="—")
    .data_color(
        columns=["revenue"],
        palette="Blues",
        domain=[rev_lo, rev_hi],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    .cols_width(cases={
        "type": "140px", "revenue": "160px", "orders": "130px", "avg_price": "130px",
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
    .cols_align(align="right", columns=["revenue", "orders", "avg_price"])
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    .tab_source_note(
        source_note=html(
            "Classic pizzas lead on both revenue and order count, but the Chicken category has "
            "the highest average price ($17.73) — chicken specialties skew toward larger sizes."
        )
    )
    .tab_source_note(
        source_note=html(
            "Source: <code>pizzaplace</code> dataset — 49,574 pizza sales, calendar year 2015 "
            "(Posit / great_tables sample data)."
        )
    )
)

gt.gtsave(str(_HERE / "pizzaplace_category_performance.png"), zoom=2.0, expand=8)
