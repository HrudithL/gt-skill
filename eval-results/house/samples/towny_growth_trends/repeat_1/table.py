import pandas as pd
from great_tables import GT, loc, style, md
from house_table import (
    PALETTE, frame, hairlines, finalize, band, stripe,
    stub_tint, heatmap, humanize_labels
)

# Read the data
df = pd.read_csv("towny.csv")

# Calculate total population growth from 1996 to 2021
df["total_pop_growth_pct"] = (df["population_2021"] - df["population_1996"]) / df["population_1996"]

# Get top 15 fastest-growing towns
top_15 = df.nlargest(15, "total_pop_growth_pct")[
    ["name", "population_1996", "population_2001", "population_2006",
     "population_2011", "population_2016", "population_2021",
     "density_1996", "density_2001", "density_2006",
     "density_2011", "density_2016", "density_2021"]
].reset_index(drop=True)

# Compute density percentage changes between periods
top_15["density_pct_1996_2001"] = (top_15["density_2001"] - top_15["density_1996"]) / top_15["density_1996"]
top_15["density_pct_2001_2006"] = (top_15["density_2006"] - top_15["density_2001"]) / top_15["density_2001"]
top_15["density_pct_2006_2011"] = (top_15["density_2011"] - top_15["density_2006"]) / top_15["density_2006"]
top_15["density_pct_2011_2016"] = (top_15["density_2016"] - top_15["density_2011"]) / top_15["density_2011"]
top_15["density_pct_2016_2021"] = (top_15["density_2021"] - top_15["density_2016"]) / top_15["density_2016"]

# Select columns for the table: name + densities + density changes
table_data = top_15[
    ["name", "density_1996", "density_2001", "density_2006", "density_2011", "density_2016", "density_2021",
     "density_pct_1996_2001", "density_pct_2001_2006", "density_pct_2006_2011",
     "density_pct_2011_2016", "density_pct_2016_2021"]
].copy()

# Rename for clarity
table_data.columns = [
    "Town", "Density 1996", "Density 2001", "Density 2006", "Density 2011", "Density 2016", "Density 2021",
    "Change 1996-01%", "Change 2001-06%", "Change 2006-11%", "Change 2011-16%", "Change 2016-21%"
]

# Build the table
gt = GT(table_data, rowname_col="Town")
gt = gt.tab_header(
    title="Population Density Trends: Top 15 Fastest-Growing Ontario Towns",
    subtitle=md("Density (persons per km²) and density change percentages across census periods, 1996–2021")
)

# Format density columns as numbers with 1 decimal
for col in ["Density 1996", "Density 2001", "Density 2006", "Density 2011", "Density 2016", "Density 2021"]:
    gt = gt.fmt_number(columns=col, decimals=1)

# Format percentage changes with 1 decimal
for col in ["Change 1996-01%", "Change 2001-06%", "Change 2006-11%", "Change 2011-16%", "Change 2016-21%"]:
    gt = gt.fmt_percent(columns=col, decimals=1, force_sign=True)

# Add spanners to organize columns
gt = gt.tab_spanner(label="Density (persons/km²)", columns=["Density 1996", "Density 2001", "Density 2006", "Density 2011", "Density 2016", "Density 2021"])
gt = gt.tab_spanner(label="Period-to-Period Density Change %", columns=["Change 1996-01%", "Change 2001-06%", "Change 2006-11%", "Change 2011-16%", "Change 2016-21%"])

# Humanize labels
gt = humanize_labels(gt, table_data, overrides={})

# Color the density change columns with diverging palette (red/yellow/green for negative/neutral/positive)
gt = heatmap(gt, ["Change 1996-01%", "Change 2001-06%", "Change 2006-11%", "Change 2011-16%", "Change 2016-21%"],
             kind="diverging", hue="default")

# Column widths
gt = gt.cols_width(
    cases={
        "Town": "160px",
        "Density 1996": "95px",
        "Density 2001": "95px",
        "Density 2006": "95px",
        "Density 2011": "95px",
        "Density 2016": "95px",
        "Density 2021": "95px",
        "Change 1996-01%": "105px",
        "Change 2001-06%": "105px",
        "Change 2006-11%": "105px",
        "Change 2011-16%": "105px",
        "Change 2016-21%": "105px",
    }
)

# Padding
gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Apply styling
gt = band(gt, hue="navy")
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

# Source notes
gt = gt.tab_source_note(
    source_note="Towns ranked by total population growth (1996–2021). Density change percentages show period-to-period shifts in persons per square kilometre."
)
gt = gt.tab_source_note(
    source_note="Source: Ontario town census data, 1996–2021."
)

gt = hairlines(gt)
gt = frame(gt)
finalize(gt)
