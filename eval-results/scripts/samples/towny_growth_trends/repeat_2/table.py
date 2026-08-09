import pandas as pd
import numpy as np
from great_tables import GT, style, loc
from gt_consistency import heatmap, band, frame, finalize, stripe, stub_tint, PALETTE

# Step 1: Load and clean data
df = pd.read_csv("towny.csv")

# Calculate overall growth rate from 1996 to 2021 for ranking
df["overall_growth_rate"] = (df["population_2021"] - df["population_1996"]) / df["population_1996"]

# Select top 15 fastest-growing towns
top_15 = df.nlargest(15, "overall_growth_rate").copy()

# Step 2: Organize data for display
# Create a clean dataset with town name, all density columns, and percentage changes
display_cols = ["name"]
density_cols = ["density_1996", "density_2001", "density_2006", "density_2011", "density_2016", "density_2021"]
change_cols = ["pop_change_1996_2001_pct", "pop_change_2001_2006_pct", "pop_change_2006_2011_pct",
               "pop_change_2011_2016_pct", "pop_change_2016_2021_pct"]

# Extract relevant columns
result_df = top_15[display_cols + density_cols + change_cols].copy()

# Rename columns for clarity
result_df.columns = ["Town",
                     "1996", "2001", "2006", "2011", "2016", "2021",
                     "1996-01 Δ%", "2001-06 Δ%", "2006-11 Δ%", "2011-16 Δ%", "2016-21 Δ%"]

# Reset index for cleaner output
result_df = result_df.reset_index(drop=True)

# Step 3: Identify colored measures - density values are ordered numeric magnitude (≥5 rows)
# These are population density columns - neutral magnitude → Blues
density_cols_renamed = ["1996", "2001", "2006", "2011", "2016", "2021"]
change_cols_renamed = ["1996-01 Δ%", "2001-06 Δ%", "2006-11 Δ%", "2011-16 Δ%", "2016-21 Δ%"]

# Compute domain for density (Big Color #1)
lo_dens = float(np.nanmin(result_df[density_cols_renamed].to_numpy()))
hi_dens = float(np.nanmax(result_df[density_cols_renamed].to_numpy()))

# Step 4: Create the table with GT
gt = (
    GT(result_df, rowname_col="Town")
    # Format density columns as numbers with 1 decimal
    .fmt_number(columns=density_cols_renamed, decimals=1, use_seps=True)
    # Format percentage change columns with 1 decimal
    .fmt_percent(columns=change_cols_renamed, decimals=1, scale_values=False)
    # Add column spanners for logical grouping
    .tab_spanner(label="Density (persons/km²)", columns=density_cols_renamed)
    .tab_spanner(label="Population Change %", columns=change_cols_renamed)
    # Color the density columns (sequential gradient - Blues for neutral magnitude)
    .data_color(
        columns=density_cols_renamed,
        palette="Blues",
        domain=[lo_dens, hi_dens],
        truncate=False,
        na_color="#808080",
    )
    # Missing value handling
    .sub_missing(columns=density_cols_renamed + change_cols_renamed, missing_text="—")
)

# Step 5: Small Color polish
# (a) Cell borders - hairlines between rows, structural rules
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
    column_labels_border_bottom_color="#CCCCCC",
    column_labels_border_bottom_width="2px",
)

# (b) Column-group vertical dividers
# Right border on last column of density group (2021) in body and header
gt = gt.tab_style(
    style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
    locations=loc.body(columns="2021"),
)
gt = gt.tab_style(
    style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
    locations=loc.column_labels(columns="2021"),
)

# (c) Row striping (≥10 rows and not fully filled by Big Color)
gt = gt.opt_row_striping()

# (d) Stub tint - light grey default
gt = gt.tab_style(
    style=style.fill(color="#F0F0F0"),
    locations=loc.stub(),
)

# Step 4: Heading band
# Has Big Color (Blues density gradient) → use light band
gt = gt.tab_options(
    column_labels_background_color="#EAF0F6",  # washed tint of Blues
    column_labels_font_weight="bold",
)

# Frame - boxed border
gt = gt.tab_options(
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

# Step 6: Titles and notes
gt = (
    gt
    .tab_header(
        title="Fastest-Growing Ontario Towns: Population Density Trends",
        subtitle="Top 15 towns ranked by growth rate (1996–2021), with density changes across census periods"
    )
    .tab_source_note(
        source_note="Density calculated as population divided by land area (km²). "
                    "Population changes are percentage changes calculated from the continuous population series across all census years."
    )
    .tab_source_note(
        source_note="Source: Ontario population census data, 1996–2021."
    )
)

# Step 7: Render
gt.gtsave("table.png", expand=15)
