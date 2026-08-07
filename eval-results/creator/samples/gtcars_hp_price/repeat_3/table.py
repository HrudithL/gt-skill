import pandas as pd
from great_tables import GT, md
from gt_house_style import apply_house_style, add_heatmap, humanize_labels

df = pd.read_csv("gtcars.csv")

# Select relevant columns: make a display name and keep hp and msrp
df_display = df[["mfr", "model", "hp", "msrp"]].copy()
df_display["car_name"] = df["mfr"] + " " + df["model"]
df_display = df_display[["car_name", "hp", "msrp"]].reset_index(drop=True)

tbl = (
    GT(df_display)
    .tab_header(
        title="GT Cars: Horsepower and Price",
        subtitle=md("2014–2017 performance and luxury vehicles"),
    )
    .cols_label(
        car_name="Model",
        hp="Horsepower",
        msrp="Price (MSRP)",
    )
    .fmt_integer(columns="hp")
    .fmt_currency(columns="msrp", currency="USD", decimals=0)
    .sub_missing(missing_text="—")
    .tab_source_note(source_note="Source: gtcars.csv")
)

tbl = add_heatmap(tbl, df_display, "hp")
tbl = apply_house_style(tbl)

tbl.gtsave("table.png", zoom=2, expand=10)
