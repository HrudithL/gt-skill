"""Summary statistics archetype — good example.

Source: ../../data/pizzaplace.csv  (49,574 individual pizza orders)
Story:  "How did the four pizza categories perform across sizes?" — a
        store manager's monthly review. Rows are sizes grouped by
        category, each cell is an aggregate, and the table closes
        with a grand total row so the headline number is on the page.
"""
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent

import pandas as pd
from great_tables import GT, loc, style

# ---- Data prep ---------------------------------------------------------------
df = pd.read_csv(_ROOT / "data" / "pizzaplace.csv")

agg = (
    df.groupby(["type", "size"])
      .agg(orders=("id", "count"),
           revenue=("price", "sum"),
           avg_price=("price", "mean"))
      .reset_index()
)

# Order sizes consistently across all groups. Without this, pandas' default
# ordering would land on alphabetic (L, M, S, XL, XXL) which is not the
# natural size progression a human expects.
size_order = ["S", "M", "L", "XL", "XXL"]
agg["size"] = pd.Categorical(agg["size"], categories=size_order, ordered=True)

# Pretty category labels: capitalize, since the raw values are lowercase.
type_pretty = {"classic": "Classic", "veggie": "Veggie",
               "chicken": "Chicken", "supreme": "Supreme"}
agg["type"] = agg["type"].map(type_pretty)

agg = agg.sort_values(["type", "size"]).reset_index(drop=True)

# ---- Table -------------------------------------------------------------------
gt = (
    GT(agg, rowname_col="size", groupname_col="type")
    .tab_header(
        title="Pizza Sales by Category and Size",
        subtitle="Full-year totals across the four menu categories",
    )
    .cols_label(
        orders="Orders",
        revenue="Revenue",
        avg_price="Avg. price",
    )
    # Revenue and avg price as USD currency — the audience is store
    # operations, not statisticians; "$74,518.50" reads faster than
    # "74518.50".
    .fmt_currency(columns=["revenue", "avg_price"], currency="USD", decimals=2)
    # Orders as integer with thousands separator — large counts deserve the
    # grouping for readability.
    .fmt_integer(columns=["orders"])
    # Grand summary row at the bottom: total orders and total revenue across
    # every group. This is the "headline" number a manager carries away.
    # The callable receives the underlying pandas DataFrame; we return a
    # Series whose index names the columns to populate (orders, revenue).
    # avg_price is intentionally absent so the summary cell renders as the
    # `missing_text` placeholder — a mean of means is not meaningful.
    .grand_summary_rows(
        fns={"All categories": lambda d: pd.Series({
            "orders": int(d["orders"].sum()),
            "revenue": float(d["revenue"].sum()),
        })},
        missing_text="",
    )
    # Bold the group labels so the four categories visually punctuate the
    # rows. tab_style + loc.row_groups scopes the bold to the group banners
    # only, not the body cells.
    .tab_style(
        style=style.text(weight="bold"),
        locations=loc.row_groups(),
    )
    .cols_align(align="right", columns=["orders", "revenue", "avg_price"])
    .tab_source_note(
        source_note="Source: pizzaplace dataset (Posit / great_tables sample data)."
    )
)

gt.gtsave(str(_HERE / "good_table.png"), zoom=3.0)
