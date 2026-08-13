import pandas as pd
import numpy as np
from great_tables import GT, style, loc
from gt_consistency import frame, hairlines, finalize, heatmap, band, stripe, stub_tint

# Step 1: Read and prepare data
df = pd.read_csv("./towny.csv")

# Calculate overall percent change 1996-2021
df["overall_growth"] = ((df["population_2021"] - df["population_1996"]) / df["population_1996"]) * 100

# Get top 15 fastest-growing towns
top_15 = df.nlargest(15, "overall_growth")[["name",
                                             "density_1996", "density_2001", "density_2006", "density_2011", "density_2016", "density_2021",
                                             "pop_change_1996_2001_pct", "pop_change_2001_2006_pct", "pop_change_2006_2011_pct",
                                             "pop_change_2011_2016_pct", "pop_change_2016_2021_pct"]].reset_index(drop=True)

# Convert percent changes from decimal to percentage (multiply by 100 for display)
pct_cols = ["pop_change_1996_2001_pct", "pop_change_2001_2006_pct", "pop_change_2006_2011_pct",
            "pop_change_2011_2016_pct", "pop_change_2016_2021_pct"]
for col in pct_cols:
    top_15[col] = top_15[col] * 100

# Rename columns for display
top_15 = top_15.rename(columns={
    "density_1996": "1996",
    "density_2001": "2001",
    "density_2006": "2006",
    "density_2011": "2011",
    "density_2016": "2016",
    "density_2021": "2021",
    "pop_change_1996_2001_pct": "96-01",
    "pop_change_2001_2006_pct": "01-06",
    "pop_change_2006_2011_pct": "06-11",
    "pop_change_2011_2016_pct": "11-16",
    "pop_change_2016_2021_pct": "16-21"
})

# Step 2: Create GT object with stub
gt = GT(top_15, rowname_col="name")

# Step 2b: Organize columns with spanners
density_cols = ["1996", "2001", "2006", "2011", "2016", "2021"]
pct_cols = ["96-01", "01-06", "06-11", "11-16", "16-21"]

gt = (gt
    .tab_spanner(label="Density (persons/km²)", columns=density_cols)
    .tab_spanner(label="Population Change (%)", columns=pct_cols)
)

# Step 2c: Set column widths
gt = gt.cols_width(cases={
    "name": "180px",
    "1996": "90px",
    "2001": "90px",
    "2006": "90px",
    "2011": "90px",
    "2016": "90px",
    "2021": "90px",
    "96-01": "85px",
    "01-06": "85px",
    "06-11": "85px",
    "11-16": "85px",
    "16-21": "85px"
})

# Step 3: Big Color - density as sequential (magnitude), changes as diverging (signed)
# Density columns - ordered magnitude in increasing density
gt = heatmap(gt, density_cols, kind="sequential", hue="neutral")

# Percent change columns - signed diverging (positive = growth is good)
gt = heatmap(gt, pct_cols, kind="diverging", hue="default")

# Step 4: Heading band
gt = band(gt)

# Step 5: Small Color polish
# Hairlines
gt = hairlines(gt)

# Row striping
gt = stripe(gt)

# Stub tint
gt = stub_tint(gt)

# Format columns
gt = (gt
    .fmt_number(columns=density_cols, decimals=1, use_seps=True)
    .fmt_percent(columns=pct_cols, decimals=1, force_sign=True, scale_values=False)
    .sub_missing(columns=density_cols + pct_cols, missing_text="—")
)

# Column dividers at spanner seams
gt = (gt
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.body(columns="2021")
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.column_labels(columns="2021")
    )
)

# Step 6: Titles & annotations
gt = (gt
    .tab_header(
        title="Fastest-Growing Ontario Towns: Density Trends & Growth Rates",
        subtitle="Top 15 towns by population growth (1996–2021)"
    )
    .tab_source_note(source_note="Fastest-growing means highest percent change in population between 1996 and 2021. Density is measured as persons per square kilometer.")
    .tab_source_note(source_note="Source: Statistics Canada Census subdivisions, 1996–2021.")
)

# Step 5 (cont): Tab options for compact layout and frame
gt = (gt
    .tab_options(
        table_border_top_style="solid", table_border_top_color="#CCCCCC", table_border_top_width="1px",
        table_border_bottom_style="solid", table_border_bottom_color="#CCCCCC", table_border_bottom_width="1px",
        table_border_left_style="solid", table_border_left_color="#CCCCCC", table_border_left_width="1px",
        table_border_right_style="solid", table_border_right_color="#CCCCCC", table_border_right_width="1px",
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
)

# Step 7: Render
finalize(gt, "table.png")
