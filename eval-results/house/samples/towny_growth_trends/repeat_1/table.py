import pandas as pd
import numpy as np
from great_tables import GT, loc, md, style
from house_table import (
    PALETTE, frame, finalize, band, stripe, stub_tint, heatmap,
    humanize_labels
)

df = pd.read_csv("towny.csv")

# Ensure population columns are numeric
pop_cols = ["population_1996", "population_2001", "population_2006",
            "population_2011", "population_2016", "population_2021"]
density_cols = ["density_1996", "density_2001", "density_2006",
                "density_2011", "density_2016", "density_2021"]

for col in pop_cols + density_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Compute overall growth rate 1996-2021 (robust to zero/negative baselines)
df["growth_1996_2021"] = np.where(
    (df["population_1996"] > 0) & (df["population_1996"].notna()),
    (df["population_2021"] - df["population_1996"]) / df["population_1996"],
    np.nan
)

# Filter rows with valid growth rates
valid_growth = df.dropna(subset=["growth_1996_2021"])

# Get top 15 fastest-growing towns
top_15 = valid_growth.nlargest(15, "growth_1996_2021")[
    ["name", "population_1996", "population_2001", "population_2006",
     "population_2011", "population_2016", "population_2021",
     "density_1996", "density_2001", "density_2006",
     "density_2011", "density_2016", "density_2021",
     "pop_change_1996_2001_pct", "pop_change_2001_2006_pct",
     "pop_change_2006_2011_pct", "pop_change_2011_2016_pct",
     "pop_change_2016_2021_pct"]
].reset_index(drop=True)

# Format percentage change columns (already fractional in data)
# Compute density changes between periods using robust formula
for i, (start_col, end_col) in enumerate([
    ("density_1996", "density_2001"),
    ("density_2001", "density_2006"),
    ("density_2006", "density_2011"),
    ("density_2011", "density_2016"),
    ("density_2016", "density_2021"),
]):
    col_name = f"dens_change_{i+1}"
    top_15[col_name] = np.where(
        top_15[start_col] > 0,
        (top_15[end_col] - top_15[start_col]) / top_15[start_col],
        None
    )

gt = GT(top_15, rowname_col="name")

gt = gt.tab_header(
    title="Top 15 Fastest-Growing Ontario Towns",
    subtitle=md("Population and density trends across census periods (1996–2021), ranked by overall growth 1996–2021")
)

gt = gt.tab_stubhead(label="Town")

# Column spanners
gt = gt.tab_spanner(label="Population", columns=[
    "population_1996", "population_2001", "population_2006",
    "population_2011", "population_2016", "population_2021"
])

gt = gt.tab_spanner(label="Density (persons/km²)", columns=[
    "density_1996", "density_2001", "density_2006",
    "density_2011", "density_2016", "density_2021"
])

gt = gt.tab_spanner(label="Population Change %", columns=[
    "pop_change_1996_2001_pct", "pop_change_2001_2006_pct",
    "pop_change_2006_2011_pct", "pop_change_2011_2016_pct",
    "pop_change_2016_2021_pct"
])

gt = gt.tab_spanner(label="Density Change %", columns=[
    "dens_change_1", "dens_change_2", "dens_change_3", "dens_change_4", "dens_change_5"
])

# Formatting
gt = gt.fmt_integer(columns=[
    "population_1996", "population_2001", "population_2006",
    "population_2011", "population_2016", "population_2021"
])

gt = gt.fmt_number(columns=[
    "density_1996", "density_2001", "density_2006",
    "density_2011", "density_2016", "density_2021"
], decimals=2)

gt = gt.fmt_percent(columns=[
    "pop_change_1996_2001_pct", "pop_change_2001_2006_pct",
    "pop_change_2006_2011_pct", "pop_change_2011_2016_pct",
    "pop_change_2016_2021_pct"
], decimals=1, scale_values=False)

gt = gt.fmt_percent(columns=[
    "dens_change_1", "dens_change_2", "dens_change_3", "dens_change_4", "dens_change_5"
], decimals=1, scale_values=False)

gt = gt.sub_missing(missing_text="—")

# Labeling
overrides = {
    "population_1996": "1996", "population_2001": "2001",
    "population_2006": "2006", "population_2011": "2011",
    "population_2016": "2016", "population_2021": "2021",
    "density_1996": "1996", "density_2001": "2001",
    "density_2006": "2006", "density_2011": "2011",
    "density_2016": "2016", "density_2021": "2021",
    "pop_change_1996_2001_pct": "1996–2001",
    "pop_change_2001_2006_pct": "2001–2006",
    "pop_change_2006_2011_pct": "2006–2011",
    "pop_change_2011_2016_pct": "2011–2016",
    "pop_change_2016_2021_pct": "2016–2021",
    "dens_change_1": "1996–2001",
    "dens_change_2": "2001–2006",
    "dens_change_3": "2006–2011",
    "dens_change_4": "2011–2016",
    "dens_change_5": "2016–2021",
}

gt = humanize_labels(gt, top_15, overrides=overrides)

# Heatmaps (max 2): population change and density change as diverging measures
gt = heatmap(gt, [
    "pop_change_1996_2001_pct", "pop_change_2001_2006_pct",
    "pop_change_2006_2011_pct", "pop_change_2011_2016_pct",
    "pop_change_2016_2021_pct"
], kind="diverging", hue="default")

gt = heatmap(gt, [
    "dens_change_1", "dens_change_2", "dens_change_3", "dens_change_4", "dens_change_5"
], kind="diverging", hue="default")

# Styling
gt = band(gt, hue="forest")
gt = stub_tint(gt, hue="forest")

if len(top_15) >= 10:
    gt = stripe(gt)

gt = gt.tab_source_note(
    source_note="Source: towny.csv. Ranked by overall population growth 1996–2021; includes all Ontario municipality types."
)

gt = frame(gt)
finalize(gt, path="table.png")
