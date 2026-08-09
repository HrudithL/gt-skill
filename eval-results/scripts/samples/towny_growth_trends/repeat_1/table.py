import pandas as pd
import numpy as np
from great_tables import GT
from gt_consistency import frame, finalize, heatmap, band, stripe, PALETTE

# Step 1: Load and prepare data
df_raw = pd.read_csv("towny.csv")

# Ensure population columns are numeric
for col in ["population_1996", "population_2021"]:
    df_raw[col] = pd.to_numeric(df_raw[col], errors="coerce")

# Calculate overall growth rate from 1996 to 2021
df_raw["overall_growth"] = np.where(
    df_raw["population_1996"] > 0,
    (df_raw["population_2021"] - df_raw["population_1996"]) / df_raw["population_1996"],
    np.nan
)

# Get top 15 fastest-growing towns
top_15 = df_raw.nlargest(15, "overall_growth")[["name", "density_1996", "density_2001", "density_2006",
                                                  "density_2011", "density_2016", "density_2021",
                                                  "pop_change_1996_2001_pct", "pop_change_2001_2006_pct",
                                                  "pop_change_2006_2011_pct", "pop_change_2011_2016_pct",
                                                  "pop_change_2016_2021_pct"]].reset_index(drop=True)

# Rename columns for display
top_15.columns = ["Town", "Density 1996", "Density 2001", "Density 2006", "Density 2011", "Density 2016", "Density 2021",
                  "Growth 1996-2001", "Growth 2001-2006", "Growth 2006-2011", "Growth 2011-2016", "Growth 2016-2021"]

# Ensure numeric columns are float
density_cols = ["Density 1996", "Density 2001", "Density 2006", "Density 2011", "Density 2016", "Density 2021"]
growth_cols = ["Growth 1996-2001", "Growth 2001-2006", "Growth 2006-2011", "Growth 2011-2016", "Growth 2016-2021"]

for col in density_cols + growth_cols:
    top_15[col] = pd.to_numeric(top_15[col], errors="coerce")

# Create the GT table with Town as stub column
gt = GT(top_15, rowname_col="Town")

# Step 3: Apply color to density columns (sequential gradient - Blues for population/magnitude)
gt = heatmap(
    gt,
    columns=density_cols,
    kind="sequential",
    hue="neutral",
)

# Step 4: Apply heading band (light band because we have Big Color)
gt = band(gt, shade="light", hue="navy")

# Step 5: Apply small color polish
# Cell borders (band() handles the column label band and bottom rule)
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
)

# Add row striping (15 rows, body not fully color-filled)
gt = stripe(gt)

# Format density columns (one decimal place)
for col in density_cols:
    gt = gt.fmt_number(columns=col, decimals=1)

# Format growth columns as percentages
for col in growth_cols:
    gt = gt.fmt_percent(columns=col, decimals=1)

# Apply frame
gt = frame(gt)

# Step 6: Add titles and source note
gt = gt.tab_header(
    title="Ontario Towns: Population Growth Trends",
    subtitle="Density changes (persons/km²) for top 15 fastest-growing towns, 1996-2021"
)

gt = gt.tab_source_note(
    "Population density measured in persons per square kilometer. Growth percentages represent relative change from previous census period."
)

# Step 7: Finalize and render
gt = finalize(gt)
gt.gtsave("table.png", zoom=2.0, expand=10)
