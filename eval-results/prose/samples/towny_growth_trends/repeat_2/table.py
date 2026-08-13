import pandas as pd
import numpy as np
from great_tables import GT, md, html, style, loc

# Step 1: Load and clean the data
df = pd.read_csv("towny.csv")

# Calculate overall population growth rate from 1996 to 2021 to identify fastest-growing towns
df["pop_growth_1996_2021"] = (df["population_2021"] - df["population_1996"]) / df["population_1996"]

# Filter to top 15 fastest-growing towns
top_15 = df.nlargest(15, "pop_growth_1996_2021").copy()

# Select and reorder columns for the table
# Stub: town name
# Density columns across all years: 1996, 2001, 2006, 2011, 2016, 2021
# Percentage change columns for each period
display_cols = ["name"] + [
    "density_1996", "pop_change_1996_2001_pct",
    "density_2001", "pop_change_2001_2006_pct",
    "density_2006", "pop_change_2006_2011_pct",
    "density_2011", "pop_change_2011_2016_pct",
    "density_2016", "pop_change_2016_2021_pct",
    "density_2021"
]

table_data = top_15[display_cols].copy()

# Rename columns for display
rename_map = {
    "name": "Town",
    "density_1996": "Density 1996",
    "density_2001": "Density 2001",
    "density_2006": "Density 2006",
    "density_2011": "Density 2011",
    "density_2016": "Density 2016",
    "density_2021": "Density 2021",
    "pop_change_1996_2001_pct": "% Change 1996-2001",
    "pop_change_2001_2006_pct": "% Change 2001-2006",
    "pop_change_2006_2011_pct": "% Change 2006-2011",
    "pop_change_2011_2016_pct": "% Change 2011-2016",
    "pop_change_2016_2021_pct": "% Change 2016-2021",
}

table_data = table_data.rename(columns=rename_map)

# Step 2: Organize columns - set town name as stub
# Reorder for better readability: density first, then % changes interspersed
# This creates a natural pairing of density before each period's change

# Step 3: Identify measures for Big Color
# Density columns are magnitudes (levels) - they earn gradient fill
# Percentage change columns are rates - they represent growth trends
density_cols = ["Density 1996", "Density 2001", "Density 2006", "Density 2011", "Density 2016", "Density 2021"]
pct_cols = ["% Change 1996-2001", "% Change 2001-2006", "% Change 2006-2011", "% Change 2011-2016", "% Change 2016-2021"]

# Data-driven domains for density gradient
lo_density = float(np.nanmin(table_data[density_cols].to_numpy()))
hi_density = float(np.nanmax(table_data[density_cols].to_numpy()))

# Data-driven domains for percentage change gradient
lo_pct = float(np.nanmin(table_data[pct_cols].to_numpy()))
hi_pct = float(np.nanmax(table_data[pct_cols].to_numpy()))

# Create the GT table
gt = (
    GT(table_data, rowname_col="Town")
    # Step 2: Organize - format numeric columns
    .fmt_number(columns=density_cols, decimals=1)
    .fmt_percent(columns=pct_cols, decimals=1, scale_values=True)
    # Step 3: Big Color - gradient fill for density (primary hero measure - magnitude)
    .data_color(
        columns=density_cols,
        palette="Blues",
        domain=[lo_density, hi_density],
        truncate=False,
        na_color="#808080",
    )
    # Second measure: percentage change (distinct dimension - rate of change)
    .data_color(
        columns=pct_cols,
        palette="Greens",
        domain=[lo_pct, hi_pct],
        truncate=False,
        na_color="#808080",
    )
    # Step 4: Heading band (fixed branding constants)
    .tab_header(
        title="Population Growth Trends in Fast-Growing Ontario Towns",
        subtitle="Density changes and growth rates across census years, 1996–2021"
    )
    # Step 5: Small Color polish - headings, borders, striping, frame
    .tab_stubhead(label="Town")
    # Column label styling (heading band) and table options
    .tab_options(
        column_labels_background_color="#08306B",
        column_labels_font_weight="bold",
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        row_striping_background_color="#F6F6F6",
        data_row_padding="8px",
    )
    # Column label text color (white on dark band)
    .tab_style(
        style.text(color="white"),
        loc.column_labels()
    )
    # Apply row striping (since we have both Big Color treatments, confirm striping applies)
    .opt_row_striping()
    # Stub tint (pale blue)
    .tab_style(
        style.fill(color="#EAF0F6"),
        loc.stub()
    )
    # Frame border with margin
    .tab_style(
        style.borders(
            sides="all",
            color="#CCCCCC",
            weight="1px"
        ),
        loc.body()
    )
    # Column group dividers for better visual grouping of density/change pairs
    .tab_spanner(
        label="1996–2001",
        columns=["Density 1996", "% Change 1996-2001"]
    )
    .tab_spanner(
        label="2001–2006",
        columns=["Density 2001", "% Change 2001-2006"]
    )
    .tab_spanner(
        label="2006–2011",
        columns=["Density 2006", "% Change 2006-2011"]
    )
    .tab_spanner(
        label="2011–2016",
        columns=["Density 2011", "% Change 2011-2016"]
    )
    .tab_spanner(
        label="2016–2021",
        columns=["Density 2016", "% Change 2016-2021", "Density 2021"]
    )
    # Step 6: Titles & annotations
    .tab_source_note(
        md("**Density** measured in persons per square kilometer; **growth rate** represents percentage population change between consecutive census periods.")
    )
    .tab_source_note(
        "Data source: Statistics Canada, Census of Population (1996–2021)"
    )
)

# Step 7: Render and verify
gt.gtsave("table.png", zoom=2)
