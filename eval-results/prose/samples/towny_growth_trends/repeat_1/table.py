import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc

# Step 1: Load and clean data
df = pd.read_csv("towny.csv")

# Calculate overall growth rate from 1996 to 2021
df["overall_growth"] = (df["population_2021"] - df["population_1996"]) / df["population_1996"]

# Get top 15 fastest-growing towns
top_15 = df.nlargest(15, "overall_growth").copy()

# Select columns for display: name, all density columns, and percentage change columns
density_cols = ["density_1996", "density_2001", "density_2006", "density_2011", "density_2016", "density_2021"]
change_cols = ["pop_change_1996_2001_pct", "pop_change_2001_2006_pct", "pop_change_2006_2011_pct", "pop_change_2011_2016_pct", "pop_change_2016_2021_pct"]

# Create the display dataframe
display_df = top_15[["name"] + density_cols + change_cols].reset_index(drop=True).copy()

# Define column names for display
density_display = [f"Density {y}" for y in ["1996", "2001", "2006", "2011", "2016", "2021"]]
change_display = [f"% Change\n{p1}-{p2}" for p1, p2 in [("1996", "2001"), ("2001", "2006"), ("2006", "2011"), ("2011", "2016"), ("2016", "2021")]]

# Rename columns for display
display_df.columns = ["Town"] + density_display + change_display

# Data-driven domain for density columns (all 6 years)
density_data = display_df[density_display].to_numpy()
density_min = float(np.nanmin(density_data))
density_max = float(np.nanmax(density_data))

# Data-driven domain for percentage changes
change_data = display_df[change_display].to_numpy()
change_min = float(np.nanmin(change_data))
change_max = float(np.nanmax(change_data))

# Step 2: Organize columns
# Stub is "Town" (identifier column)
# Primary colored measures: density columns (outer edge - right side before changes)
# Secondary measures: percentage changes (also get color as distinct dimension)

# Step 3: Big Color - Apply gradient fill to both measures (density + percentage change)
# Both qualify: density is a level, percentage change is a rate of change

# Step 4, 5, 6: Build the table with formatting and styling
gt = (
    GT(display_df, rowname_col="Town")
    # Format density columns as numbers with 1 decimal
    .fmt_number(
        columns=density_display,
        decimals=1
    )
    # Format percentage change columns with % symbol
    .fmt_percent(
        columns=change_display,
        decimals=1,
        scale_values=False  # Already in 0-1 scale
    )
    # Big Color: Density gradient (neutral magnitude -> Blues)
    .data_color(
        columns=density_display,
        palette="Blues",
        domain=[density_min, density_max],
        truncate=False,
        na_color="#808080"
    )
    # Big Color: Percentage change gradient (sequential, positive magnitude -> Greens for growth)
    .data_color(
        columns=change_display,
        palette="Greens",
        domain=[change_min, change_max],
        truncate=False,
        na_color="#808080"
    )
    # Step 4: Heading band (fixed branding)
    .tab_header(
        title="Top 15 Fastest-Growing Ontario Towns",
        subtitle="Population Density and Growth Trends Across Census Years (1996–2021)"
    )
    # Column labels
    .cols_label(
        **{col: col for col in display_df.columns}
    )
    # Step 5: Small Color polish
    .tab_options(
        # Compact layout padding (from small_color.md)
        data_row_padding="8px",
        data_row_padding_horizontal="12px",
        column_labels_padding="12px",
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        table_width="100%"
    )
    # Row striping (required unless body is 100% color-covered)
    .opt_row_striping()
    # Stub tint (fixed branding)
    .tab_style(
        style.fill(color="#EAF0F6"),
        loc.stub()
    )
    # Header band styling (dark navy, bold, white text)
    .tab_style(
        style.fill(color="#08306B"),
        loc.header()
    )
    .tab_style(
        style.text(color="white", weight="bold"),
        loc.header()
    )
    # Column label bottom rule
    .tab_style(
        style.borders(sides="bottom", color="#CCCCCC", weight="2px"),
        loc.column_labels()
    )
    # Step 6: Titles & annotations (footer)
    .tab_source_note(
        md("**Definition:** Density = population per km². Percentage changes computed as (year_end - year_start) / year_start. Towns ranked by overall growth (1996–2021).")
    )
    .tab_source_note(
        md("**Source:** Canadian Census data (1996–2021)")
    )
)

# Render
gt.gtsave("table.png")
print("✓ Table rendered to table.png")
