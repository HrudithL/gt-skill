import pandas as pd
import numpy as np
from great_tables import GT, loc, md, style
from house_table import (
    PALETTE, frame, hairlines, finalize, band, stripe, stub_tint,
    heatmap, group_emphasis, humanize_labels
)

df = pd.read_csv("towny.csv")

# Calculate overall population growth % from 1996 to 2021 (for ranking)
df["total_growth_pct"] = np.where(
    df["population_1996"] > 0,
    (df["population_2021"] - df["population_1996"]) / df["population_1996"],
    np.nan
)

# Select top 15 by overall growth
top_15 = df.nlargest(15, "total_growth_pct")

# Calculate inter-census density change percentages
# Density change = (density_end - density_start) / density_start
def calc_density_change_pct(start_col, end_col):
    return np.where(
        top_15[start_col] > 0,
        (top_15[end_col] - top_15[start_col]) / top_15[start_col],
        np.nan
    )

top_15 = top_15.copy()
top_15["density_change_1996_2001_pct"] = calc_density_change_pct("density_1996", "density_2001")
top_15["density_change_2001_2006_pct"] = calc_density_change_pct("density_2001", "density_2006")
top_15["density_change_2006_2011_pct"] = calc_density_change_pct("density_2006", "density_2011")
top_15["density_change_2011_2016_pct"] = calc_density_change_pct("density_2011", "density_2016")
top_15["density_change_2016_2021_pct"] = calc_density_change_pct("density_2016", "density_2021")

# Add rank column
top_15["rank"] = range(1, 16)

# Select and order columns for display
display_cols = [
    "name",
    "total_growth_pct",
    "rank",
    "density_1996",
    "density_2001",
    "density_change_1996_2001_pct",
    "density_2006",
    "density_change_2001_2006_pct",
    "density_2011",
    "density_change_2006_2011_pct",
    "density_2016",
    "density_change_2011_2016_pct",
    "density_2021",
    "density_change_2016_2021_pct",
]

display_df = top_15[display_cols].reset_index(drop=True)

# Build table
gt = GT(display_df, rowname_col="name")

gt = gt.tab_header(
    title="Population Growth Trends in Ontario's Fastest-Growing Towns",
    subtitle=md("Top 15 towns by overall population growth (1996–2021), with density evolution across census periods"),
)

# Spanner groups for density values and inter-census changes
gt = gt.tab_spanner(label="1996–2001", columns=["density_1996", "density_2001", "density_change_1996_2001_pct"])
gt = gt.tab_spanner(label="2001–2006", columns=["density_2006", "density_change_2001_2006_pct"])
gt = gt.tab_spanner(label="2006–2011", columns=["density_2011", "density_change_2006_2011_pct"])
gt = gt.tab_spanner(label="2011–2016", columns=["density_2016", "density_change_2011_2016_pct"])
gt = gt.tab_spanner(label="2016–2021", columns=["density_2021", "density_change_2016_2021_pct"])

# Add vertical dividers at spanner boundaries
divider_color = PALETTE["neutral"]["vertical_divider"]
divider_cols = ["density_2001", "density_2006", "density_2011", "density_2016", "density_2021"]
for col in divider_cols:
    gt = gt.tab_style(
        style=style.borders(sides="right", color=divider_color, weight="1px"),
        locations=loc.body(columns=col),
    )
    gt = gt.tab_style(
        style=style.borders(sides="right", color=divider_color, weight="1px"),
        locations=loc.column_labels(columns=col),
    )

# Format columns
gt = gt.fmt_percent(columns="total_growth_pct", decimals=1, force_sign=True)
gt = gt.fmt_integer(columns="rank")
gt = gt.fmt_number(columns=[c for c in display_cols if c.startswith("density_")], decimals=1)
gt = gt.fmt_percent(
    columns=[c for c in display_cols if "change" in c],
    decimals=1,
    force_sign=True,
    scale_values=False
)

# Humanize labels
label_overrides = {
    "total_growth_pct": "Total Growth %",
    "rank": "Rank",
    "density_1996": "1996",
    "density_2001": "2001",
    "density_change_1996_2001_pct": "Change %",
    "density_2006": "2006",
    "density_change_2001_2006_pct": "Change %",
    "density_2011": "2011",
    "density_change_2006_2011_pct": "Change %",
    "density_2016": "2016",
    "density_change_2011_2016_pct": "Change %",
    "density_2021": "2021",
    "density_change_2016_2021_pct": "Change %",
}
gt = humanize_labels(gt, display_df, overrides=label_overrides)

# Handle missing values
change_cols = [c for c in display_cols if "change" in c]
gt = gt.sub_missing(columns=change_cols, missing_text="—")

# Color the inter-census density change percentages (diverging heatmap)
# Color all change columns together under one shared domain
gt = heatmap(gt, change_cols, kind="diverging", hue="default")

# Column widths
gt = gt.cols_width(
    cases={
        "name": "140px",
        "total_growth_pct": "90px",
        "rank": "60px",
        "density_1996": "80px",
        "density_2001": "80px",
        "density_change_1996_2001_pct": "85px",
        "density_2006": "80px",
        "density_change_2001_2006_pct": "85px",
        "density_2011": "80px",
        "density_change_2006_2011_pct": "85px",
        "density_2016": "80px",
        "density_change_2011_2016_pct": "85px",
        "density_2021": "80px",
        "density_change_2016_2021_pct": "85px",
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

# Branding and polish
gt = band(gt, hue="navy")
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

# Source notes: analytical caption first, then provenance
gt = gt.tab_source_note(
    source_note="Ranked by total population growth percentage (1996–2021) for all Ontario municipalities. Density figures in persons per km². Inter-census changes (rightmost column of each period) are percentage changes in population density between census years."
)
gt = gt.tab_source_note(
    source_note="Source: towny.csv — Statistics Canada census data, 1996–2021."
)

gt = hairlines(gt)
gt = frame(gt)
finalize(gt, path="table.png")
