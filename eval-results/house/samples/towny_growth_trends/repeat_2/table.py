import pandas as pd
import numpy as np
from great_tables import GT, md, loc, style
from house_table import (
    PALETTE, frame, hairlines, finalize, band, stripe, stub_tint,
    heatmap, humanize_labels
)

# Read data
df = pd.read_csv("towny.csv")

# Compute overall population growth % (1996–2021)
df["pop_growth_1996_2021_pct"] = (
    np.where(
        df["population_1996"] > 0,
        (df["population_2021"] - df["population_1996"]) / df["population_1996"],
        np.nan
    )
)

# Filter to top 15 fastest-growing towns by population growth %
top_15 = df.nlargest(15, "pop_growth_1996_2021_pct")[
    ["name", "density_1996", "density_2001", "density_2006", "density_2011",
     "density_2016", "density_2021", "pop_change_1996_2001_pct",
     "pop_change_2001_2006_pct", "pop_change_2006_2011_pct",
     "pop_change_2011_2016_pct", "pop_change_2016_2021_pct",
     "pop_growth_1996_2021_pct"]
].reset_index(drop=True)

# Add rank for reference
top_15["rank"] = range(1, len(top_15) + 1)

# Reorder columns: rank, name, overall growth %, densities, then period changes
col_order = [
    "rank", "name", "pop_growth_1996_2021_pct",
    "density_1996", "density_2001", "density_2006", "density_2011",
    "density_2016", "density_2021",
    "pop_change_1996_2001_pct", "pop_change_2001_2006_pct",
    "pop_change_2006_2011_pct", "pop_change_2011_2016_pct",
    "pop_change_2016_2021_pct"
]
top_15 = top_15[col_order]

# Build the table
gt = GT(top_15, rowname_col="name")

# Title and subtitle
gt = gt.tab_header(
    title="Population Growth Trends: Top 15 Fastest-Growing Ontario Towns",
    subtitle=md("Density across census years (1996–2021) with population growth rates")
)

# Column labels and organization
gt = humanize_labels(
    gt,
    top_15,
    overrides={
        "rank": "Rank",
        "name": "Town",
        "pop_growth_1996_2021_pct": "Total Growth %",
        "density_1996": "1996",
        "density_2001": "2001",
        "density_2006": "2006",
        "density_2011": "2011",
        "density_2016": "2016",
        "density_2021": "2021",
        "pop_change_1996_2001_pct": "1996–2001",
        "pop_change_2001_2006_pct": "2001–2006",
        "pop_change_2006_2011_pct": "2006–2011",
        "pop_change_2011_2016_pct": "2011–2016",
        "pop_change_2016_2021_pct": "2016–2021"
    }
)

# Add spanners for density and period changes
gt = gt.tab_spanner(
    label="Density (persons/km²)",
    columns=["density_1996", "density_2001", "density_2006", "density_2011",
             "density_2016", "density_2021"]
)
gt = gt.tab_spanner(
    label="Population Change %",
    columns=["pop_change_1996_2001_pct", "pop_change_2001_2006_pct",
             "pop_change_2006_2011_pct", "pop_change_2011_2016_pct",
             "pop_change_2016_2021_pct"]
)

# Format columns
gt = gt.fmt_integer(columns="rank")
gt = gt.fmt_number(
    columns=["density_1996", "density_2001", "density_2006", "density_2011",
             "density_2016", "density_2021"],
    decimals=1
)
gt = gt.fmt_percent(
    columns=[
        "pop_growth_1996_2021_pct",
        "pop_change_1996_2001_pct", "pop_change_2001_2006_pct",
        "pop_change_2006_2011_pct", "pop_change_2011_2016_pct",
        "pop_change_2016_2021_pct"
    ],
    decimals=1,
    force_sign=True,
    scale_values=False
)

# Apply heatmap to density columns only (the main story of the request)
gt = heatmap(
    gt,
    ["density_1996", "density_2001", "density_2006", "density_2011",
     "density_2016", "density_2021"],
    kind="sequential",
    hue="neutral"
)

# Leave population growth % columns plain (no color per RULES.md Color Restraint)
# and period change columns plain for comparison visibility

gt = gt.sub_missing(columns=list(top_15.columns), missing_text="—")

# Column widths
gt = gt.cols_width(
    cases={
        "rank": "60px",
        "name": "160px",
        "pop_growth_1996_2021_pct": "110px",
        "density_1996": "90px",
        "density_2001": "90px",
        "density_2006": "90px",
        "density_2011": "90px",
        "density_2016": "90px",
        "density_2021": "90px",
        "pop_change_1996_2001_pct": "110px",
        "pop_change_2001_2006_pct": "110px",
        "pop_change_2006_2011_pct": "110px",
        "pop_change_2011_2016_pct": "110px",
        "pop_change_2016_2021_pct": "110px",
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

# Branding and polish
gt = band(gt, hue="navy")
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

# Source notes: analytical caption first, then provenance
gt = gt.tab_source_note(
    source_note="Ranked by overall population growth percentage (1996–2021). Density columns show persons per km² at each census year; percentage change columns show population growth between consecutive census periods."
)
gt = gt.tab_source_note(
    source_note="Source: provided dataset (Ontario Census 1996–2021)."
)

gt = hairlines(gt)
gt = frame(gt)
finalize(gt)
