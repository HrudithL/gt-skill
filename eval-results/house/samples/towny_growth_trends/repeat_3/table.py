import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc
from house_table import PALETTE, frame, finalize, stripe, stub_tint, heatmap, humanize_labels

# Load and prepare data
df = pd.read_csv("./towny.csv")

# Calculate overall growth rate (1996–2021, percentage)
df["growth_rate_1996_2021"] = np.where(
    df["population_1996"] > 0,
    (df["population_2021"] - df["population_1996"]) / df["population_1996"],
    np.nan
)

# Select top 15 fastest-growing towns
top_15 = df.nlargest(15, "growth_rate_1996_2021").copy()

# Reset index for display
top_15_display = top_15[["name", "density_1996", "density_2001", "density_2006", "density_2011", "density_2016", "density_2021",
                          "pop_change_1996_2001_pct", "pop_change_2001_2006_pct", "pop_change_2006_2011_pct",
                          "pop_change_2011_2016_pct", "pop_change_2016_2021_pct"]].reset_index(drop=True)

# Create the GT object
gt = (
    GT(top_15_display, rowname_col="name")
    .tab_header(
        title="Population Growth Trends: Ontario's Fastest-Growing Municipalities",
        subtitle=md("Top 15 by relative growth (1996–2021). Density shown across all census years; percentage changes show population growth between periods.")
    )
    .tab_stubhead(label="Municipality")
    .tab_spanner(label="Population Density (persons/km²)", columns=["density_1996", "density_2001", "density_2006", "density_2011", "density_2016", "density_2021"])
    .tab_spanner(label="Population Change (%)", columns=["pop_change_1996_2001_pct", "pop_change_2001_2006_pct", "pop_change_2006_2011_pct", "pop_change_2011_2016_pct", "pop_change_2016_2021_pct"])
)

# Format density columns to 1 decimal
for col in ["density_1996", "density_2001", "density_2006", "density_2011", "density_2016", "density_2021"]:
    gt = gt.fmt_number(columns=col, decimals=1)

# Format percentage columns
for col in ["pop_change_1996_2001_pct", "pop_change_2001_2006_pct", "pop_change_2006_2011_pct", "pop_change_2011_2016_pct", "pop_change_2016_2021_pct"]:
    gt = gt.fmt_percent(columns=col, decimals=1, scale_values=False)

# Humanize labels
gt = humanize_labels(
    gt,
    top_15_display,
    overrides={
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

# Apply heatmap to density columns (sequential, Greens — growth/development)
gt = heatmap(gt, ["density_1996", "density_2001", "density_2006", "density_2011", "density_2016", "density_2021"],
             kind="sequential", hue="positive")

# Apply heatmap to percentage change columns (diverging, RdYlGn — positive growth is good)
gt = heatmap(gt, ["pop_change_1996_2001_pct", "pop_change_2001_2006_pct", "pop_change_2006_2011_pct",
                  "pop_change_2011_2016_pct", "pop_change_2016_2021_pct"],
             kind="diverging", hue="default")

# Apply structural formatting
gt = gt.tab_options(
    column_labels_background_color="#CFEAD9",  # accent_tint.forest
    column_labels_border_bottom_color="#CCCCCC",
    column_labels_border_bottom_width="2px",
    column_labels_border_bottom_style="solid",
)

# Row striping and tinting
gt = stripe(gt)
gt = stub_tint(gt, hue="forest")

# Row hairlines
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
)

# Source notes
gt = (
    gt.tab_source_note(
        source_note="Ranked by overall population growth rate (1996–2021, percentage change). "
                    "Fastest-growing municipalities by relative growth, all municipality types included."
    )
    .tab_source_note(source_note="Source: Statistics Canada Census data, 1996–2021.")
)

# Frame and finalize
gt = frame(gt)
finalize(gt, path="table.png", zoom=2.0, expand=15)
