import sys
sys.path.insert(0, '.claude/skills/great-tables/scripts')

import pandas as pd
from great_tables import GT, md
from gt_house_style import apply_house_style, add_heatmap, humanize_labels

# Load data
df = pd.read_csv("towny.csv")

# Calculate overall growth 1996-2021
df["overall_growth"] = ((df["population_2021"] - df["population_1996"]) / df["population_1996"]).fillna(0)

# Get top 15 fastest-growing towns
top_15 = df.nlargest(15, "overall_growth")

# Prepare display table with populations and density
display_df = top_15[[
    "name",
    "population_1996",
    "density_1996",
    "population_2001",
    "density_2001",
    "population_2006",
    "density_2006",
    "population_2011",
    "density_2011",
    "population_2016",
    "density_2016",
    "population_2021",
    "density_2021",
    "pop_change_1996_2001_pct",
    "pop_change_2001_2006_pct",
    "pop_change_2006_2011_pct",
    "pop_change_2011_2016_pct",
    "pop_change_2016_2021_pct",
]].reset_index(drop=True).copy()

# Rename columns for clarity
display_df.columns = [
    "Town",
    "Pop 1996",
    "Dens 1996",
    "Pop 2001",
    "Dens 2001",
    "Pop 2006",
    "Dens 2006",
    "Pop 2011",
    "Dens 2011",
    "Pop 2016",
    "Dens 2016",
    "Pop 2021",
    "Dens 2021",
    "Chg 96-01 %",
    "Chg 01-06 %",
    "Chg 06-11 %",
    "Chg 11-16 %",
    "Chg 16-21 %",
]

# Build the GT table
tbl = (
    GT(display_df)
    .tab_header(
        title="Ontario Towns: Population Growth & Density Trends",
        subtitle=md("Top 15 fastest-growing towns by population (1996–2021), with density and period-over-period change"),
    )
)

# Format populations as integers
pop_cols = ["Pop 1996", "Pop 2001", "Pop 2006", "Pop 2011", "Pop 2016", "Pop 2021"]
tbl = tbl.fmt_integer(columns=pop_cols)

# Format densities (people/km²) with 1 decimal place
density_cols = ["Dens 1996", "Dens 2001", "Dens 2006", "Dens 2011", "Dens 2016", "Dens 2021"]
tbl = tbl.fmt_number(columns=density_cols, decimals=1)

# Format percentage changes
pct_change_cols = ["Chg 96-01 %", "Chg 01-06 %", "Chg 06-11 %", "Chg 11-16 %", "Chg 16-21 %"]
tbl = tbl.fmt_percent(columns=pct_change_cols, decimals=1)

# Add spanners for logical grouping
tbl = (
    tbl
    .tab_spanner(label="1996", columns=["Pop 1996", "Dens 1996"])
    .tab_spanner(label="2001", columns=["Pop 2001", "Dens 2001"])
    .tab_spanner(label="2006", columns=["Pop 2006", "Dens 2006"])
    .tab_spanner(label="2011", columns=["Pop 2011", "Dens 2011"])
    .tab_spanner(label="2016", columns=["Pop 2016", "Dens 2016"])
    .tab_spanner(label="2021", columns=["Pop 2021", "Dens 2021"])
)

# Town column is already in place

# Add source note
tbl = tbl.tab_source_note(source_note="Source: Statistics Canada Census data; density calculated as population / land area (km²).")

# Add missing value handling
tbl = tbl.sub_missing(missing_text="—")

# Add heatmap for percentage change columns to highlight growth patterns
tbl = add_heatmap(tbl, display_df, pct_change_cols, kind="auto")

# Apply house style
tbl = apply_house_style(tbl)

# Render to PNG
tbl.gtsave("table.png", zoom=2, expand=10)
print("Table rendered successfully: table.png")
