import pandas as pd
import numpy as np
from great_tables import GT, loc, style
from gt_consistency import PALETTE, frame, finalize, heatmap, band, stripe, stub_tint

df = pd.read_csv("airquality.csv")

agg = (
    df.groupby("Month")
      .agg(
          Temp=("Temp", "mean"),
          Wind=("Wind", "mean"),
          Ozone=("Ozone", "mean"),
      )
      .reset_index()
)

month_map = {
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September"
}
agg["Month"] = agg["Month"].map(month_map)

gt = (
    GT(agg, rowname_col="Month")
    .tab_header(
        title="Air Quality by Month",
        subtitle="Average temperature, wind speed, and ozone levels",
    )
    .cols_label(Temp="Temperature (°F)", Wind="Wind Speed (mph)", Ozone="Ozone (ppb)")
    .fmt_number(columns=["Temp", "Wind", "Ozone"], decimals=1)
)

gt = heatmap(gt, columns="Temp", kind="sequential", hue="neutral")
gt = heatmap(gt, columns="Wind", kind="sequential", hue="positive")
gt = band(gt, shade="light", hue="navy")
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")
gt = frame(gt)
finalize(gt, "table.png")
