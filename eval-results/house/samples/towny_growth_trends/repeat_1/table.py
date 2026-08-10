import pandas as pd
import numpy as np
from great_tables import GT, loc, md, style
from house_table import (
    PALETTE, frame, hairlines, finalize, band, stripe, stub_tint,
    heatmap, humanize_labels
)

df = pd.read_csv("towny.csv")

# Compute overall growth rate from 1996 to 2021
df["overall_growth_pct"] = np.where(
    df["population_1996"] > 0,
    (df["population_2021"] - df["population_1996"]) / df["population_1996"],
    np.nan
)

# Filter out rows with no valid baseline
df_valid = df[df["overall_growth_pct"].notna()].copy().astype({"overall_growth_pct": "float64"})

# Select top 15 fastest-growing towns by overall growth rate
top_15 = df_valid.nlargest(15, "overall_growth_pct").copy()

# Reset index and build the display table
top_15 = top_15.reset_index(drop=True)
top_15["rank"] = range(1, 16)

# Select and reorder columns: name, rank, then density for each census year,
# then pct change between periods
display_df = top_15[[
    "name",
    "rank",
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
]].copy()

# Build the GT
gt = (
    GT(display_df, rowname_col="name")
    .tab_header(
        title="Ontario's Fastest-Growing Towns: Population Growth & Density Trends",
        subtitle=md("Top 15 towns ranked by overall population growth (1996–2021), "
                    "with density changes and inter-period growth rates"),
    )
    .tab_stubhead(label="Town")
    .tab_spanner(
        label="Population Density (per km²)",
        columns=["density_1996", "density_2001", "density_2006", "density_2011", "density_2016", "density_2021"],
    )
    .tab_spanner(
        label="Population Growth Rate (% change)",
        columns=[
            "pop_change_1996_2001_pct",
            "pop_change_2001_2006_pct",
            "pop_change_2006_2011_pct",
            "pop_change_2011_2016_pct",
            "pop_change_2016_2021_pct",
        ],
    )
    # Vertical divider at the boundary between density and growth rate sections
    .tab_style(
        style=style.borders(sides="right", color=PALETTE["neutral"]["vertical_divider"], weight="1px"),
        locations=loc.body(columns="density_2021"),
    )
    .tab_style(
        style=style.borders(sides="right", color=PALETTE["neutral"]["vertical_divider"], weight="1px"),
        locations=loc.column_labels(columns="density_2021"),
    )
    # Format columns
    .fmt_number(columns="rank", decimals=0)
    .fmt_number(columns=[
        "density_1996", "density_2001", "density_2006", "density_2011", "density_2016", "density_2021"
    ], decimals=1, use_seps=True)
    .fmt_percent(columns=[
        "pop_change_1996_2001_pct",
        "pop_change_2001_2006_pct",
        "pop_change_2006_2011_pct",
        "pop_change_2011_2016_pct",
        "pop_change_2016_2021_pct",
    ], decimals=1, scale_values=False)
)

gt = humanize_labels(
    gt,
    display_df,
    overrides={
        "rank": "Rank",
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
        "pop_change_2016_2021_pct": "2016–2021",
    },
)

# Big Color: 1 sequential heatmap for density (neutral/Blues)
# Compute domain from density columns across the 15 rows
density_cols = [
    "density_1996", "density_2001", "density_2006", "density_2011", "density_2016", "density_2021"
]
density_values = display_df[density_cols].values.flatten()
density_min = np.nanmin(density_values)
density_max = np.nanmax(density_values)

gt = heatmap(
    gt,
    density_cols,
    kind="sequential",
    hue="neutral",
    domain=[density_min, density_max]
)

# Band and stub tint (navy to match Blues)
gt = band(gt, hue="navy")
gt = stub_tint(gt, hue="navy")

# Striping gate: 15 rows > 10, and only 6 columns are colored out of 13
# (not essentially fully covered), so stripe.
gt = stripe(gt)

# Add source note
gt = gt.tab_source_note(
    source_note="Source: Statistics Canada Census data (1996–2021). "
                "Ranked by overall population growth rate from 1996 to 2021. "
                "All Ontario municipality types included."
)

# Final styling
gt = hairlines(gt)
gt = frame(gt)
finalize(gt, path="table.png")
