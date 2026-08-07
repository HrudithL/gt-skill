import pandas as pd
from great_tables import GT

df = pd.read_csv("gtcars.csv")

df_display = df[["mfr", "model", "hp", "msrp"]].copy()
df_display.columns = ["Manufacturer", "Model", "Horsepower", "Price"]
df_display = df_display.sort_values("Horsepower", ascending=False).reset_index(drop=True)

gt = (
    GT(df_display)
    .tab_header(
        title="GT Cars: Horsepower and Price",
        subtitle="Performance vehicles ranked by horsepower"
    )
    .cols_label(
        Horsepower="Horsepower (hp)",
        Price="Price ($)"
    )
    .fmt_number(
        columns=["Horsepower"],
        decimals=0
    )
    .fmt_currency(
        columns=["Price"],
        currency="USD",
        decimals=0
    )
    .data_color(
        columns=["Horsepower"],
        domain=[df_display["Horsepower"].min(), df_display["Horsepower"].max()],
        palette="viridis"
    )
    .data_color(
        columns=["Price"],
        domain=[df_display["Price"].min(), df_display["Price"].max()],
        palette="plasma"
    )
    .tab_source_note("Source: GT Cars Dataset")
)

gt.gtsave("table.png")
