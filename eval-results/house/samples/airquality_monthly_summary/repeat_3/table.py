import pandas as pd
from great_tables import GT, md, style, loc
from house_table import PALETTE, frame, finalize, band, stripe, stub_tint, heatmap, humanize_labels

# Load and aggregate data by month
df = pd.read_csv("airquality.csv")

# Map month numbers to names for display
month_names = {5: "May", 6: "June", 7: "July", 8: "August", 9: "September"}
df["Month_Name"] = df["Month"].map(month_names)

# Calculate monthly averages
monthly = df.groupby("Month_Name")[["Temp", "Wind", "Ozone"]].mean().reset_index()

# Reorder to calendar order
month_order = ["May", "June", "July", "August", "September"]
monthly["Month_Name"] = pd.Categorical(monthly["Month_Name"], categories=month_order, ordered=True)
monthly = monthly.sort_values("Month_Name").reset_index(drop=True)

# Round to 1 decimal place for display
monthly["Temp"] = monthly["Temp"].round(1)
monthly["Wind"] = monthly["Wind"].round(1)
monthly["Ozone"] = monthly["Ozone"].round(1)

# Build the table
gt = GT(monthly, rowname_col="Month_Name")
gt = gt.tab_header(
    title="Air Quality Monthly Summary",
    subtitle=md("Average temperature, wind speed, and ozone levels by month"),
)
gt = gt.tab_stubhead(label="Month")

# Format numeric columns
gt = gt.fmt_number(columns=["Temp", "Wind", "Ozone"], decimals=1)

# Apply humanize_labels for column headers
gt = humanize_labels(
    gt,
    monthly,
    overrides={"Temp": "Temperature (°F)", "Wind": "Wind Speed (mph)", "Ozone": "Ozone (ppb)"},
)

# Apply heatmap coloring: Temperature is sequential (warmer is more intense)
gt = heatmap(gt, "Temp", kind="sequential", hue="warning")

# Add band styling with warm color to match temperature theme
gt = band(gt, hue="oxblood")

# Stub tint to harmonize with temperature theme
gt = stub_tint(gt, hue="oxblood")

# Add source note
gt = gt.tab_source_note(source_note="Source: provided dataset.")

# Apply frame
gt = frame(gt)

# Finalize and save
finalize(gt, path="table.png")
