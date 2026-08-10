import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Load and clean the data
df = pd.read_csv("towny.csv")

# Calculate overall population growth 1996-2021
df["growth_1996_2021"] = (df["population_2021"] - df["population_1996"]) / df["population_1996"]

# Sort by growth and get top 15
top_15 = df.nlargest(15, "growth_1996_2021").copy()

# Reset index for cleaner display
top_15 = top_15.reset_index(drop=True)

# Step 2: Organize columns for the table
# Select columns: name, all density columns, and all percentage change columns
display_cols = ["name"]
density_cols = ["density_1996", "density_2001", "density_2006", "density_2011", "density_2016", "density_2021"]
pct_cols = ["pop_change_1996_2001_pct", "pop_change_2001_2006_pct", "pop_change_2006_2011_pct",
            "pop_change_2011_2016_pct", "pop_change_2016_2021_pct"]

table_df = top_15[display_cols + density_cols + pct_cols].copy()

# Rename columns for display
table_df.columns = ["Town"] + [f"D-{year}" for year in ["1996", "2001", "2006", "2011", "2016", "2021"]] + \
                   [f"Δ {period}" for period in ["96-01", "01-06", "06-11", "11-16", "16-21"]]

# Step 3: Determine Big Color measures
# Density columns qualify as ordered magnitudes (≥5 rows, 15 towns shown)
# Percentage changes are also ordered magnitudes
# Priority: user named "density changes... with percentage changes" - both are named
# Using the tie-break rule: density is in the topic clause ("density changes"), so color density
# Percentage changes are secondary comparison, should be bold-uncolored

density_display_cols = [f"D-{year}" for year in ["1996", "2001", "2006", "2011", "2016", "2021"]]
pct_display_cols = [f"Δ {period}" for period in ["96-01", "01-06", "06-11", "11-16", "16-21"]]

# Step 4: Heading band
# Table has Big Color (density gradient) → use LIGHT band
# Palette by semantic: density is neutral magnitude → use Blues
# Get domain for density columns
density_vals = table_df[density_display_cols].to_numpy()
density_lo = float(np.nanmin(density_vals))
density_hi = float(np.nanmax(density_vals))

# Create GT and apply formatting
gt = (
    GT(table_df, rowname_col="Town")
    .fmt_number(columns=density_display_cols, decimals=2)
    .fmt_percent(columns=pct_display_cols, decimals=1, scale_values=True)
    .data_color(
        columns=density_display_cols,
        palette="Blues",
        domain=[density_lo, density_hi],
        truncate=False,
        na_color="#808080",
    )
    # Make percentage columns bold (secondary measures)
    .tab_style(
        style=style.text(weight="bold"),
        locations=loc.body(columns=pct_display_cols),
    )
)

# Step 5: Small Color polish
# (a) Cell borders - hairlines between rows
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
    column_labels_border_bottom_color="#CCCCCC",
    column_labels_border_bottom_width="2px",
)

# (b) Column-group vertical dividers - separate density and percentage change groups
gt = (
    gt.tab_spanner(label="Population Density (per km²)", columns=density_display_cols)
    .tab_spanner(label="Population Change (%)", columns=pct_display_cols)
)

# Add divider at the boundary between density and percentage change groups
gt = gt.tab_style(
    style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
    locations=loc.body(columns=[density_display_cols[-1]]),
)
gt = gt.tab_style(
    style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
    locations=loc.column_labels(columns=[density_display_cols[-1]]),
)

# Check row count for striping gate: 15 rows, density columns fully filled → striping NOT needed per the rule
# But we still add a subtle stub tint for visual anchoring
gt = gt.tab_style(
    style=style.fill(color="#EAF0F6"),  # Washed Navy tint (Forest for growth data, but Navy is default)
    locations=loc.stub(),
)

# (f) Titles and annotations
gt = (
    gt.tab_header(
        title="Top 15 Fastest-Growing Ontario Towns",
        subtitle="Population Density Trends and Growth Rates Across Census Years (1996–2021)",
    )
    .tab_source_note(
        source_note="Density measured in persons per km². Percentage changes reflect population growth between consecutive census periods.",
    )
    .tab_source_note(
        source_note="Source: towny.csv - Ontario Census Data (1996-2021)",
    )
)

# Step 6: Frame and margins
gt = gt.tab_options(
    table_border_left_color="#E0E0E0",
    table_border_left_width="1px",
    table_border_right_color="#E0E0E0",
    table_border_right_width="1px",
    table_border_top_color="#E0E0E0",
    table_border_top_width="1px",
    table_border_bottom_color="#E0E0E0",
    table_border_bottom_width="1px",
)

# Step 7: Render
gt.gtsave("table.png", zoom=1.0, expand=15)
print("Table rendered successfully to table.png")
