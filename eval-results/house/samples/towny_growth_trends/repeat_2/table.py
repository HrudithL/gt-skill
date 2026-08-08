import pandas as pd
import numpy as np
from great_tables import GT, md, loc, style
from house_table import (
    PALETTE, frame, finalize, heatmap, stub_tint, stripe, group_emphasis
)

# Read the data
df = pd.read_csv("towny.csv")

# Convert population and density columns to numeric
pop_cols = [col for col in df.columns if col.startswith("population_")]
for col in pop_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Calculate overall population growth rate from 1996 to 2021
df["growth_1996_2021"] = np.where(
    df["population_1996"] > 0,
    (df["population_2021"] - df["population_1996"]) / df["population_1996"],
    np.nan
)

# Filter to valid entries and sort by growth rate
valid_df = df[df["growth_1996_2021"].notna()].copy()
top_15 = valid_df.nlargest(15, "growth_1996_2021").reset_index(drop=True)

# Select and organize columns
display_cols = [
    "name",
    "population_1996", "density_1996",
    "population_2001", "density_2001",
    "population_2006", "density_2006",
    "population_2011", "density_2011",
    "population_2016", "density_2016",
    "population_2021", "density_2021",
    "pop_change_1996_2001_pct", "pop_change_2001_2006_pct",
    "pop_change_2006_2011_pct", "pop_change_2011_2016_pct",
    "pop_change_2016_2021_pct"
]

table_df = top_15[display_cols].copy()

# Rename for display
table_df = table_df.rename(columns={
    "name": "Town",
    "population_1996": "Pop 1996", "density_1996": "Dens 1996",
    "population_2001": "Pop 2001", "density_2001": "Dens 2001",
    "population_2006": "Pop 2006", "density_2006": "Dens 2006",
    "population_2011": "Pop 2011", "density_2011": "Dens 2011",
    "population_2016": "Pop 2016", "density_2016": "Dens 2016",
    "population_2021": "Pop 2021", "density_2021": "Dens 2021",
    "pop_change_1996_2001_pct": "1996→01 %",
    "pop_change_2001_2006_pct": "2001→06 %",
    "pop_change_2006_2011_pct": "2006→11 %",
    "pop_change_2011_2016_pct": "2011→16 %",
    "pop_change_2016_2021_pct": "2016→21 %",
})

# Build the table
gt = GT(table_df, rowname_col="Town")

gt = gt.tab_header(
    title="Top 15 Fastest-Growing Ontario Towns",
    subtitle=md("Population and density across census years 1996–2021, ranked by overall growth rate 1996–2021"),
)

gt = gt.tab_spanner(label="1996", columns=["Pop 1996", "Dens 1996"])
gt = gt.tab_spanner(label="2001", columns=["Pop 2001", "Dens 2001"])
gt = gt.tab_spanner(label="2006", columns=["Pop 2006", "Dens 2006"])
gt = gt.tab_spanner(label="2011", columns=["Pop 2011", "Dens 2011"])
gt = gt.tab_spanner(label="2016", columns=["Pop 2016", "Dens 2016"])
gt = gt.tab_spanner(label="2021", columns=["Pop 2021", "Dens 2021"])
gt = gt.tab_spanner(label="Growth %", columns=[
    "1996→01 %", "2001→06 %", "2006→11 %", "2011→16 %", "2016→21 %"
])

# Format columns
gt = gt.fmt_integer(columns=[
    "Pop 1996", "Pop 2001", "Pop 2006", "Pop 2011", "Pop 2016", "Pop 2021"
])
gt = gt.fmt_number(columns=[
    "Dens 1996", "Dens 2001", "Dens 2006", "Dens 2011", "Dens 2016", "Dens 2021"
], decimals=1)
gt = gt.fmt_percent(columns=[
    "1996→01 %", "2001→06 %", "2006→11 %", "2011→16 %", "2016→21 %"
], decimals=1)

gt = gt.sub_missing(missing_text="—")

# Color the density measure (sequential - positive is growth/more dense)
gt = heatmap(gt, [
    "Dens 1996", "Dens 2001", "Dens 2006", "Dens 2011", "Dens 2016", "Dens 2021"
], kind="sequential", hue="neutral")

# Color the growth percentages (diverging - signed values)
gt = heatmap(gt, [
    "1996→01 %", "2001→06 %", "2006→11 %", "2011→16 %", "2016→21 %"
], kind="diverging", hue="default")

# Apply styling
gt = gt.tab_options(
    column_labels_background_color="#C9E0F0",
    column_labels_border_bottom_color=PALETTE["neutral"]["column_label_rule"],
    column_labels_border_bottom_width="2px",
    column_labels_border_bottom_style="solid",
)

gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

# Row hairlines
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color=PALETTE["neutral"]["hairline"],
    table_body_hlines_width="1px",
)

gt = frame(gt)

gt = (
    gt.tab_source_note(
        source_note="Ranked by total population growth rate (1996–2021). All municipality types included."
    )
    .tab_source_note(source_note="Source: towny.csv")
)

finalize(gt, path="table.png", zoom=2.0, expand=15)
