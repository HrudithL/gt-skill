import pandas as pd
import numpy as np
from great_tables import GT, md, loc, style

# Step 1: Read and clean the data
df = pd.read_csv("gtcars.csv")

# Create a composite identifier for the stub (manufacturer + model)
df["car"] = df["mfr"] + " " + df["model"]

# Select only the columns we need and reorder
df = df[["car", "hp", "msrp"]].copy()
df.columns = ["car", "hp", "price"]

# Ensure numeric columns are properly typed
df["hp"] = pd.to_numeric(df["hp"], errors="coerce")
df["price"] = pd.to_numeric(df["price"], errors="coerce")

# Step 3: Big Color - horsepower and price both qualify (ordered magnitude, ≥5 rows)
# They are the core of the request. Rank: "horsepower and price" → both in prompt order.
# hp is explicitly mentioned first, price second. Both earn fills.
# hp: neutral magnitude → Blues
# price: money/financial → use Greens
hp_min = float(np.nanmin(df[["hp"]].to_numpy()))
hp_max = float(np.nanmax(df[["hp"]].to_numpy()))
price_min = float(np.nanmin(df[["price"]].to_numpy()))
price_max = float(np.nanmax(df[["price"]].to_numpy()))

# Step 2: Organize columns - create GT with car as stub
gt = (
    GT(df, rowname_col="car")
    .fmt_number(columns="hp", decimals=0, use_seps=False)
    .fmt_currency(columns="price", decimals=0, currency="USD")
    .data_color(
        columns="hp",
        palette="Blues",
        domain=[hp_min, hp_max],
        truncate=False,
        na_color="#808080",
    )
    .data_color(
        columns="price",
        palette="Greens",
        domain=[price_min, price_max],
        truncate=False,
        na_color="#808080",
    )
    # Step 4: Heading band
    .tab_header(
        title="GT Cars: Horsepower and Price",
        subtitle="Performance specifications and market prices",
    )
    # Step 5: Small Color polish
    # (a) Cell hairlines between rows
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
    )
    # (c) Striping - apply by default
    .opt_row_striping()
    # (d) Stub tint - the stub exists, so apply the pale blue tint
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # (e) Footer - caption + source note (table has >5 rows, so both required)
    .tab_source_note(
        source_note="Horsepower (HP) and price (USD) are key performance and market indicators for these vehicles.",
    )
    .tab_source_note(
        source_note="Data source: gtcars.csv",
    )
    # (f) Frame - boxed border on all four sides
    .tab_options(
        table_border_top_style="solid",
        table_border_top_color="#CCCCCC",
        table_border_top_width="1px",
        table_border_bottom_style="solid",
        table_border_bottom_color="#CCCCCC",
        table_border_bottom_width="1px",
        table_border_left_style="solid",
        table_border_left_color="#CCCCCC",
        table_border_left_width="1px",
        table_border_right_style="solid",
        table_border_right_color="#CCCCCC",
        table_border_right_width="1px",
    )
)

# Step 7: Render
gt.gtsave("table.png")
