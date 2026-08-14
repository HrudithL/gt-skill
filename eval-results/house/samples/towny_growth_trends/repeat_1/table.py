import pandas as pd
import numpy as np
from great_tables import GT, loc, style
from house_table import PALETTE, frame, hairlines, finalize, band, stripe, stub_tint, heatmap

# Read the data
df = pd.read_csv("towny.csv")

# Calculate overall population growth rate (1996-2021)
df["total_growth_pct"] = np.where(
    df["population_1996"] > 0,
    (df["population_2021"] - df["population_1996"]) / df["population_1996"],
    np.nan
)

# Select top 15 fastest-growing towns
top_15 = df.nlargest(15, "total_growth_pct").copy()
top_15 = top_15.reset_index(drop=True)

# Calculate inter-census density change percentages
density_cols = ["density_1996", "density_2001", "density_2006", "density_2011", "density_2016", "density_2021"]
density_change_cols = []

for i in range(len(density_cols) - 1):
    col_name = f"density_change_{density_cols[i].split('_')[1]}_{density_cols[i+1].split('_')[1]}_pct"
    top_15[col_name] = np.where(
        top_15[density_cols[i]] > 0,
        (top_15[density_cols[i+1]] - top_15[density_cols[i]]) / top_15[density_cols[i]],
        np.nan
    )
    density_change_cols.append(col_name)

# Select relevant columns for display
display_cols = ["name"] + density_cols + density_change_cols
display_df = top_15[display_cols].copy()

# Create the GT object
gt = GT(display_df, rowname_col="name")

# Add title and subtitle
gt = gt.tab_header(
    title="Ontario Population Growth Trends",
    subtitle="Top 15 Fastest-Growing Towns (1996–2021)"
)

# Add source notes
gt = gt.tab_source_note(
    source_note="Ranked by overall population growth rate 1996–2021; density measured in persons per km². Inter-census changes shown as percentage shifts in population density."
)
gt = gt.tab_source_note(
    source_note="Source: Census data, 1996–2021."
)

# Label columns
gt = gt.cols_label(
    density_1996="1996",
    density_2001="2001",
    density_2006="2006",
    density_2011="2011",
    density_2016="2016",
    density_2021="2021",
    density_change_1996_2001_pct="1996–2001",
    density_change_2001_2006_pct="2001–2006",
    density_change_2006_2011_pct="2006–2011",
    density_change_2011_2016_pct="2011–2016",
    density_change_2016_2021_pct="2016–2021"
)

# Add spanners for density levels and changes
gt = gt.tab_spanner(label="Population Density (persons/km²)", columns=density_cols)
gt = gt.tab_spanner(label="Density Change (%)", columns=density_change_cols)

# Add vertical dividers at spanner boundaries
gt = gt.tab_style(
    style=style.borders(sides="right", color=PALETTE["neutral"]["vertical_divider"], weight="1px"),
    locations=loc.body(columns="density_2021")
)
gt = gt.tab_style(
    style=style.borders(sides="right", color=PALETTE["neutral"]["vertical_divider"], weight="1px"),
    locations=loc.column_labels(columns="density_2021")
)

# Format density columns as numbers with 1 decimal place
for col in density_cols:
    gt = gt.fmt_number(columns=col, decimals=1)

# Format density change columns as percentages
for col in density_change_cols:
    gt = gt.fmt_percent(columns=col, decimals=1, scale_values=False, force_sign=True)

# Apply heatmap to density change columns (diverging, green=good growth)
gt = heatmap(gt, density_change_cols, kind="diverging", hue="default")

# Apply branding (band and stub tint)
gt = band(gt, hue="navy")
gt = stub_tint(gt, hue="navy")

# Apply striping and frame
gt = stripe(gt)
gt = frame(gt)
gt = hairlines(gt)

# Finalize and save
finalize(gt, path="table.png")
