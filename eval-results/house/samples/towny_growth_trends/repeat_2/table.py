import pandas as pd
import numpy as np
from great_tables import GT, md, loc, style
from house_table import (
    PALETTE, frame, hairlines, finalize, band, stripe, stub_tint,
    heatmap, humanize_labels
)

# Read and prepare data
df = pd.read_csv("towny.csv")

# Convert population columns to numeric
pop_cols_src = [f"population_{year}" for year in [1996, 2001, 2006, 2011, 2016, 2021]]
for col in pop_cols_src:
    df[col] = pd.to_numeric(df[col], errors="coerce")

den_cols_src = [f"density_{year}" for year in [1996, 2001, 2006, 2011, 2016, 2021]]
for col in den_cols_src:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Calculate total population growth rate from 1996-2021
df["total_growth_pct"] = np.where(
    df["population_1996"] > 0,
    (df["population_2021"] - df["population_1996"]) / df["population_1996"],
    np.nan
)
df["total_growth_pct"] = pd.to_numeric(df["total_growth_pct"], errors="coerce")

# Filter to top 15 fastest-growing towns and sort
top15 = df.dropna(subset=["total_growth_pct"]).nlargest(15, "total_growth_pct").copy()
top15 = top15.sort_values("total_growth_pct", ascending=False).reset_index(drop=True)

# Build result dataframe with population, density, and percent changes
result = pd.DataFrame()
result["Town"] = top15["name"].values

# Population columns
result["Pop 1996"] = top15["population_1996"].astype(int).values
result["Pop 2001"] = top15["population_2001"].astype(int).values
result["Pop 2006"] = top15["population_2006"].astype(int).values
result["Pop 2011"] = top15["population_2011"].astype(int).values
result["Pop 2016"] = top15["population_2016"].astype(int).values
result["Pop 2021"] = top15["population_2021"].astype(int).values

# Density columns
result["Den 1996"] = top15["density_1996"].round(2).values
result["Den 2001"] = top15["density_2001"].round(2).values
result["Den 2006"] = top15["density_2006"].round(2).values
result["Den 2011"] = top15["density_2011"].round(2).values
result["Den 2016"] = top15["density_2016"].round(2).values
result["Den 2021"] = top15["density_2021"].round(2).values

# Population change percentages between periods
result["Chg 96-01%"] = np.where(
    top15["population_1996"] > 0,
    (top15["population_2001"] - top15["population_1996"]) / top15["population_1996"],
    None
)
result["Chg 01-06%"] = np.where(
    top15["population_2001"] > 0,
    (top15["population_2006"] - top15["population_2001"]) / top15["population_2001"],
    None
)
result["Chg 06-11%"] = np.where(
    top15["population_2006"] > 0,
    (top15["population_2011"] - top15["population_2006"]) / top15["population_2006"],
    None
)
result["Chg 11-16%"] = np.where(
    top15["population_2011"] > 0,
    (top15["population_2016"] - top15["population_2011"]) / top15["population_2011"],
    None
)
result["Chg 16-21%"] = np.where(
    top15["population_2016"] > 0,
    (top15["population_2021"] - top15["population_2016"]) / top15["population_2016"],
    None
)

# Build the GT table
gt = GT(result, rowname_col="Town")
gt = gt.tab_header(
    title="Top 15 Fastest-Growing Ontario Towns",
    subtitle=md("Population and population density across census years (1996–2021), with growth rates between periods"),
)
gt = gt.tab_stubhead(label="Town")

# Spanners for organization
gt = gt.tab_spanner(label="Population", columns=["Pop 1996", "Pop 2001", "Pop 2006", "Pop 2011", "Pop 2016", "Pop 2021"])
gt = gt.tab_spanner(label="Density (persons/km²)", columns=["Den 1996", "Den 2001", "Den 2006", "Den 2011", "Den 2016", "Den 2021"])
gt = gt.tab_spanner(label="Population Growth %", columns=["Chg 96-01%", "Chg 01-06%", "Chg 06-11%", "Chg 11-16%", "Chg 16-21%"])

# Format numbers
pop_cols = ["Pop 1996", "Pop 2001", "Pop 2006", "Pop 2011", "Pop 2016", "Pop 2021"]
den_cols = ["Den 1996", "Den 2001", "Den 2006", "Den 2011", "Den 2016", "Den 2021"]
chg_cols = ["Chg 96-01%", "Chg 01-06%", "Chg 06-11%", "Chg 11-16%", "Chg 16-21%"]

gt = gt.fmt_integer(columns=pop_cols)
gt = gt.fmt_number(columns=den_cols, decimals=1)
gt = gt.fmt_percent(columns=chg_cols, decimals=1, scale_values=False, force_sign=True)
gt = gt.sub_missing(columns=chg_cols, missing_text="—")

# Apply humanized labels
gt = humanize_labels(gt, result)

# Column widths and padding
gt = gt.cols_width(
    cases={
        "Town": "140px",
        "Pop 1996": "80px",
        "Pop 2001": "80px",
        "Pop 2006": "80px",
        "Pop 2011": "80px",
        "Pop 2016": "80px",
        "Pop 2021": "80px",
        "Den 1996": "95px",
        "Den 2001": "95px",
        "Den 2006": "95px",
        "Den 2011": "95px",
        "Den 2016": "95px",
        "Den 2021": "95px",
        "Chg 96-01%": "90px",
        "Chg 01-06%": "90px",
        "Chg 06-11%": "90px",
        "Chg 11-16%": "90px",
        "Chg 16-21%": "90px",
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

# Big Color: heatmap the population growth percentage changes (diverging, signed values)
gt = heatmap(gt, chg_cols, kind="diverging", hue="default")

# Branding surfaces: band (dark navy) and stub tint (navy washed)
gt = band(gt, hue="navy")
gt = stub_tint(gt, hue="navy")

# Small-color polish: striping (only where not 100% covered by heatmap)
gt = stripe(gt)

# Two source notes: analytical caption first, then provenance
gt = gt.tab_source_note(
    source_note="Ranked by total population growth rate from 1996–2021. Includes all Ontario municipality types (towns, townships, cities, villages, etc.). Population change percentages are calculated for each 5-year period based on population at the start of that period."
)
gt = gt.tab_source_note(source_note="Source: provided dataset with Census of Canada data, 1996–2021.")

# Frame and hairlines
gt = hairlines(gt)
gt = frame(gt)

# Finalize and render
finalize(gt, path="table.png")
