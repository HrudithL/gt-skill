import pandas as pd
import numpy as np
from great_tables import GT, style, loc
from gt_consistency import frame, finalize, heatmap, band, stripe, stub_tint, hairlines

df = pd.read_csv("airquality.csv")

monthly = df.groupby("Month").agg({
    "Temp": "mean",
    "Wind": "mean",
    "Ozone": "mean",
}).round(1)

month_names = {5: "May", 6: "June", 7: "July", 8: "August", 9: "September"}
monthly.index = monthly.index.map(month_names)
monthly = monthly.rename(columns={"Temp": "Temperature (°F)", "Wind": "Wind Speed (mph)", "Ozone": "Ozone (ppb)"})

gt = (
    GT(monthly.reset_index().rename(columns={"Month": "Month"}))
    .cols_move_to_start(columns="Month")
    .cols_width(cases={"Month": "110px", "Temperature (°F)": "130px", "Wind Speed (mph)": "130px", "Ozone (ppb)": "110px"})
    .fmt_number(columns=["Temperature (°F)", "Wind Speed (mph)", "Ozone (ppb)"], decimals=1)
    .tab_header(
        title="Air Quality Metrics by Month",
        subtitle="Average temperature, wind speed, and ozone levels (May–September)"
    )
    .tab_spanner(
        label="Measurements",
        columns=["Temperature (°F)", "Wind Speed (mph)", "Ozone (ppb)"]
    )
)

gt = heatmap(gt, columns=["Temperature (°F)"], kind="sequential", hue="neutral")
gt = heatmap(gt, columns=["Ozone (ppb)"], kind="sequential", hue="positive")

gt = band(gt)
gt = stripe(gt)
gt = hairlines(gt)
gt = (
    gt.tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.column_labels(columns="Ozone (ppb)"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.body(columns="Ozone (ppb)"),
    )
)

gt = (
    gt.tab_options(
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
)

gt = frame(gt)

gt = (
    gt.tab_source_note(
        source_note="Temperature and ozone show the seasonal patterns in air quality, with higher ozone levels during summer months and peak temperatures in August."
    )
    .tab_source_note(
        source_note="Source: airquality.csv"
    )
)

finalize(gt)
