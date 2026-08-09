import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc
from gt_consistency import PALETTE, frame, finalize, heatmap, band, stripe, stub_tint

# Step 1: Load and clean data
df = pd.read_csv("towny.csv")

# Calculate overall growth rate 1996-2021 to identify fastest-growing towns
df["overall_growth_1996_2021"] = (df["population_2021"] - df["population_1996"]) / df["population_1996"]

# Get top 15 fastest-growing towns
top_15 = df.nlargest(15, "overall_growth_1996_2021")[["name", "population_1996", "population_2001", "population_2006", "population_2011", "population_2016", "population_2021", "density_1996", "density_2001", "density_2006", "density_2011", "density_2016", "density_2021", "pop_change_1996_2001_pct", "pop_change_2001_2006_pct", "pop_change_2006_2011_pct", "pop_change_2011_2016_pct", "pop_change_2016_2021_pct"]].copy()

# Calculate density percentage changes between periods
top_15["density_change_1996_2001_pct"] = (top_15["density_2001"] - top_15["density_1996"]) / top_15["density_1996"]
top_15["density_change_2001_2006_pct"] = (top_15["density_2006"] - top_15["density_2001"]) / top_15["density_2001"]
top_15["density_change_2006_2011_pct"] = (top_15["density_2011"] - top_15["density_2006"]) / top_15["density_2006"]
top_15["density_change_2011_2016_pct"] = (top_15["density_2016"] - top_15["density_2011"]) / top_15["density_2011"]
top_15["density_change_2016_2021_pct"] = (top_15["density_2021"] - top_15["density_2016"]) / top_15["density_2016"]

# Prepare display table with density values and changes
display_cols = [
    "name",
    "density_1996", "density_2001", "density_change_1996_2001_pct",
    "density_2006", "density_change_2001_2006_pct",
    "density_2011", "density_change_2006_2011_pct",
    "density_2016", "density_change_2011_2016_pct",
    "density_2021", "density_change_2016_2021_pct"
]

display_df = top_15[display_cols].copy()
display_df = display_df.reset_index(drop=True)

# Create GT table
gt = (
    GT(display_df, rowname_col="name")
    .tab_header(
        title="Population Density Growth in Ontario's Top 15 Fastest-Growing Towns",
        subtitle="Density by census year (persons/km²) with percentage changes between periods (1996–2021)"
    )
    .cols_label(
        density_1996=md("**1996**"),
        density_2001=md("**2001**"),
        density_change_1996_2001_pct=md("% change<br>1996–2001"),
        density_2006=md("**2006**"),
        density_change_2001_2006_pct=md("% change<br>2001–2006"),
        density_2011=md("**2011**"),
        density_change_2006_2011_pct=md("% change<br>2006–2011"),
        density_2016=md("**2016**"),
        density_change_2011_2016_pct=md("% change<br>2011–2016"),
        density_2021=md("**2021**"),
        density_change_2016_2021_pct=md("% change<br>2016–2021"),
    )
    .fmt_number(
        columns=["density_1996", "density_2001", "density_2006", "density_2011", "density_2016", "density_2021"],
        decimals=1
    )
    .fmt_percent(
        columns=["density_change_1996_2001_pct", "density_change_2001_2006_pct", "density_change_2006_2011_pct", "density_change_2011_2016_pct", "density_change_2016_2021_pct"],
        decimals=1
    )
)

# Color the density changes (percentage columns) with a diverging palette for growth trends
density_change_cols = ["density_change_1996_2001_pct", "density_change_2001_2006_pct", "density_change_2006_2011_pct", "density_change_2011_2016_pct", "density_change_2016_2021_pct"]
gt = heatmap(gt, density_change_cols, kind="diverging", hue="default")

# Apply band, stripe, stub tint, and frame
gt = band(gt, shade="light", hue="forest")
gt = stripe(gt)
gt = stub_tint(gt, hue="forest")
gt = frame(gt)

finalize(gt, "table.png")
