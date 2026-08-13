import pandas as pd
import numpy as np
from great_tables import GT, md
from house_table import (
    PALETTE, frame, hairlines, finalize, band, stripe, stub_tint,
    heatmap, humanize_labels
)

df = pd.read_csv("airquality.csv")

monthly_summary = df.groupby("Month").agg({
    "Temp": "mean",
    "Wind": "mean",
    "Ozone": "mean"
}).reset_index()

monthly_summary = monthly_summary.round(1)

month_names = {
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September"
}
monthly_summary["Month"] = monthly_summary["Month"].map(month_names)

gt = (
    GT(monthly_summary, rowname_col="Month")
    .tab_header(
        title="Air Quality Metrics by Month",
        subtitle=md("Average temperature, wind speed, and ozone levels across summer months")
    )
    .tab_stubhead(label="Month")
    .fmt_number(columns="Temp", decimals=1)
    .fmt_number(columns="Wind", decimals=1)
    .fmt_number(columns="Ozone", decimals=1)
)

gt = humanize_labels(
    gt,
    monthly_summary,
    overrides={"Temp": "Avg Temperature (°F)", "Wind": "Avg Wind Speed", "Ozone": "Avg Ozone"}
)

gt = gt.cols_width(
    cases={
        "Month": "120px",
        "Temp": "140px",
        "Wind": "140px",
        "Ozone": "120px",
    }
)

gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

gt = heatmap(gt, ["Temp", "Wind", "Ozone"], kind="sequential", hue="neutral")

gt = band(gt, hue="navy")
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

gt = (
    gt.tab_source_note(
        source_note="Averages computed from daily measurements during the summer season."
    )
    .tab_source_note(
        source_note="Source: New York State air quality dataset."
    )
)

gt = hairlines(gt)
gt = frame(gt)
finalize(gt)
