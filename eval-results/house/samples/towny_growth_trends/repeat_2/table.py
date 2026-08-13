import pandas as pd
import numpy as np
from great_tables import GT, loc, style, md
from house_table import (
    PALETTE, frame, hairlines, finalize, band, stripe, stub_tint,
    heatmap, humanize_labels
)

# Read the data
df = pd.read_csv("towny.csv")

# Calculate overall growth rate from 1996 to 2021
df["overall_growth_rate"] = np.where(
    df["population_1996"] > 0,
    (df["population_2021"] - df["population_1996"]) / df["population_1996"],
    np.nan
)

# Get top 15 fastest-growing towns
top_15 = df.nlargest(15, "overall_growth_rate")

# Create a display dataframe with town name and the relevant columns
display_cols = [
    "name",
    "population_1996", "density_1996",
    "population_2001", "density_2001",
    "population_2006", "density_2006",
    "population_2011", "density_2011",
    "population_2016", "density_2016",
    "population_2021", "density_2021",
    "pop_change_1996_2001_pct",
    "pop_change_2001_2006_pct",
    "pop_change_2006_2011_pct",
    "pop_change_2011_2016_pct",
    "pop_change_2016_2021_pct",
]

df_display = top_15[display_cols].reset_index(drop=True)
df_display["rank"] = range(1, len(df_display) + 1)

# Reorder columns to put rank first
df_display = df_display[["rank", "name"] + [c for c in df_display.columns if c not in ["rank", "name"]]]

# Create the GT object with the town name as the stub
gt = (
    GT(df_display, rowname_col="name")
    .tab_header(
        title="Ontario Population Growth Trends",
        subtitle="Top 15 fastest-growing municipalities (1996–2021)"
    )
    .cols_label(
        rank="Rank",
        population_1996="Pop 1996",
        density_1996="Dens 1996",
        population_2001="Pop 2001",
        density_2001="Dens 2001",
        population_2006="Pop 2006",
        density_2006="Dens 2006",
        population_2011="Pop 2011",
        density_2011="Dens 2011",
        population_2016="Pop 2016",
        density_2016="Dens 2016",
        population_2021="Pop 2021",
        density_2021="Dens 2021",
        pop_change_1996_2001_pct="1996–2001 %",
        pop_change_2001_2006_pct="2001–2006 %",
        pop_change_2006_2011_pct="2006–2011 %",
        pop_change_2011_2016_pct="2011–2016 %",
        pop_change_2016_2021_pct="2016–2021 %",
    )
    .fmt_integer(columns=["population_1996", "population_2001", "population_2006",
                          "population_2011", "population_2016", "population_2021"])
    .fmt_number(
        columns=["density_1996", "density_2001", "density_2006",
                 "density_2011", "density_2016", "density_2021"],
        decimals=2
    )
    .fmt_percent(
        columns=["pop_change_1996_2001_pct", "pop_change_2001_2006_pct",
                 "pop_change_2006_2011_pct", "pop_change_2011_2016_pct",
                 "pop_change_2016_2021_pct"],
        decimals=1,
        scale_values=False,
        force_sign=True
    )
    .fmt_integer(columns="rank")
)

# Apply branding and formatting
gt = (
    gt
    .tab_stubhead(label="Municipality")
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
)

# Apply heatmap for percentage changes (diverging color, growth = good)
gt = heatmap(
    gt,
    columns=["pop_change_1996_2001_pct", "pop_change_2001_2006_pct",
             "pop_change_2006_2011_pct", "pop_change_2011_2016_pct",
             "pop_change_2016_2021_pct"],
    kind="diverging",
    hue="default"
)

# Apply heatmap for density (sequential, neutral blue for magnitude)
gt = heatmap(
    gt,
    columns=["density_1996", "density_2001", "density_2006",
             "density_2011", "density_2016", "density_2021"],
    kind="sequential",
    hue="neutral"
)

# Add spanning labels for census years (population and density pairs)
gt = (
    gt
    .tab_spanner(label="1996", columns=["population_1996", "density_1996"])
    .tab_spanner(label="2001", columns=["population_2001", "density_2001"])
    .tab_spanner(label="2006", columns=["population_2006", "density_2006"])
    .tab_spanner(label="2011", columns=["population_2011", "density_2011"])
    .tab_spanner(label="2016", columns=["population_2016", "density_2016"])
    .tab_spanner(label="2021", columns=["population_2021", "density_2021"])
    .tab_spanner(label="Period-over-Period Growth %", columns=[
        "pop_change_1996_2001_pct", "pop_change_2001_2006_pct",
        "pop_change_2006_2011_pct", "pop_change_2011_2016_pct",
        "pop_change_2016_2021_pct"
    ])
)

# Add source notes
gt = (
    gt
    .tab_source_note(
        source_note=md(
            "**Ranking:** by overall population growth rate (1996–2021, percentage change). "
            "**Density columns:** persons per km². **Growth % columns:** year-over-year population change, scaled already (not fractional)."
        )
    )
    .tab_source_note(
        source_note="Source: provided dataset."
    )
)

# Apply house formatting
gt = band(gt, hue="navy")
gt = stub_tint(gt, hue="navy")
gt = stripe(gt)
gt = frame(gt)
gt = hairlines(gt)

# Finalize and save
finalize(gt, path="table.png")

print("Table created: table.png")
