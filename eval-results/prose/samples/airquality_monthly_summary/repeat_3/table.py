import pandas as pd
from great_tables import GT, html, loc, style

# Step 1: Load and clean data
df = pd.read_csv("airquality.csv")

# Step 2: Create monthly aggregation
month_names = {5: "May", 6: "June", 7: "July", 8: "August", 9: "September"}

monthly = df.groupby("Month").agg(
    ozone_avg=("Ozone", "mean"),
    wind_avg=("Wind", "mean"),
    temp_avg=("Temp", "mean"),
).reset_index()

monthly["month_label"] = monthly["Month"].map(month_names)
monthly = monthly[["month_label", "ozone_avg", "wind_avg", "temp_avg"]]

# Step 3-7: Build table
gt = (
    GT(monthly, rowname_col="month_label")
    .tab_header(
        title="Air Quality Summary by Month",
        subtitle="Average ozone, wind speed, and temperature (May–September 1973)",
    )
    .cols_label(
        ozone_avg=html("Ozone<br/>(ppb)"),
        wind_avg=html("Wind Speed<br/>(mph)"),
        temp_avg=html("Temperature<br/>(&deg;F)"),
    )
    .fmt_number(columns=["ozone_avg", "wind_avg", "temp_avg"], decimals=1)
    .tab_source_note(
        source_note="Source: New York State Department of Conservation, daily measurements."
    )
)

gt.gtsave("table.png")
