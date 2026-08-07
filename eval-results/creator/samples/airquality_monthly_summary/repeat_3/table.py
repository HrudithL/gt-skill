import pandas as pd
from great_tables import GT, md
from gt_house_style import apply_house_style, add_heatmap, humanize_labels

df = pd.read_csv("airquality.csv")

monthly_agg = df.groupby("Month").agg({
    "Temp": "mean",
    "Wind": "mean",
    "Ozone": "mean",
}).reset_index()

monthly_agg.columns = ["Month", "temp", "wind", "ozone"]

month_names = {
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
}

monthly_agg["Month"] = monthly_agg["Month"].map(month_names)

tbl = (
    GT(monthly_agg)
    .tab_header(
        title="Monthly Air Quality Metrics",
        subtitle=md("Average temperature, wind speed, and ozone levels by month"),
    )
    .fmt_number(columns="temp", decimals=1)
    .fmt_number(columns="wind", decimals=2)
    .fmt_number(columns="ozone", decimals=2)
    .sub_missing(missing_text="—")
)

tbl = humanize_labels(tbl, monthly_agg, overrides={
    "temp": "Avg Temperature (°F)",
    "wind": "Avg Wind Speed (mph)",
    "ozone": "Avg Ozone (ppb)",
})

tbl = add_heatmap(tbl, monthly_agg, ["temp", "wind", "ozone"])
tbl = apply_house_style(tbl)

tbl.gtsave("table.png", zoom=2, expand=10)
