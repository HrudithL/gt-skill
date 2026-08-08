import pandas as pd
import numpy as np
from great_tables import GT, loc, style
from gt_consistency import PALETTE, frame, finalize, band, stripe, stub_tint, heatmap

# Step 1: Load and clean the data
df = pd.read_csv("towny.csv")

# Calculate overall growth rate from 1996 to 2021
df["overall_growth_rate"] = np.where(
    df["population_1996"] > 0,
    (df["population_2021"] - df["population_1996"]) / df["population_1996"],
    np.nan
)

# Select top 15 fastest-growing towns
top_15 = df.nlargest(15, "overall_growth_rate").copy()

# Select and organize columns for the display
display_df = top_15[
    ["name", "density_1996", "density_2001", "density_2006",
     "density_2011", "density_2016", "density_2021",
     "pop_change_1996_2001_pct", "pop_change_2001_2006_pct",
     "pop_change_2006_2011_pct", "pop_change_2011_2016_pct",
     "pop_change_2016_2021_pct"]
].reset_index(drop=True)

# Rename columns for clarity
display_df = display_df.rename(columns={
    "name": "Town",
    "density_1996": "Density 1996",
    "density_2001": "Density 2001",
    "density_2006": "Density 2006",
    "density_2011": "Density 2011",
    "density_2016": "Density 2016",
    "density_2021": "Density 2021",
    "pop_change_1996_2001_pct": "Change 1996-2001",
    "pop_change_2001_2006_pct": "Change 2001-2006",
    "pop_change_2006_2011_pct": "Change 2006-2011",
    "pop_change_2011_2016_pct": "Change 2011-2016",
    "pop_change_2016_2021_pct": "Change 2016-2021",
})

# Ensure density columns are numeric (in case of any issues)
density_cols = ["Density 1996", "Density 2001", "Density 2006",
                "Density 2011", "Density 2016", "Density 2021"]
change_cols = ["Change 1996-2001", "Change 2001-2006",
               "Change 2006-2011", "Change 2011-2016", "Change 2016-2021"]

for col in density_cols + change_cols:
    display_df[col] = pd.to_numeric(display_df[col], errors="coerce")

# Step 2: Create the GT table with stub
gt = GT(display_df, rowname_col="Town")

# Step 3: Apply big color — density gradient (Blues for neutral magnitude)
density_cols_list = ["Density 1996", "Density 2001", "Density 2006",
                     "Density 2011", "Density 2016", "Density 2021"]
lo_density = float(np.nanmin(display_df[density_cols_list].to_numpy()))
hi_density = float(np.nanmax(display_df[density_cols_list].to_numpy()))

gt = gt.data_color(
    columns=density_cols_list,
    palette="Blues",
    domain=[lo_density, hi_density],
    truncate=False,
    na_color="#808080",
)

# Color the percentage change columns with diverging palette (Green for positive/growth)
change_cols_list = ["Change 1996-2001", "Change 2001-2006",
                    "Change 2006-2011", "Change 2011-2016", "Change 2016-2021"]
lo_change = float(np.nanmin(display_df[change_cols_list].to_numpy()))
hi_change = float(np.nanmax(display_df[change_cols_list].to_numpy()))
# Ensure symmetric domain for diverging palette
max_abs = max(abs(lo_change), abs(hi_change))
domain_change = [-max_abs, max_abs]

gt = gt.data_color(
    columns=change_cols_list,
    palette="RdYlGn",
    domain=domain_change,
    truncate=False,
    na_color="#808080",
)

# Step 4: Format columns
gt = (
    gt
    .fmt_number(columns=density_cols_list, decimals=1)
    .fmt_percent(columns=change_cols_list, decimals=1, scale_values=False)
)

# Step 4: Column label band (Light band with Big Color present)
gt = gt.tab_options(
    column_labels_background_color="#EAF0F6",  # washed-blue tint (Blues is dominant hue)
    column_labels_font_weight="bold",
    column_labels_border_bottom_color="#CCCCCC",
    column_labels_border_bottom_width="2px",
)

# Step 5: Small color polish
# Cell borders
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
)

# Row striping (≥10 rows)
gt = gt.opt_row_striping()

# Stub tint (use washed-blue tint to harmonize with Blues gradient)
gt = gt.tab_style(
    style=style.fill(color="#EAF0F6"),
    locations=loc.stub(),
)

# Column group dividers for logical grouping
gt = (
    gt
    .tab_spanner(label="Population Density (per km²)", columns=density_cols_list)
    .tab_spanner(label="Period Change (%)", columns=change_cols_list)
)

# Add divider after the last density column
gt = gt.tab_style(
    style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
    locations=loc.body(columns="Density 2021"),
)
gt = gt.tab_style(
    style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
    locations=loc.column_labels(columns="Density 2021"),
)

# Step 6: Titles and annotations
gt = (
    gt
    .tab_header(
        title="Top 15 Fastest-Growing Ontario Towns",
        subtitle="Population density trends (1996-2021) and period-over-period growth rates",
    )
    .tab_source_note(
        source_note="Growth ranking is based on overall population growth from 1996 to 2021."
    )
    .tab_source_note(
        source_note="Source: towny.csv — Ontario municipal population and density data."
    )
)

# Step 7: Apply frame and render
gt = frame(gt)
finalize(gt)
