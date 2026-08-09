import pandas as pd
import numpy as np
from great_tables import GT, style, loc
from gt_consistency import PALETTE, frame, finalize, heatmap, band, stripe, stub_tint

# STEP 1: Data cleaning and preparation
df = pd.read_csv("towny.csv")

# Calculate total population growth percentage from 1996 to 2021
df["total_growth_pct"] = ((df["population_2021"] - df["population_1996"]) / df["population_1996"]).round(4)

# Sort by total growth and get top 15 fastest-growing towns
top15 = df.nlargest(15, "total_growth_pct").copy()
top15 = top15.reset_index(drop=True)

# STEP 2: Select and organize columns
# We want: town name (stub), density for each year, and % change for each period
display_cols = [
    "name",
    "density_1996", "density_2001", "density_2006", "density_2011", "density_2016", "density_2021",
    "pop_change_1996_2001_pct", "pop_change_2001_2006_pct", "pop_change_2006_2011_pct",
    "pop_change_2011_2016_pct", "pop_change_2016_2021_pct"
]

display_df = top15[display_cols].copy()

# Format the data: ensure numeric columns are properly typed
density_cols = ["density_1996", "density_2001", "density_2006", "density_2011", "density_2016", "density_2021"]
pct_cols = ["pop_change_1996_2001_pct", "pop_change_2001_2006_pct", "pop_change_2006_2011_pct",
            "pop_change_2011_2016_pct", "pop_change_2016_2021_pct"]

for col in density_cols + pct_cols:
    display_df[col] = pd.to_numeric(display_df[col], errors="coerce")

# STEP 3: Build the table
gt = (
    GT(display_df, rowname_col="name")
    # Format columns
    .fmt_number(columns=density_cols, decimals=1, use_seps=True)
    .fmt_percent(columns=pct_cols, decimals=1, scale_values=True)
    .sub_missing(columns=density_cols + pct_cols, missing_text="—")
    # Column spanners to group density years and periods
    .tab_spanner(label="Density (persons/km²)", columns=density_cols)
    .tab_spanner(label="Population % Change", columns=pct_cols)
    # Titles and footer
    .tab_header(
        title="Population Growth in Ontario's Fastest-Growing Towns",
        subtitle="Density changes and growth rates across Census periods, 1996–2021"
    )
    .tab_source_note(
        source_note="Fastest-growing is measured by highest percent population change from 1996 to 2021 across the full span."
    )
    .tab_source_note(
        source_note="Source: Statistics Canada Census subdivisions, 1996–2021."
    )
)

# STEP 3: Color the density columns with Blues gradient (hero measure)
gt = heatmap(gt, columns=density_cols, kind="sequential", hue="neutral")

# STEP 4: Apply the heading band (light shade with Big Color present)
gt = band(gt, shade="light", hue="navy")

# STEP 5: Apply small-color polish
# Hairlines between rows
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color=PALETTE["neutral"]["hairline"],
    table_body_hlines_width="1px",
)

# Column group dividers (right border on last col of each group)
gt = (
    gt.tab_style(
        style=style.borders(sides="right", color=PALETTE["neutral"]["vertical_divider"], weight="1px"),
        locations=loc.body(columns="density_2021"),
    )
    .tab_style(
        style=style.borders(sides="right", color=PALETTE["neutral"]["vertical_divider"], weight="1px"),
        locations=loc.column_labels(columns="density_2021"),
    )
)

# Row striping (≥10 rows and not fully filled by Big Color)
gt = stripe(gt)

# Stub tint
gt = stub_tint(gt, hue="grey")

# STEP 5/7: Apply frame and finalize
gt = frame(gt)
finalize(gt, "table.png")
