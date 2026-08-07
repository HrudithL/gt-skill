import pandas as pd
import numpy as np
from great_tables import GT, style, loc
from gt_consistency import frame, finalize

# Step 1: Load and clean the data
df = pd.read_csv("towny.csv")

# Convert population columns to numeric, handling missing values
pop_cols = ["population_1996", "population_2001", "population_2006", "population_2011", "population_2016", "population_2021"]
for col in pop_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Calculate overall growth rate from 1996 to 2021
df["overall_growth"] = ((df["population_2021"] - df["population_1996"]) / df["population_1996"]).fillna(0)

# Filter out rows with missing 1996 or 2021 data
df_clean = df[(df["population_1996"].notna()) & (df["population_2021"].notna())].copy()

# Sort by overall growth rate and get top 15
top_15 = df_clean.nlargest(15, "overall_growth")[["name", "population_1996", "population_2001", "population_2006",
                                                     "population_2011", "population_2016", "population_2021",
                                                     "density_1996", "density_2001", "density_2006",
                                                     "density_2011", "density_2016", "density_2021",
                                                     "pop_change_1996_2001_pct", "pop_change_2001_2006_pct",
                                                     "pop_change_2006_2011_pct", "pop_change_2011_2016_pct",
                                                     "pop_change_2016_2021_pct"]].copy()

# Prepare the display data with rounded values
display_data = top_15.copy()
display_data = display_data.rename(columns={"name": "Town"})

# Round population to whole numbers
pop_cols_display = ["population_1996", "population_2001", "population_2006", "population_2011", "population_2016", "population_2021"]
for col in pop_cols_display:
    display_data[col] = display_data[col].round(0).astype("Int64")

# Round density to 2 decimal places
density_cols_display = ["density_1996", "density_2001", "density_2006", "density_2011", "density_2016", "density_2021"]
for col in density_cols_display:
    display_data[col] = display_data[col].round(2)

# Round percentage changes (already in decimal form, convert to percent)
pct_cols_display = ["pop_change_1996_2001_pct", "pop_change_2001_2006_pct", "pop_change_2006_2011_pct",
                    "pop_change_2011_2016_pct", "pop_change_2016_2021_pct"]
for col in pct_cols_display:
    display_data[col] = display_data[col].round(4)

# Reorder columns for logical grouping: Population first, then changes, then density
display_data = display_data[["Town"] + pop_cols_display + pct_cols_display + density_cols_display]

# Reset index for clean display
display_data = display_data.reset_index(drop=True)

# Step 3: Calculate domain for Big Color (population columns)
lo = float(np.nanmin(display_data[pop_cols_display].to_numpy()))
hi = float(np.nanmax(display_data[pop_cols_display].to_numpy()))

# Build the table
gt = (
    GT(display_data, rowname_col="Town")
    # Population columns with gradient
    .tab_spanner(label="Population", columns=pop_cols_display)
    .tab_spanner(label="Population Change %", columns=pct_cols_display)
    .tab_spanner(label="Density (per km²)", columns=density_cols_display)
    # Format population as integers
    .fmt_integer(columns=pop_cols_display)
    # Format density with 2 decimals
    .fmt_number(columns=density_cols_display, decimals=2)
    # Format percentage changes (convert from decimal to percent)
    .fmt_percent(columns=pct_cols_display)
    # Apply gradient color to population columns
    .data_color(
        columns=pop_cols_display,
        palette="Blues",
        domain=[lo, hi],
        truncate=False,
        na_color="#808080",
    )
    # Column label bottom rule
    .tab_options(
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Cell borders
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
    # Column group dividers (after each spanner group)
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.body(columns=pop_cols_display[-1]),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.column_labels(columns=pop_cols_display[-1]),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.body(columns=pct_cols_display[-1]),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.column_labels(columns=pct_cols_display[-1]),
    )
    # Row striping (≥15 rows)
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    # Stub tint (Blues hue wash)
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # Heading band (light tint for Blues Big Color)
    .tab_options(heading_background_color="#EAF0F6")
    # Title and subtitle
    .tab_header(
        title="Ontario Towns: Population Growth Trends (1996–2021)",
        subtitle="Top 15 Fastest-Growing Municipalities with Density Changes Across Census Years"
    )
    # Source note
    .tab_source_note("Data source: Ontario Census, 1996–2021")
)

# Apply frame (border and margin)
gt = frame(gt)

# Render to PNG with wider viewport
finalize(gt, vwidth=3000, vheight=1400)
