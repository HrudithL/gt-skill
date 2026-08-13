import pandas as pd
import numpy as np
from great_tables import GT, loc, md, style
from house_table import PALETTE, frame, hairlines, finalize, band, \
    stripe, stub_tint, heatmap, humanize_labels

# Read data
df = pd.read_csv("towny.csv")

# Calculate overall growth rate (1996 to 2021)
df["overall_growth_pct"] = np.where(
    df["population_1996"] > 0,
    (df["population_2021"] - df["population_1996"]) / df["population_1996"],
    np.nan
)

# Select top 15 by overall growth rate, excluding NaN values
df_top15 = df.dropna(subset=["overall_growth_pct"]).nlargest(15, "overall_growth_pct")

# Create a working copy for the display table
display_df = df_top15.copy()

# Prepare data for display
# Select key columns: town name, populations, densities, and period changes
display_df = display_df[[
    "name",
    "population_1996", "population_2001", "population_2006", "population_2011", "population_2016", "population_2021",
    "density_1996", "density_2001", "density_2006", "density_2011", "density_2016", "density_2021",
    "pop_change_1996_2001_pct", "pop_change_2001_2006_pct", "pop_change_2006_2011_pct",
    "pop_change_2011_2016_pct", "pop_change_2016_2021_pct"
]].reset_index(drop=True)

# Rename columns for cleaner display
display_df.columns = [
    "Town",
    "Pop 1996", "Pop 2001", "Pop 2006", "Pop 2011", "Pop 2016", "Pop 2021",
    "Den 1996", "Den 2001", "Den 2006", "Den 2011", "Den 2016", "Den 2021",
    "Δ 96-01 %", "Δ 01-06 %", "Δ 06-11 %", "Δ 11-16 %", "Δ 16-21 %"
]

# Create GT object
gt = GT(display_df, rowname_col="Town")

# Add title and subtitle
gt = gt.tab_header(
    title="Population Growth Trends: Top 15 Fastest-Growing Ontario Towns",
    subtitle="Density changes and period-over-period growth rates, 1996–2021"
)

# Format population columns as integers
pop_cols = ["Pop 1996", "Pop 2001", "Pop 2006", "Pop 2011", "Pop 2016", "Pop 2021"]
gt = gt.fmt_integer(columns=pop_cols)

# Format density columns with 1 decimal
density_cols = ["Den 1996", "Den 2001", "Den 2006", "Den 2011", "Den 2016", "Den 2021"]
gt = gt.fmt_number(columns=density_cols, decimals=1)

# Format period change columns as percentages
change_cols = ["Δ 96-01 %", "Δ 01-06 %", "Δ 06-11 %", "Δ 11-16 %", "Δ 16-21 %"]
gt = gt.fmt_percent(columns=change_cols, decimals=1, scale_values=False, force_sign=True)

# Apply diverging heatmap to period change columns (the hero measure)
gt = heatmap(gt, change_cols, kind="diverging", hue="default")

# Add spanner headers for visual grouping
gt = gt.tab_spanner(label="Population (Count)", columns=pop_cols)
gt = gt.tab_spanner(label="Density (per km²)", columns=density_cols)
gt = gt.tab_spanner(label="Period Growth Rates", columns=change_cols)

# Stub tint and band
gt = band(gt, shade="dark", hue="navy")
gt = stub_tint(gt, hue="navy")

# Striping
gt = stripe(gt)

# Hairlines
gt = hairlines(gt)

# Handle missing values
gt = gt.sub_missing(columns=change_cols, missing_text="—")

# Column width and padding
gt = gt.cols_width(cases={
    "Town": "180px",
    "Pop 1996": "95px", "Pop 2001": "95px", "Pop 2006": "95px",
    "Pop 2011": "95px", "Pop 2016": "95px", "Pop 2021": "95px",
    "Den 1996": "85px", "Den 2001": "85px", "Den 2006": "85px",
    "Den 2011": "85px", "Den 2016": "85px", "Den 2021": "85px",
    "Δ 96-01 %": "90px", "Δ 01-06 %": "90px", "Δ 06-11 %": "90px",
    "Δ 11-16 %": "90px", "Δ 16-21 %": "90px"
})

# Padding
gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px"
)

# Add source notes
gt = gt.tab_source_note(
    source_note="Ranked by overall population growth rate (1996–2021) as percentage change. All municipality types included. Period growth rates shown as percentage changes between consecutive census years."
)
gt = gt.tab_source_note(
    source_note="Source: Statistics Canada census data, 1996–2021."
)

# Frame and finalize
gt = frame(gt)
finalize(gt, path="table.png")
