import pandas as pd
import numpy as np
from great_tables import GT, md, loc, style
from house_table import PALETTE, frame, finalize, band, stripe, stub_tint, heatmap, humanize_labels

df = pd.read_csv("towny.csv")

# Ensure consistent dtypes
for col in ["population_1996", "population_2001", "population_2006", "population_2011", "population_2016", "population_2021"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Filter to Ontario towns (all municipality types per rule 2 in RULES.md)
# Add overall population growth metric (1996-2021)
df["pop_growth_overall"] = np.where(
    df["population_1996"] > 0,
    (df["population_2021"] - df["population_1996"]) / df["population_1996"],
    np.nan
)

# Keep only rows where growth can be calculated
df_valid = df[df["pop_growth_overall"].notna()].copy()

# Rank by overall population growth and take top 15
df_top15 = df_valid.nlargest(15, "pop_growth_overall").copy()

# Calculate per-period percentage changes in density
# Using the guard: np.where(start > 0, (end - start) / start, None)
df_top15["density_change_1996_2001_pct"] = np.where(
    df_top15["density_1996"] > 0,
    (df_top15["density_2001"] - df_top15["density_1996"]) / df_top15["density_1996"],
    None
)
df_top15["density_change_2001_2006_pct"] = np.where(
    df_top15["density_2001"] > 0,
    (df_top15["density_2006"] - df_top15["density_2001"]) / df_top15["density_2001"],
    None
)
df_top15["density_change_2006_2011_pct"] = np.where(
    df_top15["density_2006"] > 0,
    (df_top15["density_2011"] - df_top15["density_2006"]) / df_top15["density_2006"],
    None
)
df_top15["density_change_2011_2016_pct"] = np.where(
    df_top15["density_2011"] > 0,
    (df_top15["density_2016"] - df_top15["density_2011"]) / df_top15["density_2011"],
    None
)
df_top15["density_change_2016_2021_pct"] = np.where(
    df_top15["density_2016"] > 0,
    (df_top15["density_2021"] - df_top15["density_2016"]) / df_top15["density_2016"],
    None
)

# Select and order columns for display
display_cols = [
    "name",
    "population_1996",
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

df_display = df_top15[display_cols].copy()
df_display = df_display.reset_index(drop=True)

gt = (
    GT(df_display, rowname_col="name")
    .tab_header(
        title="Ontario Municipal Population Growth",
        subtitle=md("Top 15 fastest-growing municipalities (1996–2021): density across all census years with period-to-period changes"),
    )
    .tab_spanner(label="1996", columns=["population_1996", "density_1996"])
    .tab_spanner(label="2001", columns=["density_2001", "density_change_1996_2001_pct"])
    .tab_spanner(label="2006", columns=["density_2006", "density_change_2001_2006_pct"])
    .tab_spanner(label="2011", columns=["density_2011", "density_change_2006_2011_pct"])
    .tab_spanner(label="2016", columns=["density_2016", "density_change_2011_2016_pct"])
    .tab_spanner(label="2021", columns=["density_2021", "density_change_2016_2021_pct"])
    .fmt_number(columns=["population_1996"], decimals=0, use_seps=True)
    .fmt_number(columns=["density_1996", "density_2001", "density_2006", "density_2011", "density_2016", "density_2021"], decimals=2)
    .fmt_percent(
        columns=[
            "density_change_1996_2001_pct",
            "density_change_2001_2006_pct",
            "density_change_2006_2011_pct",
            "density_change_2011_2016_pct",
            "density_change_2016_2021_pct",
        ],
        decimals=1
    )
    .sub_missing(missing_text="—")
)

gt = humanize_labels(
    gt,
    df_display,
    overrides={
        "population_1996": "Population",
        "density_1996": "Density",
        "density_2001": "Density",
        "density_change_1996_2001_pct": "Δ %",
        "density_2006": "Density",
        "density_change_2001_2006_pct": "Δ %",
        "density_2011": "Density",
        "density_change_2006_2011_pct": "Δ %",
        "density_2016": "Density",
        "density_change_2011_2016_pct": "Δ %",
        "density_2021": "Density",
        "density_change_2016_2021_pct": "Δ %",
    }
)

# Heatmap 1: density values (sequential, Blues/neutral)
gt = heatmap(
    gt,
    ["density_1996", "density_2001", "density_2006", "density_2011", "density_2016", "density_2021"],
    kind="sequential",
    hue="neutral"
)

# Heatmap 2: density changes (diverging, default RdYlGn)
gt = heatmap(
    gt,
    [
        "density_change_1996_2001_pct",
        "density_change_2001_2006_pct",
        "density_change_2006_2011_pct",
        "density_change_2011_2016_pct",
        "density_change_2016_2021_pct",
    ],
    kind="diverging",
    hue="default"
)

gt = band(gt, hue="navy")
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

gt.tab_source_note(source_note="Source: Statistics Canada, Census of Population (1996–2021). Ranked by overall population growth rate (1996–2021). All Ontario municipality types included.")

gt = frame(gt)
finalize(gt, path="table.png")
