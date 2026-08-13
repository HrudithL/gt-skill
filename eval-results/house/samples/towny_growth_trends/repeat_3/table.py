import pandas as pd
import numpy as np
from great_tables import GT, md, loc, style
from house_table import (
    PALETTE, frame, hairlines, finalize, band, stripe,
    stub_tint, heatmap, humanize_labels
)

# Read data
df = pd.read_csv("towny.csv")

# Compute overall population growth rate (1996-2021)
df["total_growth_pct"] = np.where(
    df["population_1996"] > 0,
    (df["population_2021"] - df["population_1996"]) / df["population_1996"],
    np.nan
)

# Select top 15 fastest-growing towns
top_15 = df.nlargest(15, "total_growth_pct").copy()

# Prepare the table data with density values and period changes
result = pd.DataFrame()
result["Town"] = top_15["name"].reset_index(drop=True)

# Density columns for each census year
result["Density 1996"] = top_15["density_1996"].reset_index(drop=True)
result["Density 2001"] = top_15["density_2001"].reset_index(drop=True)
result["Density 2006"] = top_15["density_2006"].reset_index(drop=True)
result["Density 2011"] = top_15["density_2011"].reset_index(drop=True)
result["Density 2016"] = top_15["density_2016"].reset_index(drop=True)
result["Density 2021"] = top_15["density_2021"].reset_index(drop=True)

# Period changes (as percentages, already in the data but we compute to be safe)
result["Change 96-01 %"] = np.where(
    top_15["density_1996"].reset_index(drop=True) > 0,
    (top_15["density_2001"].reset_index(drop=True) - top_15["density_1996"].reset_index(drop=True)) / top_15["density_1996"].reset_index(drop=True),
    np.nan
)
result["Change 01-06 %"] = np.where(
    top_15["density_2001"].reset_index(drop=True) > 0,
    (top_15["density_2006"].reset_index(drop=True) - top_15["density_2001"].reset_index(drop=True)) / top_15["density_2001"].reset_index(drop=True),
    np.nan
)
result["Change 06-11 %"] = np.where(
    top_15["density_2006"].reset_index(drop=True) > 0,
    (top_15["density_2011"].reset_index(drop=True) - top_15["density_2006"].reset_index(drop=True)) / top_15["density_2006"].reset_index(drop=True),
    np.nan
)
result["Change 11-16 %"] = np.where(
    top_15["density_2011"].reset_index(drop=True) > 0,
    (top_15["density_2016"].reset_index(drop=True) - top_15["density_2011"].reset_index(drop=True)) / top_15["density_2011"].reset_index(drop=True),
    np.nan
)
result["Change 16-21 %"] = np.where(
    top_15["density_2016"].reset_index(drop=True) > 0,
    (top_15["density_2021"].reset_index(drop=True) - top_15["density_2016"].reset_index(drop=True)) / top_15["density_2016"].reset_index(drop=True),
    np.nan
)

# Reset index to ensure Town is a proper column for the stub
result = result.reset_index(drop=True)

# Create GT table
gt = GT(result, rowname_col="Town")

# Format density columns (no decimals for large values)
density_cols = ["Density 1996", "Density 2001", "Density 2006", "Density 2011", "Density 2016", "Density 2021"]
for col in density_cols:
    gt = gt.fmt_number(columns=col, decimals=1)

# Format percentage changes
pct_cols = ["Change 96-01 %", "Change 01-06 %", "Change 06-11 %", "Change 11-16 %", "Change 16-21 %"]
for col in pct_cols:
    gt = gt.fmt_percent(columns=col, decimals=1, scale_values=False, force_sign=True)

# Apply missing value substitution
for col in density_cols + pct_cols:
    gt = gt.sub_missing(columns=col, missing_text="—")

# Add title and subtitle
gt = gt.tab_header(
    title="Population Density Growth in Ontario's Fastest-Growing Towns",
    subtitle="Top 15 towns by population growth rate (1996–2021)"
)

# Add source notes
gt = gt.tab_source_note(
    source_note="Ranked by overall population growth rate 1996–2021; all Ontario municipality types included."
)
gt = gt.tab_source_note(
    source_note="Source: provided dataset."
)

# Add stub head
gt = gt.tab_stubhead(label="Town")

# Create spanners for density and change sections
gt = gt.tab_spanner(label="Population Density (persons/km²)", columns=density_cols)
gt = gt.tab_spanner(label="Period Change (%)", columns=pct_cols)

# Add vertical divider at spanner boundaries
gt = gt.tab_style(
    style=style.borders(sides="right", color=PALETTE["neutral"]["vertical_divider"], weight="1px"),
    locations=[loc.body(columns="Density 2021"), loc.column_labels(columns="Density 2021")]
)

# Apply house format styling
gt = band(gt, hue="navy")
gt = stub_tint(gt, hue="navy")
gt = stripe(gt)

# Apply heatmaps to the density columns (sequential - growth is positive)
gt = heatmap(gt, density_cols, kind="sequential", hue="positive")

# Apply heatmap to period changes (diverging - positive and negative both meaningful)
gt = heatmap(gt, pct_cols, kind="diverging", hue="default")

# Apply frame and hairlines
gt = frame(gt)
gt = hairlines(gt)

# Finalize and save
finalize(gt, path="table.png")
