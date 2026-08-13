import pandas as pd
import numpy as np
from great_tables import GT, style, loc, md

# Read the data
df = pd.read_csv("towny.csv")

# Calculate overall growth from 1996 to 2021
df["overall_growth_pct"] = (df["population_2021"] - df["population_1996"]) / df["population_1996"]

# Get top 15 fastest-growing towns
top_15 = df.nlargest(15, "overall_growth_pct").copy()

# Reset index for clean display
top_15 = top_15.reset_index(drop=True)

# Select and organize columns for the display
display_df = top_15[[
    "name",
    "density_1996",
    "density_2001",
    "density_2006",
    "density_2011",
    "density_2016",
    "density_2021",
    "pop_change_1996_2001_pct",
    "pop_change_2001_2006_pct",
    "pop_change_2006_2011_pct",
    "pop_change_2011_2016_pct",
    "pop_change_2016_2021_pct",
]].copy()

# Rename columns for clarity
display_df.columns = [
    "Town",
    "1996",
    "2001",
    "2006",
    "2011",
    "2016",
    "2021",
    "1996-2001",
    "2001-2006",
    "2006-2011",
    "2011-2016",
    "2016-2021",
]

# Calculate domains for gradient fills
density_cols = ["1996", "2001", "2006", "2011", "2016", "2021"]
pct_cols = ["1996-2001", "2001-2006", "2006-2011", "2011-2016", "2016-2021"]

density_lo = float(np.nanmin(display_df[density_cols].to_numpy()))
density_hi = float(np.nanmax(display_df[density_cols].to_numpy()))

pct_lo = float(np.nanmin(display_df[pct_cols].to_numpy()))
pct_hi = float(np.nanmax(display_df[pct_cols].to_numpy()))

# Build the table
gt = (
    GT(display_df, rowname_col="Town")
    .tab_header(
        title="Ontario's Fastest-Growing Towns (1996–2021)",
        subtitle="Population Density and Growth Rates by Census Period",
    )
    .tab_spanner(label="Density (persons/km²)", columns=density_cols)
    .tab_spanner(label="Population Change (%)", columns=pct_cols)
    .fmt_number(
        columns=density_cols,
        decimals=1,
        use_seps=True,
    )
    .fmt_percent(
        columns=pct_cols,
        decimals=1,
        force_sign=True,
    )
    .data_color(
        columns=density_cols,
        palette="Blues",
        domain=[density_lo, density_hi],
        truncate=False,
        na_color="#808080",
    )
    .data_color(
        columns=pct_cols,
        palette="RdYlGn",
        domain=[pct_lo, pct_hi],
        truncate=False,
        na_color="#808080",
    )
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    .tab_style(
        style=style.text(color="white"),
        locations=loc.column_labels(),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.body(columns="2021"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.column_labels(columns="2021"),
    )
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
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
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        heading_background_color="#08306B",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    .opt_row_striping()
    .tab_source_note(
        source_note="Fastest-growing means highest percent change across the full 1996–2021 span. Density is population per square kilometer."
    )
    .tab_source_note(
        source_note="Source: Statistics Canada Census subdivisions, 1996–2021."
    )
    .cols_width(cases={
        "Town": "160px",
        "1996": "90px",
        "2001": "90px",
        "2006": "90px",
        "2011": "90px",
        "2016": "90px",
        "2021": "90px",
        "1996-2001": "95px",
        "2001-2006": "95px",
        "2006-2011": "95px",
        "2011-2016": "95px",
        "2016-2021": "95px",
    })
)

gt.gtsave("table.png", expand=15)
