import numpy as np
import pandas as pd
from great_tables import GT, loc, style, md

df = pd.read_csv("towny.csv")

# Compute overall growth rate from 1996 to 2021
overall_growth = np.where(
    df["population_1996"] > 0,
    (df["population_2021"] - df["population_1996"]) / df["population_1996"],
    np.nan
)
df["overall_growth_rate"] = pd.to_numeric(overall_growth)

# Filter to top 15 fastest-growing towns by overall growth rate
top_15 = df.nlargest(15, "overall_growth_rate").reset_index(drop=True)
top_15["rank"] = top_15.index + 1

# Select and order columns: rank, name, then density for each year, then % change between periods
cols_to_keep = [
    "rank",
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
]
top_15 = top_15[cols_to_keep]

# Compute domain for percentage changes (all pct change columns)
pct_cols = [
    "pop_change_1996_2001_pct",
    "pop_change_2001_2006_pct",
    "pop_change_2006_2011_pct",
    "pop_change_2011_2016_pct",
    "pop_change_2016_2021_pct",
]
pct_lo = float(np.nanmin(top_15[pct_cols].to_numpy()))
pct_hi = float(np.nanmax(top_15[pct_cols].to_numpy()))

# Compute domain for density values (all density columns)
density_cols = [
    "density_1996",
    "density_2001",
    "density_2006",
    "density_2011",
    "density_2016",
    "density_2021",
]
density_lo = float(np.nanmin(top_15[density_cols].to_numpy()))
density_hi = float(np.nanmax(top_15[density_cols].to_numpy()))

gt = (
    GT(top_15, rowname_col="rank")
    .tab_header(
        title="Top 15 Fastest-Growing Ontario Towns",
        subtitle="Population density and growth rates across census years (1996–2021)",
    )
    .cols_label(
        rank="#",
        name="Town",
        density_1996="1996",
        density_2001="2001",
        density_2006="2006",
        density_2011="2011",
        density_2016="2016",
        density_2021="2021",
        pop_change_1996_2001_pct="1996–2001",
        pop_change_2001_2006_pct="2001–2006",
        pop_change_2006_2011_pct="2006–2011",
        pop_change_2011_2016_pct="2011–2016",
        pop_change_2016_2021_pct="2016–2021",
    )
    .tab_spanner(label="Density (people/km²)", columns=density_cols)
    .tab_spanner(label="Population Growth %", columns=pct_cols)
    # Format density columns as numbers with 1 decimal
    .fmt_number(columns=density_cols, decimals=1, use_seps=True)
    # Format percentage change columns as percent with 1 decimal
    .fmt_percent(columns=pct_cols, decimals=1)
    # Add missing value handling
    .sub_missing(columns=density_cols + pct_cols, missing_text="—")
    # Big Color: gradient fill on density to show magnitude
    .data_color(
        columns=density_cols,
        palette="Blues",
        domain=[density_lo, density_hi],
        truncate=False,
        na_color="#808080",
    )
    # Big Color: gradient fill on percentage changes (green for growth)
    .data_color(
        columns=pct_cols,
        palette="Greens",
        domain=[pct_lo, pct_hi],
        truncate=False,
        na_color="#808080",
    )
    # Highlight top 3 rows with light background
    .tab_style(
        style=style.fill(color="#fff4d6"),
        locations=loc.body(rows=[0, 1, 2]),
    )
    .tab_style(
        style=style.text(weight="bold"),
        locations=loc.body(columns=["rank"], rows=[0, 1, 2]),
    )
    # Bold the town name in top 3
    .tab_style(
        style=style.text(weight="bold"),
        locations=loc.body(columns=["name"], rows=[0, 1, 2]),
    )
    # Bold rank column across all rows
    .tab_style(
        style=style.text(weight="bold"),
        locations=loc.body(columns=["rank"]),
    )
    # Align: left for text columns, right for numbers
    .cols_align(align="left", columns=["name"])
    .cols_align(align="right", columns=["rank"] + density_cols + pct_cols)
    # Heading band (light washed tint for Blues primary Big Color)
    .tab_options(column_labels_background_color="#EAF0F6")
    # Cell borders
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
        # Frame
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
    # Stub tint (light grey to separate from value columns)
    .tab_style(
        style=style.fill(color="#F0F0F0"),
        locations=loc.stub(),
    )
    # Row striping (≥10 rows and Big Color present, so apply)
    .opt_row_striping()
    # Column group dividers
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.body(columns="density_2021"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.column_labels(columns="density_2021"),
    )
    # Source note explaining the ranking metric
    .tab_source_note(
        source_note="Towns ranked by overall population growth rate from 1996 to 2021. "
                    "Percentage changes computed as period-over-period growth: (end − start) / start."
    )
    .tab_source_note(source_note="Source: Ontario census data (1996–2021).")
)

gt.gtsave("table.png", expand=15)
