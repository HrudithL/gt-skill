import pandas as pd
import numpy as np
from great_tables import GT, md
from gt_consistency import heatmap, band, stripe, stub_tint, frame, finalize, PALETTE

df = pd.read_csv("airquality.csv")

monthly = df.groupby("Month").agg({
    "Temp": "mean",
    "Wind": "mean",
    "Ozone": "mean"
}).reset_index()

month_names = {
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September"
}

monthly["Month_Name"] = monthly["Month"].map(month_names)
monthly = monthly[["Month_Name", "Temp", "Wind", "Ozone"]]
monthly.columns = ["Month", "Temperature (°F)", "Wind Speed (mph)", "Ozone (ppb)"]

gt = (
    GT(monthly, rowname_col="Month")
    .fmt_number(columns=["Temperature (°F)", "Wind Speed (mph)", "Ozone (ppb)"], decimals=1)
)

gt = heatmap(gt, ["Temperature (°F)", "Wind Speed (mph)", "Ozone (ppb)"], kind="sequential", hue="neutral")
gt = band(gt, shade="light", hue="navy")
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")
gt = frame(gt)

gt = gt.tab_header(
    title="Air Quality Monthly Summary",
    subtitle="Average temperature, wind speed, and ozone levels by month"
)

gt = gt.tab_source_note(
    md("Source: New York air quality dataset")
)

finalize(gt, "table.png")
