import numpy as np
import pandas as pd
from great_tables import GT, md, loc, style
from house_table import (
    PALETTE, frame, hairlines, finalize, band, stripe, stub_tint, heatmap,
    humanize_labels
)

# Read and prepare data
df = pd.read_csv("towny.csv")

# Calculate overall growth from 1996 to 2021 as percentage
# Guard against zero/negative baselines as per RULES.md
df["overall_growth_pct"] = np.where(
    df["population_1996"] > 0,
    (df["population_2021"] - df["population_1996"]) / df["population_1996"],
    np.nan
)

# Select top 15 fastest-growing towns (by overall growth percentage)
top_15 = df.nlargest(15, "overall_growth_pct").copy()
top_15 = top_15.reset_index(drop=True)

# Extract density columns for all 6 census years
density_cols = [
    "density_1996", "density_2001", "density_2006",
    "density_2011", "density_2016", "density_2021"
]

# Calculate period-over-period percentage changes in density
# Guard baselines with np.where to handle zero/negative values
pct_change_cols = {}
periods = [
    ("1996", "2001"), ("2001", "2006"), ("2006", "2011"),
    ("2011", "2016"), ("2016", "2021")
]

for start_year, end_year in periods:
    col_name = f"density_change_{start_year}_{end_year}_pct"
    start_col = f"density_{start_year}"
    end_col = f"density_{end_year}"
    top_15[col_name] = np.where(
        top_15[start_col] > 0,
        (top_15[end_col] - top_15[start_col]) / top_15[start_col],
        np.nan
    )
    pct_change_cols[col_name] = f"{start_year}–{end_year}"

# Build the table with name as stub
display_df = top_15[["name"] + density_cols + list(pct_change_cols.keys())].copy()
display_df = display_df.rename(columns={
    "name": "Town",
    "density_1996": "1996",
    "density_2001": "2001",
    "density_2006": "2006",
    "density_2011": "2011",
    "density_2016": "2016",
    "density_2021": "2021",
})
display_df = display_df.rename(columns=pct_change_cols)

# Create GT object
gt = GT(display_df, rowname_col="Town")

# Header
gt = gt.tab_header(
    title="Population Density Trends: Ontario's Fastest-Growing Towns",
    subtitle=md("Top 15 towns ranked by population growth 1996–2021, showing density by census year and period-over-period changes"),
)

# Spanners for density values and changes
gt = gt.tab_spanner(
    label="Population Density (per km²)",
    columns=["1996", "2001", "2006", "2011", "2016", "2021"]
)
gt = gt.tab_spanner(
    label="Density Change (%)",
    columns=list(pct_change_cols.values())
)

# Formatting
# Density values: 1 decimal place
for col in ["1996", "2001", "2006", "2011", "2016", "2021"]:
    gt = gt.fmt_number(columns=col, decimals=1)

# Percentage changes: 1 decimal place with force_sign
for col in pct_change_cols.values():
    gt = gt.fmt_percent(columns=col, decimals=1, scale_values=False, force_sign=True)

# Missing value substitution
all_numeric = ["1996", "2001", "2006", "2011", "2016", "2021"] + list(pct_change_cols.values())
gt = gt.sub_missing(columns=all_numeric, missing_text="—")

# Humanize labels
gt = humanize_labels(gt, display_df, overrides={})

# Column widths
gt = gt.cols_width(
    cases={
        "Town": "160px",
        "1996": "90px",
        "2001": "90px",
        "2006": "90px",
        "2011": "90px",
        "2016": "90px",
        "2021": "90px",
        "1996–2001": "105px",
        "2001–2006": "105px",
        "2006–2011": "105px",
        "2011–2016": "105px",
        "2016–2021": "105px",
    }
)

# Padding
gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Vertical divider between density values and changes
gt = gt.tab_style(
    style=style.borders(sides="right", color=PALETTE["neutral"]["vertical_divider"], weight="1px"),
    locations=loc.body(columns="2021"),
)
gt = gt.tab_style(
    style=style.borders(sides="right", color=PALETTE["neutral"]["vertical_divider"], weight="1px"),
    locations=loc.column_labels(columns="2021"),
)

# Big Color: heatmap the density change percentages (diverging, signed)
gt = heatmap(gt, list(pct_change_cols.values()), kind="diverging", hue="default")

# Branding
gt = band(gt, hue="navy")
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

# Frame and hairlines
gt = frame(gt)
gt = hairlines(gt)

# Source notes: analytical caption (definition) first, then provenance
gt = gt.tab_source_note(
    source_note=md("Ranked by overall population growth (1996–2021), all municipality types. Density changes are period-over-period percentage changes in population density (persons per km²)."),
)
gt = gt.tab_source_note(
    source_note="Source: provided dataset (Ontario municipalities, six census years: 1996–2021).",
)

# Finalize and render
finalize(gt, path="table.png")
print("Table rendered to table.png")
