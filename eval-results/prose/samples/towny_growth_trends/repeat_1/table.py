import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc

# Read data
df = pd.read_csv("towny.csv")

# Step 1: UNDERSTAND THE DATA
# We have: name (identifier), populations for 6 census years, densities for 6 years,
# and pre-calculated percentage changes between periods.
# Task: Top 15 fastest-growing towns by overall growth 1996-2021,
# showing density across all years + period-over-period % changes

# Calculate overall growth rate 1996-2021
df["overall_growth_pct"] = (df["population_2021"] - df["population_1996"]) / df["population_1996"]

# Filter to top 15 fastest-growing
top_15 = df.nlargest(15, "overall_growth_pct").reset_index(drop=True)

# Select columns for display:
# - Town name (stub)
# - Population densities for all census years (1996, 2001, 2006, 2011, 2016, 2021)
# - Period-over-period percentage changes
display_cols = [
    "name",
    "density_1996", "density_2001", "density_2006", "density_2011", "density_2016", "density_2021",
    "pop_change_1996_2001_pct", "pop_change_2001_2006_pct", "pop_change_2006_2011_pct",
    "pop_change_2011_2016_pct", "pop_change_2016_2021_pct"
]

table_df = top_15[display_cols].copy()

# Rename columns for display
table_df = table_df.rename(columns={
    "name": "Town",
    "density_1996": "1996",
    "density_2001": "2001",
    "density_2006": "2006",
    "density_2011": "2011",
    "density_2016": "2016",
    "density_2021": "2021",
    "pop_change_1996_2001_pct": "1996-2001",
    "pop_change_2001_2006_pct": "2001-2006",
    "pop_change_2006_2011_pct": "2006-2011",
    "pop_change_2011_2016_pct": "2011-2016",
    "pop_change_2016_2021_pct": "2016-2021"
})

# Convert percentage columns from decimal (0.15) to percentage scale for display
pct_cols = ["1996-2001", "2001-2006", "2006-2011", "2011-2016", "2016-2021"]
for col in pct_cols:
    table_df[col] = table_df[col] * 100

# Determine Big Color: we have two ordered magnitudes
# 1. Density columns (neutral magnitude - ordered, ≥5 rows) → Blues
# 2. Change percentage columns (growth - more is better direction) → Greens
# Both qualify, so we color both (≤2 rule allows this)

# Compute domains for coloring
density_cols = ["1996", "2001", "2006", "2011", "2016", "2021"]
density_lo = float(np.nanmin(table_df[density_cols].to_numpy()))
density_hi = float(np.nanmax(table_df[density_cols].to_numpy()))

pct_change_lo = float(np.nanmin(table_df[pct_cols].to_numpy()))
pct_change_hi = float(np.nanmax(table_df[pct_cols].to_numpy()))

# Step 2: ORGANIZE COLUMNS
gt = GT(table_df, rowname_col="Town")

# Step 3: BIG COLOR
# Apply gradient fills for two measures:
# 1. Density columns: ordered magnitude, neutral (population density) → Blues
gt = gt.data_color(
    columns=density_cols,
    palette="Blues",
    domain=[density_lo, density_hi],
    truncate=False,
    na_color="#808080"
)

# 2. Percentage change columns: growth direction → Greens
gt = gt.data_color(
    columns=pct_cols,
    palette="Greens",
    domain=[pct_change_lo, pct_change_hi],
    truncate=False,
    na_color="#808080"
)

# Step 4: HEADING BAND - light washed tint because we have Big Color
# With Blues + Greens coloring, use Navy (default) with washed tint #EAF0F6
gt = gt.tab_header(
    title="Population Density Trends",
    subtitle="Top 15 fastest-growing Ontario towns (1996-2021), showing density per km² and period-over-period population change %"
)

gt = gt.tab_style(
    style=style.fill(color="#EAF0F6"),
    locations=loc.header()
)

gt = gt.tab_style(
    style=style.text(color="#22384F", weight="bold"),
    locations=loc.header()
)

# Step 5: SMALL COLOR - polish checklist
# (a) Cell borders - light hairline between rows
gt = gt.tab_style(
    style=style.borders(
        sides="bottom",
        color="#E8E8E8",
        weight="1px"
    ),
    locations=loc.body(rows=list(range(len(table_df) - 1)))
)

# (b) Column dividers - vertical divider between density and change sections
# Place at column index 6 (after "2021", before "1996-2001")
for row_idx in range(len(table_df)):
    gt = gt.tab_style(
        style=style.borders(
            sides="right",
            color="#D0D0D0",
            weight="1px"
        ),
        locations=loc.body(rows=[row_idx], columns=["2021"])
    )

# (c) Row striping with gate: apply to every other row
for i in range(1, len(table_df), 2):
    gt = gt.tab_style(
        style=style.fill(color="#F6F6F6"),
        locations=loc.body(rows=[i])
    )

# (d) Stub tint - grey for row names
gt = gt.tab_style(
    style=style.fill(color="#F0F0F0"),
    locations=loc.stub()
)

# (e) Formatting - format numbers appropriately
# Density: 1 decimal place
gt = gt.fmt_number(
    columns=density_cols,
    decimals=1
)

# Percentage changes: 1 decimal place with % sign
gt = gt.fmt_percent(
    columns=pct_cols,
    decimals=1,
    scale_values=False  # Already multiplied by 100 above
)

# Column label bottom rule - #CCCCCC, 2px
gt = gt.tab_style(
    style=style.borders(
        sides="bottom",
        color="#CCCCCC",
        weight="2px"
    ),
    locations=loc.column_labels()
)

# Column label styling - washed tint background
gt = gt.tab_style(
    style=style.fill(color="#EAF0F6"),
    locations=loc.column_labels()
)

# Step 6: TITLES & ANNOTATIONS
gt = gt.tab_source_note(
    source_note="Ranking by overall population growth rate from 1996 to 2021. Density measured in persons per km². " +
                "Population change percentages are period-over-period rates."
)

# Step 7: RENDER & VERIFY
gt.gtsave("table.png")
print("Table rendered successfully to table.png")
