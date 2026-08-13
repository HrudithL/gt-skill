import pandas as pd
import numpy as np
from great_tables import GT, md, loc, style
from gt_consistency import PALETTE, frame, finalize, band, stripe, stub_tint, hairlines

# Step 1: Load and clean data
df = pd.read_csv("towny.csv")

# Calculate overall population growth rate (1996 to 2021) to identify fastest-growing towns
df["total_growth_pct"] = (df["population_2021"] - df["population_1996"]) / df["population_1996"]

# Get top 15 fastest-growing towns
top15 = df.nlargest(15, "total_growth_pct")[["name", "density_1996", "density_2001", "density_2006", "density_2011", "density_2016", "density_2021", "pop_change_1996_2001_pct", "pop_change_2001_2006_pct", "pop_change_2006_2011_pct", "pop_change_2011_2016_pct", "pop_change_2016_2021_pct"]].reset_index(drop=True)

# Rename columns for clearer labels
top15 = top15.rename(columns={
    "name": "Town",
    "density_1996": "Density 1996",
    "density_2001": "Density 2001",
    "density_2006": "Density 2006",
    "density_2011": "Density 2011",
    "density_2016": "Density 2016",
    "density_2021": "Density 2021",
    "pop_change_1996_2001_pct": "1996-2001 (%)",
    "pop_change_2001_2006_pct": "2001-2006 (%)",
    "pop_change_2006_2011_pct": "2006-2011 (%)",
    "pop_change_2011_2016_pct": "2011-2016 (%)",
    "pop_change_2016_2021_pct": "2016-2021 (%)",
})

# Step 2: Organize columns - density columns first, then percent changes
density_cols = ["Density 1996", "Density 2001", "Density 2006", "Density 2011", "Density 2016", "Density 2021"]
pct_cols = ["1996-2001 (%)", "2001-2006 (%)", "2006-2011 (%)", "2011-2016 (%)", "2016-2021 (%)"]

# Step 3: Big Color - compute domains for heatmaps
# Domain for density (ordered magnitude, sequential palette)
density_vals = top15[density_cols].to_numpy()
density_min = float(np.nanmin(density_vals))
density_max = float(np.nanmax(density_vals))

# Domain for percentage changes (diverging - can be negative)
pct_vals = top15[pct_cols].to_numpy()
pct_min = float(np.nanmin(pct_vals))
pct_max = float(np.nanmax(pct_vals))
# Symmetric domain for diverging
pct_domain_bound = max(abs(pct_min), abs(pct_max))
pct_domain = [-pct_domain_bound, pct_domain_bound]

# Step 4: Build the table with GT
gt = GT(top15, rowname_col="Town")

# Format density columns to 1 decimal
gt = gt.fmt_number(columns=density_cols, decimals=1)

# Format percentage columns with force_sign=True since they cross zero
gt = gt.fmt_percent(columns=pct_cols, decimals=1, force_sign=True)

# Apply density heatmap (Blues for neutral magnitude)
gt = gt.data_color(
    columns=density_cols,
    palette="Blues",
    domain=[density_min, density_max],
    na_color="#808080",
)

# Apply percentage change heatmap (diverging - RdYlGn for diverging treatment)
gt = gt.data_color(
    columns=pct_cols,
    palette="RdYlGn",
    domain=pct_domain,
    na_color="#808080",
)

# Column labels
gt = gt.cols_label(
    **{col: col for col in density_cols},
    **{col: col for col in pct_cols}
)

# Compact layout: set column widths and padding
gt = gt.cols_width(cases={
    "Town": "180px",
    **{col: "100px" for col in density_cols},
    **{col: "90px" for col in pct_cols},
})

# Standard padding (from small_color.md)
gt = gt.tab_options(
    heading_padding="12px",
    column_labels_padding="12px",
    column_labels_padding_horizontal="6px",
    data_row_padding="8px",
    data_row_padding_horizontal="6px",
    source_notes_padding="12px",
)

# Step 4: Apply heading band
gt = band(gt)

# Step 5: Apply Small Color polish
gt = hairlines(gt)
gt = stripe(gt)
gt = stub_tint(gt)

# Step 6: Titles & annotations
gt = gt.tab_header(
    title="Ontario's 15 Fastest-Growing Towns",
    subtitle="Population Density and Growth Rates Across Census Years (1996–2021)",
)

gt = gt.tab_source_note(
    md("**Growth measured by:** Fastest-growing towns ranked by total population change from 1996 to 2021. Density is persons per square kilometer."),
)

gt = gt.tab_source_note(
    md("**Source:** Canadian census data, 1996–2021 (Statistics Canada)."),
)

# Step 7: Frame and render
gt = frame(gt)
gt = hairlines(gt)

finalize(gt)
