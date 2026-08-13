import pandas as pd
import numpy as np
from great_tables import GT, style, loc
from gt_consistency import heatmap, band, stripe, stub_tint, frame, finalize, PALETTE

df = pd.read_csv("airquality.csv")

df["Temp"] = pd.to_numeric(df["Temp"], errors="coerce")
df["Wind"] = pd.to_numeric(df["Wind"], errors="coerce")
df["Ozone"] = pd.to_numeric(df["Ozone"], errors="coerce")

monthly = df.groupby("Month").agg({
    "Temp": "mean",
    "Wind": "mean",
    "Ozone": "mean"
}).reset_index()

monthly = monthly.rename(columns={
    "Month": "Month",
    "Temp": "Avg Temp (°F)",
    "Wind": "Avg Wind (mph)",
    "Ozone": "Avg Ozone (ppb)"
})

month_names = {
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September"
}
monthly["Month"] = monthly["Month"].map(month_names)

gt = (
    GT(monthly, rowname_col="Month")
    .fmt_number(columns=["Avg Temp (°F)", "Avg Wind (mph)", "Avg Ozone (ppb)"], decimals=1)
    .sub_missing(columns=["Avg Temp (°F)", "Avg Wind (mph)", "Avg Ozone (ppb)"], missing_text="—")
)

gt = heatmap(gt, "Avg Temp (°F)", kind="sequential", hue="neutral")
gt = heatmap(gt, "Avg Ozone (ppb)", kind="sequential", hue="positive")

gt = (
    gt
    .tab_header(
        title="Air Quality Monthly Summary",
        subtitle="Average temperature, wind speed, and ozone levels by month"
    )
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    .cols_width(cases={
        "Month": "90px",
        "Avg Temp (°F)": "120px",
        "Avg Wind (mph)": "120px",
        "Avg Ozone (ppb)": "120px"
    })
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
)

gt = band(gt)
gt = stripe(gt)
gt = stub_tint(gt)

gt = (
    gt
    .tab_source_note(source_note="Temperature and ozone levels are heatmap-colored to highlight seasonal patterns and variation; wind speed is shown as reference.")
    .tab_source_note(source_note="Source: airquality.csv (R built-in dataset, May–September 1973)")
)

gt = frame(gt)
gt.gtsave("table.png", expand=15, zoom=2.0)
