import pandas as pd
from great_tables import GT, md, loc, style
from house_table import PALETTE, frame, hairlines, finalize, band, stripe, stub_tint, heatmap, humanize_labels

# Read the data
df = pd.read_csv("towny.csv")

# Calculate overall population growth 1996-2021 to rank by
df["overall_growth"] = (df["population_2021"] - df["population_1996"]) / df["population_1996"]

# Get top 15 fastest-growing towns by overall growth
top_15 = df.nlargest(15, "overall_growth").reset_index(drop=True)

# Select columns for display
# Population columns for each census year
pop_cols = [
    "population_1996", "population_2001", "population_2006",
    "population_2011", "population_2016", "population_2021"
]

# Density columns for each census year
density_cols = [
    "density_1996", "density_2001", "density_2006",
    "density_2011", "density_2016", "density_2021"
]

# Percentage change columns
pct_change_cols = [
    "pop_change_1996_2001_pct", "pop_change_2001_2006_pct",
    "pop_change_2006_2011_pct", "pop_change_2011_2016_pct",
    "pop_change_2016_2021_pct"
]

# Build the display dataframe with town name and all columns
display_df = top_15[["name"] + pop_cols + density_cols + pct_change_cols].copy()

# Create the GT table
gt = GT(display_df, rowname_col="name")

# Add title and subtitle
gt = gt.tab_header(
    title="Ontario's Fastest-Growing Towns",
    subtitle=md("Top 15 towns by population growth (1996–2021), with population, density, and percent changes across census periods")
)

# Create spanners for readability
gt = gt.tab_spanner(label="Population (Count)", columns=pop_cols)
gt = gt.tab_spanner(label="Density (per km²)", columns=density_cols)
gt = gt.tab_spanner(label="Population % Change", columns=pct_change_cols)

# Format numbers
# Population columns: thousands separator, no decimals
for col in pop_cols:
    gt = gt.fmt_number(columns=col, decimals=0, use_seps=True)

# Density columns: 2 decimals
for col in density_cols:
    gt = gt.fmt_number(columns=col, decimals=2)

# Percent change columns: percentage format
for col in pct_change_cols:
    gt = gt.fmt_percent(columns=pct_change_cols, decimals=1)

# Humanize labels
gt = humanize_labels(
    gt,
    display_df,
    overrides={
        "population_1996": "1996",
        "population_2001": "2001",
        "population_2006": "2006",
        "population_2011": "2011",
        "population_2016": "2016",
        "population_2021": "2021",
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
    }
)

# Apply heatmaps to the percentage change columns (the hero measure)
# Use diverging red-yellow-green since these are signed values
gt = heatmap(gt, pct_change_cols, kind="diverging", hue="default")

# Apply band with forest hue (growth/environment context)
gt = band(gt, hue="forest")

# Small color polish: 15 rows and only ~5 columns are colored, so striping applies
gt = stripe(gt)
gt = stub_tint(gt, hue="forest")

# Add source note and finalize with frame and hairlines
gt = gt.tab_source_note(
    source_note="Source: Statistics Canada census data, 1996–2021. Ranked by overall population growth (1996–2021)."
)
gt = hairlines(gt)
gt = frame(gt)
finalize(gt, path="table.png")
