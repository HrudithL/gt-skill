import pandas as pd
import numpy as np
from great_tables import GT, html, style, loc

df = pd.read_csv("towny.csv")

# STEP 1: UNDERSTAND & CLEAN DATA
# Calculate overall growth rate 1996-2021 to identify fastest-growing towns
df["growth_rate_overall"] = (df["population_2021"] - df["population_1996"]) / df["population_1996"]

# Get top 15 fastest-growing towns
top15 = df.nlargest(15, "growth_rate_overall")[
    ["name", "density_1996", "density_2001", "density_2006", "density_2011", "density_2016", "density_2021",
     "pop_change_1996_2001_pct", "pop_change_2001_2006_pct", "pop_change_2006_2011_pct",
     "pop_change_2011_2016_pct", "pop_change_2016_2021_pct"]
].reset_index(drop=True)

# Rename columns for clarity
top15.columns = [
    "Town",
    "Density 1996", "Density 2001", "Density 2006", "Density 2011", "Density 2016", "Density 2021",
    "% Change 1996–2001", "% Change 2001–2006", "% Change 2006–2011",
    "% Change 2011–2016", "% Change 2016–2021"
]

# STEP 3: BIG COLOR — column gradient for density values (ordered magnitude, ≥5 rows)
# Density is a neutral magnitude → Blues palette
density_cols = ["Density 1996", "Density 2001", "Density 2006", "Density 2011", "Density 2016", "Density 2021"]
density_vals = top15[density_cols].to_numpy()
density_min = float(np.nanmin(density_vals))
density_max = float(np.nanmax(density_vals))

# STEP 4: HEADING BAND — Big Color present (Blues) → light washed-blue tint band
# STEP 5: SMALL COLOR POLISH

gt = (
    GT(top15, rowname_col="Town")
    .tab_header(
        title="Ontario's Fastest-Growing Towns: Population Density Trends",
        subtitle="Top 15 towns by growth rate, 1996–2021, with density changes per census period"
    )
    # Column spanners: group density years together, group percentage changes together
    .tab_spanner(label="Population Density (persons/km²)", columns=density_cols)
    .tab_spanner(label="Population Change (%)", columns=[
        "% Change 1996–2001", "% Change 2001–2006", "% Change 2006–2011",
        "% Change 2011–2016", "% Change 2016–2021"
    ])
    # Format density values with 1 decimal (appropriate precision for density)
    .fmt_number(columns=density_cols, decimals=1, use_seps=True)
    # Format percentage changes with 1 decimal, show sign
    .fmt_percent(
        columns=["% Change 1996–2001", "% Change 2001–2006", "% Change 2006–2011",
                 "% Change 2011–2016", "% Change 2016–2021"],
        decimals=1,
        force_sign=True,
        scale_values=False
    )
    # Apply gradient fill to density columns (Big Color Step 3)
    .data_color(
        columns=density_cols,
        palette="Blues",
        domain=[density_min, density_max],
        truncate=False,
        na_color="#808080"
    )
    # Missing values as em dash
    .sub_missing(
        columns=density_cols + ["% Change 1996–2001", "% Change 2001–2006", "% Change 2006–2011",
                               "% Change 2011–2016", "% Change 2016–2021"],
        missing_text="—"
    )
    # STEP 5 (a): Cell borders — light hairline
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        # Column label bottom rule (constant across all tables)
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # STEP 5 (b): Column-group vertical dividers at group boundaries
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.body(columns="Density 2021")
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.column_labels(columns="Density 2021")
    )
    # STEP 5 (c): Row striping (≥10 rows, not fully covered by Big Color) — density fills are in columns, not full
    .opt_row_striping()
    # STEP 5 (d): Stub tint — light washed-blue to match Blues palette (grey-budget rule: harmonize to Big Color hue)
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub()
    )
    # STEP 4: Heading band — light washed-blue (Big Color is Blues, so use washed tint)
    .tab_options(
        heading_background_color="#EAF0F6",
        column_labels_background_color="#EAF0F6",
        row_striping_background_color="#F6F6F6",
    )
    .tab_source_note(
        source_note="Source: Statistics Canada Census of Population (1996–2021). Density = population per square kilometre."
    )
)

gt.gtsave("table.png")
