import pandas as pd
import numpy as np
from great_tables import GT, md
from gt_consistency import frame, band, heatmap, stripe, stub_tint, finalize, PALETTE

# Read and clean data
df = pd.read_csv("towny.csv")

# Calculate overall growth rate (1996-2021)
df["overall_growth"] = (df["population_2021"] - df["population_1996"]) / df["population_1996"]

# Find top 15 fastest-growing towns (by overall growth rate)
# Filter out towns with missing 1996 or 2021 data
valid_df = df.dropna(subset=["population_1996", "population_2021"])
top_15 = valid_df.nlargest(15, "overall_growth")

# Create output dataframe with relevant columns
output_df = top_15[["name", "population_1996", "density_1996", "population_2001",
                     "density_2001", "population_2006", "density_2006", "population_2011",
                     "density_2011", "population_2016", "density_2016", "population_2021",
                     "density_2021", "pop_change_1996_2001_pct", "pop_change_2001_2006_pct",
                     "pop_change_2006_2011_pct", "pop_change_2011_2016_pct",
                     "pop_change_2016_2021_pct"]].copy().reset_index(drop=True)

# Rename columns for clarity
output_df.columns = [
    "Town",
    "Pop 1996", "Density 1996",
    "Pop 2001", "Density 2001",
    "Pop 2006", "Density 2006",
    "Pop 2011", "Density 2011",
    "Pop 2016", "Density 2016",
    "Pop 2021", "Density 2021",
    "Pct 1996-2001", "Pct 2001-2006", "Pct 2006-2011", "Pct 2011-2016", "Pct 2016-2021"
]

# Convert percentage columns from decimal to proper percentage scale (0-100)
pct_cols = ["Pct 1996-2001", "Pct 2001-2006", "Pct 2006-2011", "Pct 2011-2016", "Pct 2016-2021"]
for col in pct_cols:
    output_df[col] = output_df[col] * 100

# Build the table
gt = (
    GT(output_df, rowname_col="Town")
    .cols_label(
        **{
            "Pop 1996": md("Pop<br>1996"),
            "Density 1996": md("Density<br>1996"),
            "Pop 2001": md("Pop<br>2001"),
            "Density 2001": md("Density<br>2001"),
            "Pop 2006": md("Pop<br>2006"),
            "Density 2006": md("Density<br>2006"),
            "Pop 2011": md("Pop<br>2011"),
            "Density 2011": md("Density<br>2011"),
            "Pop 2016": md("Pop<br>2016"),
            "Density 2016": md("Density<br>2016"),
            "Pop 2021": md("Pop<br>2021"),
            "Density 2021": md("Density<br>2021"),
            "Pct 1996-2001": md("% Chg<br>96–01"),
            "Pct 2001-2006": md("% Chg<br>01–06"),
            "Pct 2006-2011": md("% Chg<br>06–11"),
            "Pct 2011-2016": md("% Chg<br>11–16"),
            "Pct 2016-2021": md("% Chg<br>16–21"),
        }
    )
    .fmt_number(
        columns=["Pop 1996", "Pop 2001", "Pop 2006", "Pop 2011", "Pop 2016", "Pop 2021"],
        decimals=0
    )
    .fmt_number(
        columns=["Density 1996", "Density 2001", "Density 2006", "Density 2011", "Density 2016", "Density 2021"],
        decimals=1
    )
    .fmt_number(
        columns=pct_cols,
        decimals=1
    )
    .sub_missing(missing_text="—")
)

# Apply heatmap coloring to density columns (showing magnitude)
density_cols = ["Density 1996", "Density 2001", "Density 2006", "Density 2011", "Density 2016", "Density 2021"]
gt = heatmap(gt, density_cols, kind="sequential", hue="neutral")

# Apply band styling
gt = band(gt, shade="light", hue="navy")

# Apply striping and other polish
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

# Apply title, subtitle, and caption
gt = (
    gt.tab_header(
        title="Ontario Towns: Population Growth & Density Trends (1996–2021)",
        subtitle="Top 15 Fastest-Growing Towns with Census Data"
    )
    .tab_source_note(
        source_note="Data source: Statistics Canada Census data, 1996–2021"
    )
)

# Apply frame and finalize
gt = frame(gt)
gt = finalize(gt)

gt.gtsave("table.png")
