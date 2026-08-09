import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc

# Load and clean data
df = pd.read_csv("towny.csv")

# Calculate total population growth (1996-2021) to identify fastest-growing towns
df["growth_1996_2021"] = ((df["population_2021"] - df["population_1996"]) / df["population_1996"]) * 100

# Get top 15 fastest-growing towns
top_15 = df.nlargest(15, "growth_1996_2021")[["name", "population_1996", "population_2001", "population_2006",
                                                "population_2011", "population_2016", "population_2021",
                                                "density_1996", "density_2001", "density_2006", "density_2011",
                                                "density_2016", "density_2021",
                                                "pop_change_1996_2001_pct", "pop_change_2001_2006_pct",
                                                "pop_change_2006_2011_pct", "pop_change_2011_2016_pct",
                                                "pop_change_2016_2021_pct"]].reset_index(drop=True)

# Rename columns for display
display_df = top_15.copy()
display_df.columns = ["Town", "Pop 1996", "Pop 2001", "Pop 2006", "Pop 2011", "Pop 2016", "Pop 2021",
                       "Dens 1996", "Dens 2001", "Dens 2006", "Dens 2011", "Dens 2016", "Dens 2021",
                       "% 96-01", "% 01-06", "% 06-11", "% 11-16", "% 16-21"]

# Extract density columns for Big Color treatment (gradient fill)
density_cols = ["Dens 1996", "Dens 2001", "Dens 2006", "Dens 2011", "Dens 2016", "Dens 2021"]
pop_cols = ["Pop 1996", "Pop 2001", "Pop 2006", "Pop 2011", "Pop 2016", "Pop 2021"]
pct_cols = ["% 96-01", "% 01-06", "% 06-11", "% 11-16", "% 16-21"]

# Calculate domain for density columns (Big Color measure #1)
dens_lo = float(np.nanmin(display_df[density_cols].to_numpy()))
dens_hi = float(np.nanmax(display_df[density_cols].to_numpy()))

# Calculate domain for percentage change columns (Big Color measure #2) - diverging around 0
pct_lo = float(np.nanmin(display_df[pct_cols].to_numpy()))
pct_hi = float(np.nanmax(display_df[pct_cols].to_numpy()))
# Make domain symmetric for diverging
pct_domain_abs = max(abs(pct_lo), abs(pct_hi))
pct_domain = [-pct_domain_abs, pct_domain_abs]

# Create the GT table
gt = (
    GT(display_df, rowname_col="Town")

    # Format population columns as integers
    .fmt_number(columns=pop_cols, decimals=0)

    # Format density columns with 1 decimal place
    .fmt_number(columns=density_cols, decimals=1)

    # Format percentage change columns (already on 0-1 scale, so use scale_values=False after converting to percent scale)
    # Note: data is already in decimal form (0.05 = 5%), so scale_values=True converts to 500% - need False
    .fmt_percent(columns=pct_cols, decimals=1, scale_values=False)

    # Big Color #1: Density columns with sequential Blues palette (neutral magnitude)
    .data_color(
        columns=density_cols,
        palette="Blues",
        domain=[dens_lo, dens_hi],
        truncate=False,
        na_color="#808080",
    )

    # Big Color #2: Percentage change columns with diverging palette (signed measure)
    .data_color(
        columns=pct_cols,
        palette="RdYlGn",
        domain=pct_domain,
        truncate=False,
        na_color="#808080",
    )

    # Light band (Big Color present) - washed Navy tint
    .tab_options(
        column_labels_background_color="#EAF0F6",
        column_labels_font_weight="bold",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        # Frame borders
        table_border_top_style="solid",    table_border_top_color="#CCCCCC",    table_border_top_width="1px",
        table_border_bottom_style="solid", table_border_bottom_color="#CCCCCC", table_border_bottom_width="1px",
        table_border_left_style="solid",   table_border_left_color="#CCCCCC",   table_border_left_width="1px",
        table_border_right_style="solid",  table_border_right_color="#CCCCCC",  table_border_right_width="1px",
    )

    # Add titles and caption
    .tab_header(
        title="Top 15 Fastest-Growing Ontario Towns",
        subtitle="Population and Density Trends (1996–2021)"
    )

    .tab_source_note(
        md("*Data source: Census Canada (1996–2021)*")
    )
)

# Render to PNG with expand margin
gt.gtsave("table.png", expand=15)
print("Table rendered successfully to table.png")
