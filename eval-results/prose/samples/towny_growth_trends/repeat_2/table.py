import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc

# Step 1: Read and clean the data
df_raw = pd.read_csv("towny.csv")

# Ensure numeric columns are numeric
pop_cols = ["population_1996", "population_2001", "population_2006", "population_2011", "population_2016", "population_2021"]
density_cols = ["density_1996", "density_2001", "density_2006", "density_2011", "density_2016", "density_2021"]
pct_cols = ["pop_change_1996_2001_pct", "pop_change_2001_2006_pct", "pop_change_2006_2011_pct", "pop_change_2011_2016_pct", "pop_change_2016_2021_pct"]

for col in pop_cols + density_cols + pct_cols:
    df_raw[col] = pd.to_numeric(df_raw[col], errors="coerce")

# Calculate overall growth rate from 1996 to 2021 to identify fastest-growing towns
df_raw["overall_growth_pct"] = ((df_raw["population_2021"] - df_raw["population_1996"]) / df_raw["population_1996"]).fillna(0)

# Get top 15 fastest-growing towns
top15 = df_raw.nlargest(15, "overall_growth_pct")[["name", "population_1996", "population_2001", "population_2006", "population_2011", "population_2016", "population_2021",
                                                      "density_1996", "density_2001", "density_2006", "density_2011", "density_2016", "density_2021",
                                                      "pop_change_1996_2001_pct", "pop_change_2001_2006_pct", "pop_change_2006_2011_pct", "pop_change_2011_2016_pct", "pop_change_2016_2021_pct"]].reset_index(drop=True)

# Create display table with population and density grouped by census year
df_display = pd.DataFrame({
    "Town": top15["name"],
    "Pop 1996": top15["population_1996"].astype(int),
    "Density 1996": top15["density_1996"],
    "Pop 2001": top15["population_2001"].astype(int),
    "Density 2001": top15["density_2001"],
    "Pop 2006": top15["population_2006"].astype(int),
    "Density 2006": top15["density_2006"],
    "Pop 2011": top15["population_2011"].astype(int),
    "Density 2011": top15["density_2011"],
    "Pop 2016": top15["population_2016"].astype(int),
    "Density 2016": top15["density_2016"],
    "Pop 2021": top15["population_2021"].astype(int),
    "Density 2021": top15["density_2021"],
    "Growth 96-01 %": top15["pop_change_1996_2001_pct"],
    "Growth 01-06 %": top15["pop_change_2001_2006_pct"],
    "Growth 06-11 %": top15["pop_change_2006_2011_pct"],
    "Growth 11-16 %": top15["pop_change_2011_2016_pct"],
    "Growth 16-21 %": top15["pop_change_2016_2021_pct"],
})

# Define column groups for spanners
pop_growth_cols = ["Growth 96-01 %", "Growth 01-06 %", "Growth 06-11 %", "Growth 11-16 %", "Growth 16-21 %"]

# Calculate min/max for colored measures (population gradient)
pop_cols_display = ["Pop 1996", "Pop 2001", "Pop 2006", "Pop 2011", "Pop 2016", "Pop 2021"]
pop_min = float(np.nanmin(df_display[pop_cols_display].to_numpy()))
pop_max = float(np.nanmax(df_display[pop_cols_display].to_numpy()))

# Build the table
gt = (
    GT(df_display, rowname_col="Town")
    # Spanners for logical grouping
    .tab_spanner(label="1996", columns=["Pop 1996", "Density 1996"])
    .tab_spanner(label="2001", columns=["Pop 2001", "Density 2001"])
    .tab_spanner(label="2006", columns=["Pop 2006", "Density 2006"])
    .tab_spanner(label="2011", columns=["Pop 2011", "Density 2011"])
    .tab_spanner(label="2016", columns=["Pop 2016", "Density 2016"])
    .tab_spanner(label="2021", columns=["Pop 2021", "Density 2021"])
    .tab_spanner(label="Period Change %", columns=pop_growth_cols)
    # Format population columns with gradient fill (Big Color - Blues for neutral magnitude)
    .data_color(
        columns=pop_cols_display,
        palette="Blues",
        domain=[pop_min, pop_max],
        truncate=False,
        na_color="#808080",
    )
    # Format numbers and percentages
    .fmt_number(columns=pop_cols_display, decimals=0, use_seps=True)
    .fmt_number(columns=["Density 1996", "Density 2001", "Density 2006", "Density 2011", "Density 2016", "Density 2021"], decimals=1, use_seps=True)
    .fmt_percent(columns=pop_growth_cols, decimals=1, scale_values=False)
    # Stub styling
    .tab_style(
        style=style.fill(color="#EAF0F6"),  # Washed-DA Navy tint for stub
        locations=loc.stub(),
    )
    # Column hairlines
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Column-group vertical dividers (last column of each spanner group)
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.body(columns="Density 1996"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.column_labels(columns="Density 1996"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.body(columns="Density 2001"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.column_labels(columns="Density 2001"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.body(columns="Density 2006"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.column_labels(columns="Density 2006"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.body(columns="Density 2011"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.column_labels(columns="Density 2011"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.body(columns="Density 2016"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.column_labels(columns="Density 2016"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.body(columns="Growth 16-21 %"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.column_labels(columns="Growth 16-21 %"),
    )
    # Row striping (≥10 rows and body not fully colored)
    .opt_row_striping()
    # Heading band - light tint since we have Big Color (Blues)
    .tab_options(
        heading_background_color="#EAF0F6",  # Washed-DA Navy
        row_striping_background_color="#F6F6F6",
    )
    # Frame
    .tab_options(
        table_border_top_style="solid",
        table_border_top_color="#CCCCCC",
        table_border_top_width="1px",
        table_border_bottom_style="solid",
        table_border_bottom_color="#CCCCCC",
        table_border_bottom_width="1px",
        table_border_left_style="solid",
        table_border_left_color="#CCCCCC",
        table_border_left_width="1px",
        table_border_right_style="solid",
        table_border_right_color="#CCCCCC",
        table_border_right_width="1px",
    )
    # Titles and annotations
    .tab_header(
        title="Ontario's Fastest-Growing Towns: Population & Density Trends (1996–2021)",
        subtitle="Top 15 towns by overall population growth, showing census snapshots and period-to-period percent changes"
    )
    .tab_source_note(source_note="Fastest-growing reflects the highest absolute percent increase from 1996 to 2021, not the average of intervening periods.")
    .tab_source_note(source_note="Source: Statistics Canada Census subdivisions, 1996–2021.")
)

# Render and save
gt.gtsave("table.png", expand=15, vwidth=1600, vheight=900, zoom=2.0)
