"""Ontario towns: population growth trends and density changes (1996–2021)."""

import pandas as pd
import numpy as np
from great_tables import GT, loc, md, style
from house_table import (
    PALETTE, frame, hairlines, finalize, band, stripe, stub_tint, heatmap,
    humanize_labels
)

# Load data
df = pd.read_csv("towny.csv")

# Compute overall growth metric (1996-2021) for ranking
# Using percentage change when baseline is positive
df["growth_rate_1996_2021"] = np.where(
    df["population_1996"] > 0,
    (df["population_2021"] - df["population_1996"]) / df["population_1996"],
    np.nan
)

# Select top 15 fastest-growing by overall population growth rate
top15 = df.nlargest(15, "growth_rate_1996_2021").copy()

# Build display columns: population and density for each census year, plus % changes
columns_to_keep = [
    "name",
    "population_1996", "density_1996",
    "population_2001", "density_2001",
    "pop_change_1996_2001_pct",
    "population_2006", "density_2006",
    "pop_change_2001_2006_pct",
    "population_2011", "density_2011",
    "pop_change_2006_2011_pct",
    "population_2016", "density_2016",
    "pop_change_2011_2016_pct",
    "population_2021", "density_2021",
    "pop_change_2016_2021_pct",
]

display_df = top15[columns_to_keep].reset_index(drop=True)

# Build GT table
gt = GT(display_df, rowname_col="name").tab_header(
    title="Ontario Towns: Population Growth Trends",
    subtitle=md("Top 15 fastest-growing municipalities by population growth rate (1996–2021), "
                "with density and period-to-period changes"),
)

# Add spanners to organize columns by census year
gt = (
    gt
    .tab_spanner(label="1996", columns=["population_1996", "density_1996"])
    .tab_spanner(label="2001", columns=["population_2001", "density_2001", "pop_change_1996_2001_pct"])
    .tab_spanner(label="2006", columns=["population_2006", "density_2006", "pop_change_2001_2006_pct"])
    .tab_spanner(label="2011", columns=["population_2011", "density_2011", "pop_change_2006_2011_pct"])
    .tab_spanner(label="2016", columns=["population_2016", "density_2016", "pop_change_2011_2016_pct"])
    .tab_spanner(label="2021", columns=["population_2021", "density_2021", "pop_change_2016_2021_pct"])
)

# Add vertical dividers at spanner seams (right edge of each census year's density column)
for col in ["density_1996", "density_2001", "density_2006", "density_2011", "density_2016"]:
    gt = gt.tab_style(
        style=style.borders(sides="right", color=PALETTE["neutral"]["vertical_divider"], weight="1px"),
        locations=loc.body(columns=col),
    )
    gt = gt.tab_style(
        style=style.borders(sides="right", color=PALETTE["neutral"]["vertical_divider"], weight="1px"),
        locations=loc.column_labels(columns=col),
    )

# Format columns
gt = (
    gt
    .fmt_integer(columns=[c for c in display_df.columns if c.startswith("population_")])
    .fmt_number(columns=[c for c in display_df.columns if c.startswith("density_")], decimals=1)
    .fmt_percent(
        columns=[c for c in display_df.columns if c.startswith("pop_change_")],
        decimals=1,
        force_sign=True,
    )
)

# Apply labels with humanize helper
overrides = {
    "population_1996": "Pop.", "density_1996": "Density",
    "population_2001": "Pop.", "density_2001": "Density", "pop_change_1996_2001_pct": "Change %",
    "population_2006": "Pop.", "density_2006": "Density", "pop_change_2001_2006_pct": "Change %",
    "population_2011": "Pop.", "density_2011": "Density", "pop_change_2006_2011_pct": "Change %",
    "population_2016": "Pop.", "density_2016": "Density", "pop_change_2011_2016_pct": "Change %",
    "population_2021": "Pop.", "density_2021": "Density", "pop_change_2016_2021_pct": "Change %",
}
gt = humanize_labels(gt, display_df, overrides=overrides)

# Column widths and padding
gt = gt.cols_width(
    cases={
        "name": "160px",
        "population_1996": "70px", "density_1996": "70px",
        "population_2001": "70px", "density_2001": "70px", "pop_change_1996_2001_pct": "75px",
        "population_2006": "70px", "density_2006": "70px", "pop_change_2001_2006_pct": "75px",
        "population_2011": "70px", "density_2011": "70px", "pop_change_2006_2011_pct": "75px",
        "population_2016": "70px", "density_2016": "70px", "pop_change_2011_2016_pct": "75px",
        "population_2021": "70px", "density_2021": "70px", "pop_change_2016_2021_pct": "75px",
    }
)

gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Big Color: heatmap for population growth percentage changes (diverging, RdYlGn)
# The per-period percentage changes show direction of growth; negative means decline
pct_cols = [c for c in display_df.columns if c.startswith("pop_change_")]
gt = heatmap(gt, pct_cols, kind="diverging", hue="default")

# Branding: heading band (house default is dark navy)
gt = band(gt, hue="navy")

# Small-color polish: striping + stub tint
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

# Source notes: analytical caption (the chosen definition) first, then provenance
gt = (
    gt
    .tab_source_note(
        source_note="Ranked by overall population growth rate (1996–2021) as percentage change. "
        "Density in persons per km². All municipality types included."
    )
    .tab_source_note(
        source_note="Source: Statistics Canada Census data, 1996–2021."
    )
)

# Finalize: frame + hairlines + render
gt = hairlines(gt)
gt = frame(gt)
finalize(gt, path="table.png")
