import pandas as pd
import numpy as np
from great_tables import GT, style, loc
from gt_consistency import heatmap, band, stripe, stub_tint, frame, hairlines, finalize, PALETTE

# Step 1: Load and clean data
df = pd.read_csv("./towny.csv")

# Calculate overall population growth from 1996 to 2021
df["overall_growth"] = (df["population_2021"] - df["population_1996"]) / df["population_1996"]

# Select top 15 fastest-growing towns
top15 = df.nlargest(15, "overall_growth")[["name", "population_1996", "population_2021", "density_1996", "density_2001", "density_2006", "density_2011", "density_2016", "density_2021"]].copy()

# Calculate percentage changes in density between periods
top15["density_change_1996_2001"] = ((top15["density_2001"] - top15["density_1996"]) / top15["density_1996"]) * 100
top15["density_change_2001_2006"] = ((top15["density_2006"] - top15["density_2001"]) / top15["density_2001"]) * 100
top15["density_change_2006_2011"] = ((top15["density_2011"] - top15["density_2006"]) / top15["density_2006"]) * 100
top15["density_change_2011_2016"] = ((top15["density_2016"] - top15["density_2011"]) / top15["density_2011"]) * 100
top15["density_change_2016_2021"] = ((top15["density_2021"] - top15["density_2016"]) / top15["density_2016"]) * 100

# Guard against zero/negative baselines - mask invalid results
for col in ["density_change_1996_2001", "density_change_2001_2006", "density_change_2006_2011", "density_change_2011_2016", "density_change_2016_2021"]:
    top15[col] = top15[col].replace([np.inf, -np.inf], np.nan)

# Reset index for clean display
top15 = top15.reset_index(drop=True)

# Select columns for display
display_cols = [
    "name",
    "density_1996", "density_2001", "density_2006", "density_2011", "density_2016", "density_2021",
    "density_change_1996_2001", "density_change_2001_2006", "density_change_2006_2011",
    "density_change_2011_2016", "density_change_2016_2021"
]
display_df = top15[display_cols].copy()

# Rename columns for display
display_df.columns = [
    "Town",
    "1996", "2001", "2006", "2011", "2016", "2021",
    "1996-2001", "2001-2006", "2006-2011", "2011-2016", "2016-2021"
]

# Step 2: Organize columns - identify density and change measures
density_cols = ["1996", "2001", "2006", "2011", "2016", "2021"]
change_cols = ["1996-2001", "2001-2006", "2006-2011", "2011-2016", "2016-2021"]

# Build table with stub
gt = GT(display_df, rowname_col="Town")

# Add column spanners for logical grouping
gt = gt.tab_spanner(label="Population Density (persons/km²)", columns=density_cols)
gt = gt.tab_spanner(label="Density Change (%)", columns=change_cols)

# Format density columns as numbers with 1 decimal
gt = gt.fmt_number(columns=density_cols, decimals=1, use_seps=True)

# Format change columns with 1 decimal and force sign for zero-crossing columns
gt = gt.fmt_number(columns=change_cols, decimals=1, use_seps=False, force_sign=True)

# Handle missing values
gt = gt.sub_missing(columns=list(display_df.columns), missing_text="—")

# Step 3: Color the measures using heatmap helper
# Density measures - use sequential Blues (neutral magnitude)
gt = heatmap(gt, density_cols, kind="sequential", hue="neutral")

# Change measures - use diverging palette (can be positive or negative)
gt = heatmap(gt, change_cols, kind="diverging", hue="default")

# Step 4: Apply heading band
gt = band(gt)

# Step 5: Small Color polish
# Column dividers at spanner seams
gt = (
    gt.tab_style(
        style=style.borders(sides="right", color=PALETTE["neutral"]["vertical_divider"], weight="1px"),
        locations=loc.body(columns="2021"),  # last col of density group
    )
    .tab_style(
        style=style.borders(sides="right", color=PALETTE["neutral"]["vertical_divider"], weight="1px"),
        locations=loc.column_labels(columns="2021"),  # matching seam in header
    )
)

# Row striping
gt = stripe(gt)

# Stub tint
gt = stub_tint(gt)

# Hairlines
gt = hairlines(gt)

# Compact layout padding
gt = gt.cols_width(cases={
    "Town": "140px",
    "1996": "90px",
    "2001": "90px",
    "2006": "90px",
    "2011": "90px",
    "2016": "90px",
    "2021": "90px",
    "1996-2001": "100px",
    "2001-2006": "100px",
    "2006-2011": "100px",
    "2011-2016": "100px",
    "2016-2021": "100px",
})

gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Step 6: Titles & annotations
gt = gt.tab_header(
    title="Ontario Towns: Population Density Trends & Growth Rates",
    subtitle="Top 15 Fastest-Growing Communities (1996–2021)"
)

# Two separate footer calls for proper attribution
gt = (
    gt.tab_source_note(source_note="Fastest-growing means highest percent change in population from 1996 to 2021. Density = population ÷ land area (persons per km²).")
    .tab_source_note(source_note="Source: Statistics Canada Census subdivisions, 1996–2021.")
)

# Step 7: Frame and finalize
gt = frame(gt)
finalize(gt)
