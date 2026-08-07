import pandas as pd
from great_tables import GT, md
from gt_house_style import apply_house_style, add_heatmap, humanize_labels

df = pd.read_csv("airquality.csv")

month_names = {
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September"
}

monthly_summary = df.groupby("Month").agg({
    "Temp": "mean",
    "Wind": "mean",
    "Ozone": "mean"
}).round(2)

monthly_summary["Month_Name"] = monthly_summary.index.map(month_names)
monthly_summary = monthly_summary[["Month_Name", "Temp", "Wind", "Ozone"]]
monthly_summary = monthly_summary.reset_index(drop=True)

tbl = (
    GT(monthly_summary)
    .tab_header(
        title="Air Quality Metrics by Month",
        subtitle=md("Average temperature, wind speed, and ozone levels across the monitoring period"),
    )
    .fmt_number(columns="Temp", decimals=1)
    .fmt_number(columns="Wind", decimals=1)
    .fmt_number(columns="Ozone", decimals=1)
    .sub_missing(missing_text="—")
    .tab_source_note(source_note="Source: air quality dataset")
)

tbl = humanize_labels(tbl, monthly_summary, overrides={
    "Month_Name": "Month",
    "Temp": "Avg Temperature (°F)",
    "Wind": "Avg Wind Speed (mph)",
    "Ozone": "Avg Ozone (ppb)"
})

tbl = add_heatmap(tbl, monthly_summary, columns=["Temp", "Wind", "Ozone"])
tbl = apply_house_style(tbl)

tbl.gtsave("table.png", zoom=2, expand=10)
