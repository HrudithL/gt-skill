"""Ground truth for prompts/hard/pizzaplace_daypart_by_category.json.

Data: data/pizzaplace.csv  (49,574 individual pizza sales across 2015 at
      one hypothetical pizzeria; one row per pizza sold, with `time`,
      `type` in {classic, chicken, supreme, veggie}, and `price`).
Story: A two-level demand cross-tab -- for every combination of day-part
       (Morning / Lunch / Afternoon / Dinner) and pizza category
       (Classic / Chicken / Supreme / Veggie), total revenue, order
       count, and average order value.

Design decisions:

- Day-part definition: hour of order (from the `time` column) binned
  into four buckets:
    Morning   = hour < 11        (open, breakfast, brunch)
    Lunch     = 11 <= hour < 14
    Afternoon = 14 <= hour < 17
    Dinner    = 17 <= hour       (evening)
  These are the transparent thresholds stated in the analytical caption
  note so the same prompt always yields the same 4x4 = 16 rows.
- Row scope: 4 dayparts x 4 categories = 16 rows. REQUIRED_INSTRUCTIONS
  pins row_count=16 and grouping=True (grouped by daypart).
- Stub: pizza category (`type` humanized).
- Group: `daypart` (Morning -> Lunch -> Afternoon -> Dinner, ordered
  chronologically across the business day, matching the natural
  reading of a "when do people order what" cross-tab).
- Colored measures (two, distinct families):
  * `revenue`: sequential Blues -- the "sales performance" hero and
    the currency measure.
  * `orders`: sequential Greens -- a count magnitude; distinct hue
    from revenue to avoid a same-family collision. Revenue and orders
    correlate strongly (a busier daypart has more of both), so pairing
    two distinct heatmaps makes the two dimensions of "busy" both
    legible without one dominating.
  `avg_order` stays plain -- a per-order figure that swings little
  across categories/dayparts (a tighter, less-heatmap-worthy range).
- Sort: within-group by revenue descending (the "top-selling category
  within this daypart first" reading, matching the same within-group
  convention gtcars_top10_by_country.py uses).
- Header/stub branding: DEEP navy (#08306B) band + washed navy stub +
  group_emphasis pattern (bold weight + structural rule, no fill).

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
    "revenue": ["revenue", "total revenue", "sales", "total sales"],
    "orders": ["orders", "order count", "count", "number of orders", "pizzas ordered"],
    "avg_order": [
        "avg order", "average order", "avg. order", "avg order value",
        "avg. order value", "mean order value", "avg price",
    ],
}

REQUIRED_INSTRUCTIONS = {
    "row_count": 16,
    "grouping": True,
    "sort": ("revenue", "desc", "within_group"),
}

CANONICAL_MEASURES = {
    "colored": ["revenue", "orders"],
    "hero_uncolored": ["avg_order"],
}

SEMANTIC_TYPES = {
    "revenue": "currency",
    "orders": "integer",
    "avg_order": "currency",
}

# ---- Data prep -------------------------------------------------------------
df = pd.read_csv(_ROOT / "data" / "pizzaplace.csv")
df["hour"] = pd.to_datetime(df["time"], format="%H:%M:%S").dt.hour


def _daypart(h):
    if h < 11:
        return "Morning"
    if h < 14:
        return "Lunch"
    if h < 17:
        return "Afternoon"
    return "Dinner"


df["daypart"] = df["hour"].map(_daypart)

CATEGORY_LABELS = {
    "classic": "Classic",
    "chicken": "Chicken",
    "supreme": "Supreme",
    "veggie":  "Veggie",
}
df["category"] = df["type"].map(CATEGORY_LABELS).fillna(df["type"])

agg = (
    df.groupby(["daypart", "category"])
      .agg(revenue=("price", "sum"), orders=("id", "count"), avg_order=("price", "mean"))
      .reset_index()
)

DAYPART_ORDER = ["Morning", "Lunch", "Afternoon", "Dinner"]
agg["daypart"] = pd.Categorical(agg["daypart"], categories=DAYPART_ORDER, ordered=True)

# Sort within group by revenue descending -- "top-selling category first"
# within each daypart.
agg = agg.sort_values(["daypart", "revenue"], ascending=[True, False]).reset_index(drop=True)
agg["daypart"] = agg["daypart"].astype(str)

# ---- Color domains ---------------------------------------------------------
rev_lo = float(agg["revenue"].min())
rev_hi = float(agg["revenue"].max())

ord_lo = float(agg["orders"].min())
ord_hi = float(agg["orders"].max())

# ---- Table -----------------------------------------------------------------
gt = (
    GT(agg, rowname_col="category", groupname_col="daypart")
    .tab_header(
        title="Pizza Demand by Day-Part and Category, 2015",
        subtitle="Total revenue, order count, and average order value for every combination of day-part and pizza category across the full year",
    )
    .tab_stubhead(label="Category")
    .cols_label(revenue="Revenue", orders="Orders", avg_order="Avg. Order")
    .fmt_currency(columns=["revenue", "avg_order"], decimals=2)
    .fmt_integer(columns=["orders"], use_seps=True)
    .sub_missing(columns=["revenue", "orders", "avg_order"], missing_text="—")
    # Big Color 1/2: revenue -- Blues sequential.
    .data_color(
        columns=["revenue"],
        palette="Blues",
        domain=[rev_lo, rev_hi],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    # Big Color 2/2: orders -- Greens sequential (distinct hue family
    # from revenue Blues to avoid a same-family collision).
    .data_color(
        columns=["orders"],
        palette="Greens",
        domain=[ord_lo, ord_hi],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    .cols_width(cases={
        "category": "150px", "revenue": "150px",
        "orders": "130px", "avg_order": "130px",
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
        # group_emphasis: bold weight + structural rule above/below each
        # daypart's header row, deliberately NO background fill (matches
        # sp500_monthly_performance.py's year-group treatment).
        row_group_font_weight="bold",
        row_group_border_top_color="#BDBDBD",
        row_group_border_bottom_color="#BDBDBD",
        row_group_padding="6px",
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    .tab_style(style=style.text(color="white"), locations=loc.column_labels())
    .tab_style(style=style.fill(color="#EAF0F6"), locations=loc.stub())
    .cols_align(align="right", columns=["revenue", "orders", "avg_order"])
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    .tab_source_note(
        source_note=html(
            "Day-parts are defined by hour of order: Morning &lt; 11h, Lunch 11-14h, "
            "Afternoon 14-17h, Dinner &ge; 17h. Dinner is the busiest slot by a wide margin "
            "(~$372K, ~22.5K orders), while Morning barely registers (~$387 across 22 orders) -- "
            "the shop isn't really open for breakfast. Category rank holds across every "
            "day-part: Classic first on volume, Chicken first on average order value."
        )
    )
    .tab_source_note(
        source_note=html(
            "Source: <code>pizzaplace</code> dataset -- 49,574 pizza sales, calendar year 2015 "
            "(Posit / great_tables sample data)."
        )
    )
)

gt.gtsave(str(_HERE / "pizzaplace_daypart_by_category.png"), zoom=2.0, expand=8)
