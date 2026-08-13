import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc
from gt_consistency import PALETTE, heatmap, band, finalize, frame, hairlines, stripe, stub_tint

# Step 1: Load and clean data
df = pd.read_csv("towny.csv")

# Calculate overall growth rate from 1996 to 2021 to identify fastest-growing towns
df["total_growth_pct"] = (df["population_2021"] - df["population_1996"]) / df["population_1996"]

# Get top 15 fastest-growing towns
top_15 = df.nlargest(15, "total_growth_pct")

# Step 2: Select and organize columns
# Show town name, then density across years, then percent changes across periods
display_df = top_15[
    [
        "name",
        "density_1996",
        "density_2001",
        "density_2006",
        "density_2011",
        "density_2016",
        "density_2021",
        "pop_change_1996_2001_pct",
        "pop_change_2001_2006_pct",
        "pop_change_2006_2011_pct",
        "pop_change_2011_2016_pct",
        "pop_change_2016_2021_pct",
    ]
].reset_index(drop=True)

# Rename columns for clarity
display_df.columns = [
    "Town",
    "Density 1996",
    "Density 2001",
    "Density 2006",
    "Density 2011",
    "Density 2016",
    "Density 2021",
    "1996-2001",
    "2001-2006",
    "2006-2011",
    "2011-2016",
    "2016-2021",
]

# Define column groups
density_cols = [
    "Density 1996",
    "Density 2001",
    "Density 2006",
    "Density 2011",
    "Density 2016",
    "Density 2021",
]
pct_cols = [
    "1996-2001",
    "2001-2006",
    "2006-2011",
    "2011-2016",
    "2016-2021",
]

# Step 3 & 4: Build the table with structure
gt = (
    GT(display_df, rowname_col="Town")
    .fmt_number(columns=density_cols, decimals=1)
    .fmt_percent(columns=pct_cols, decimals=1)
    # Column spanners
    .tab_spanner(label="Population Density (persons/km²)", columns=density_cols)
    .tab_spanner(label="Population Change (%)", columns=pct_cols)
)

# Step 3: Apply color fills using heatmap helper
gt = heatmap(gt, density_cols, kind="sequential", hue="neutral")
gt = heatmap(gt, pct_cols, kind="sequential", hue="positive")

# Column dividers at spanner boundaries
gt = (
    gt.tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.body(columns="Density 2021"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.column_labels(columns="Density 2021"),
    )
)

# Step 5: Apply small-color polish
gt = band(gt)
gt = hairlines(gt)
gt = stripe(gt)
gt = stub_tint(gt)
gt = frame(gt)

# Compact layout: column width sizing and padding
gt = (
    gt.cols_width(
        cases={
            "Town": "180px",
            "Density 1996": "90px",
            "Density 2001": "90px",
            "Density 2006": "90px",
            "Density 2011": "90px",
            "Density 2016": "90px",
            "Density 2021": "90px",
            "1996-2001": "85px",
            "2001-2006": "85px",
            "2006-2011": "85px",
            "2011-2016": "85px",
            "2016-2021": "85px",
        }
    )
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
)

# Step 6: Titles and annotations
gt = (
    gt.tab_header(
        title="Ontario's Fastest-Growing Towns: Population Density Trends (1996–2021)",
        subtitle="Top 15 towns ranked by total population growth; density and inter-census percent changes across all periods",
    )
    .tab_source_note(
        md(
            "**Finding:** Fastest-growing means highest percent change across the full 1996–2021 span, not averaged across periods."
        )
    )
    .tab_source_note(
        md(
            "**Source:** Statistics Canada Census of Population and Housing, 1996–2021. Density in persons per square kilometre; percent change calculated as (end − start) / start for each inter-census period."
        )
    )
)

# Step 7: Render to PNG
finalize(gt)
