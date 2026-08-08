import pandas as pd
import numpy as np
from great_tables import GT, md
from gt_consistency import PALETTE, frame, finalize, band, stripe, stub_tint, heatmap

# Load and clean the data
df = pd.read_csv("airquality.csv")

# Map month numbers to month names
month_names = {5: "May", 6: "June", 7: "July", 8: "August", 9: "September"}
df["Month"] = df["Month"].map(month_names)

# Calculate monthly averages
monthly = df.groupby("Month", as_index=False)[["Ozone", "Wind", "Temp"]].mean()

# Round to 1 decimal place
monthly = monthly.round(1)

# Reorder months in calendar order
month_order = ["May", "June", "July", "August", "September"]
monthly["Month"] = pd.Categorical(monthly["Month"], categories=month_order, ordered=True)
monthly = monthly.sort_values("Month").reset_index(drop=True)

# Create the table with Month as stub
gt = (
    GT(monthly, rowname_col="Month")
    .fmt_number(columns=["Ozone", "Wind", "Temp"], decimals=1)
)

# Apply colors to the two main measures
# Priority: Ozone (air quality metric) and Temp (environmental factor)
# Wind is shown uncolored for reference
gt = heatmap(gt, "Ozone", kind="sequential", hue="neutral")
gt = heatmap(gt, "Temp", kind="sequential", hue="positive")

# Apply light heading band (because we have colored measures)
gt = band(gt, shade="light", hue="navy")

# Apply small-color polish
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")
gt = frame(gt)

# Add titles and annotations
gt = gt.tab_header(
    title="Air Quality by Month",
    subtitle="Average monthly temperature, wind speed, and ozone levels"
)

gt = gt.tab_source_note(
    "Source: New York air quality measurements (May–September 1973)"
)

finalize(gt, "table.png")
