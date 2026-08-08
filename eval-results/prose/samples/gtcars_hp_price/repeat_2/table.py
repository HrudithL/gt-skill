import pandas as pd
import numpy as np
from great_tables import GT

df = pd.read_csv("gtcars.csv")

df = df[["mfr", "model", "hp", "msrp"]].copy()
df.columns = ["Manufacturer", "Model", "Horsepower", "Price"]

df = df.sort_values("Price", ascending=False).reset_index(drop=True)

hp_min = float(np.nanmin(df["Horsepower"].to_numpy()))
hp_max = float(np.nanmax(df["Horsepower"].to_numpy()))
price_min = float(np.nanmin(df["Price"].to_numpy()))
price_max = float(np.nanmax(df["Price"].to_numpy()))

gt = (
    GT(df)
    .fmt_integer(columns="Horsepower")
    .fmt_currency(columns="Price", currency="USD", decimals=0)
    .data_color(
        columns="Horsepower",
        palette="Blues",
        domain=[hp_min, hp_max],
        truncate=False,
        na_color="#808080",
    )
    .data_color(
        columns="Price",
        palette="Greens",
        domain=[price_min, price_max],
        truncate=False,
        na_color="#808080",
    )
    .tab_options(
        heading_background_color="#EAF0F6",
        column_labels_background_color="#EAF0F6",
        table_border_top_style="solid",
        table_border_top_color="#CCCCCC",
        table_border_top_width="2px",
        table_border_bottom_style="solid",
        table_border_bottom_color="#CCCCCC",
        table_border_bottom_width="2px",
    )
    .tab_header(
        title="GT Cars: Horsepower & Price",
        subtitle="Performance and pricing comparison for high-performance vehicles"
    )
)

gt.gtsave("table.png")
