import pandas as pd
import numpy as np
from great_tables import GT, loc, style

# STEP 1: UNDERSTAND & CLEAN DATA
df = pd.read_csv("towny.csv")

# Calculate overall growth rate from 1996 to 2021 to identify fastest-growing towns
df["total_growth_pct"] = (df["population_2021"] - df["population_1996"]) / df["population_1996"]

# Get top 15 fastest-growing towns
top_15 = df.nlargest(15, "total_growth_pct")[["name", "population_1996", "density_1996",
                                                "population_2001", "density_2001",
                                                "population_2006", "density_2006",
                                                "population_2011", "density_2011",
                                                "population_2016", "density_2016",
                                                "population_2021", "density_2021",
                                                "pop_change_1996_2001_pct", "pop_change_2001_2006_pct",
                                                "pop_change_2006_2011_pct", "pop_change_2011_2016_pct",
                                                "pop_change_2016_2021_pct"]].copy()

# Rename for clarity
top_15.columns = ["Town", "Pop1996", "Dens1996", "Pop2001", "Dens2001", "Pop2006", "Dens2006",
                  "Pop2011", "Dens2011", "Pop2016", "Dens2016", "Pop2021", "Dens2021",
                  "Chg1996-01%", "Chg2001-06%", "Chg2006-11%", "Chg2011-16%", "Chg2016-21%"]

# Reset index for clean display
top_15 = top_15.reset_index(drop=True)

# Calculate density changes between periods
top_15["DensChg1996-01%"] = ((top_15["Dens2001"] - top_15["Dens1996"]) / top_15["Dens1996"]) * 100
top_15["DensChg2001-06%"] = ((top_15["Dens2006"] - top_15["Dens2001"]) / top_15["Dens2001"]) * 100
top_15["DensChg2006-11%"] = ((top_15["Dens2011"] - top_15["Dens2006"]) / top_15["Dens2006"]) * 100
top_15["DensChg2011-16%"] = ((top_15["Dens2016"] - top_15["Dens2011"]) / top_15["Dens2011"]) * 100
top_15["DensChg2016-21%"] = ((top_15["Dens2021"] - top_15["Dens2016"]) / top_15["Dens2016"]) * 100

# Create display dataframe with just what we need for the table
display_df = top_15[["Town",
                     "Dens1996", "Dens2001", "Dens2006", "Dens2011", "Dens2016", "Dens2021",
                     "DensChg1996-01%", "DensChg2001-06%", "DensChg2006-11%", "DensChg2011-16%", "DensChg2016-21%"]].copy()

# Rename for cleaner display
display_df.columns = ["Town",
                      "Density 1996", "Density 2001", "Density 2006", "Density 2011", "Density 2016", "Density 2021",
                      "% Chg 96-01", "% Chg 01-06", "% Chg 06-11", "% Chg 11-16", "% Chg 16-21"]

# Calculate data domain for density columns (for heatmap)
density_cols = ["Density 1996", "Density 2001", "Density 2006", "Density 2011", "Density 2016", "Density 2021"]
density_lo = float(np.nanmin(display_df[density_cols].to_numpy()))
density_hi = float(np.nanmax(display_df[density_cols].to_numpy()))

# Calculate data domain for percentage change columns
pct_cols = ["% Chg 96-01", "% Chg 01-06", "% Chg 06-11", "% Chg 11-16", "% Chg 16-21"]
pct_min = float(np.nanmin(display_df[pct_cols].to_numpy()))
pct_max = float(np.nanmax(display_df[pct_cols].to_numpy()))
# Use symmetric domain for diverging (percent change can be negative)
pct_domain = [-max(abs(pct_min), abs(pct_max)), max(abs(pct_min), abs(pct_max))]

# STEP 2-5: BUILD TABLE with Great Tables
gt = (
    GT(display_df, rowname_col="Town")
    # STEP 3: BIG COLOR - Density columns with sequential palette (ordered magnitude)
    .data_color(
        columns=density_cols,
        palette="Blues",
        domain=[density_lo, density_hi],
        truncate=False,
        na_color="#808080",
    )
    # STEP 3: BIG COLOR - Percentage change columns with diverging palette (signed measure)
    .data_color(
        columns=pct_cols,
        palette="RdBu",
        domain=pct_domain,
        truncate=False,
        na_color="#808080",
    )
    # STEP 4: HEADING BAND - dark navy, bold white text
    .tab_header(
        title="Top 15 Fastest-Growing Ontario Towns",
        subtitle="Population Density Evolution Across Census Years (1996–2021)"
    )
    # Format density columns as numbers with 1 decimal
    .fmt_number(columns=density_cols, decimals=1)
    # Format percentage change columns as numbers with 1 decimal
    .fmt_number(columns=pct_cols, decimals=1)
    # STEP 5: SMALL COLOR - Row striping
    .opt_row_striping()
    # STEP 5: SMALL COLOR - Stub tint
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # STEP 5: SMALL COLOR - Body row hairlines
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # STEP 5: SMALL COLOR - Frame with border on all four sides
    .tab_options(
        table_border_top_style="solid",
        table_border_top_color="#CCCCCC",
        table_border_top_width="1px",
        table_border_bottom_style="solid",
        table_border_bottom_color="#CCCCCC",
        table_border_bottom_width="1px",
        table_border_left_style="solid",
        table_border_left_color="#CCCCCC",
        table_border_left_width="1px",
        table_border_right_style="solid",
        table_border_right_color="#CCCCCC",
        table_border_right_width="1px",
    )
    # STEP 6: TITLES & ANNOTATIONS - Footer notes
    .tab_source_note(
        "Fastest-growing means highest percent change across the full 1996–2021 span. Density measured as population per square kilometer."
    )
    .tab_source_note(
        "Source: Statistics Canada Census data, 1996–2021"
    )
)

# STEP 7: RENDER & VERIFY
gt.gtsave("table.png", expand=15)
print("Table rendered successfully to table.png")
