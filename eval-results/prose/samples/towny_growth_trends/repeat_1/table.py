import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Load and clean data
df = pd.read_csv("towny.csv")

# Compute overall growth (1996 to 2021)
df["total_pop_change_pct"] = np.where(
    df["population_1996"] > 0,
    (df["population_2021"] - df["population_1996"]) / df["population_1996"],
    np.nan
)

# Identify top 15 fastest-growing towns
top_15 = df.nlargest(15, "total_pop_change_pct")[["name", "density_1996", "density_2001", "density_2006", "density_2011", "density_2016", "density_2021", "pop_change_1996_2001_pct", "pop_change_2001_2006_pct", "pop_change_2006_2011_pct", "pop_change_2011_2016_pct", "pop_change_2016_2021_pct"]].copy()

# Rename columns for display
top_15.columns = ["Town", "Density 1996", "Density 2001", "Density 2006", "Density 2011", "Density 2016", "Density 2021", "% Change 1996-2001", "% Change 2001-2006", "% Change 2006-2011", "% Change 2011-2016", "% Change 2016-2021"]

# Reset index
top_15 = top_15.reset_index(drop=True)

# Compute domains for coloring
density_cols = ["Density 1996", "Density 2001", "Density 2006", "Density 2011", "Density 2016", "Density 2021"]
density_lo = float(np.nanmin(top_15[density_cols].to_numpy()))
density_hi = float(np.nanmax(top_15[density_cols].to_numpy()))

pct_cols = ["% Change 1996-2001", "% Change 2001-2006", "% Change 2006-2011", "% Change 2011-2016", "% Change 2016-2021"]
pct_lo = float(np.nanmin(top_15[pct_cols].to_numpy()))
pct_hi = float(np.nanmax(top_15[pct_cols].to_numpy()))

# Diverging domain must be symmetric
pct_max = max(abs(pct_lo), abs(pct_hi))
pct_domain = [-pct_max, pct_max]

# Create GT table
gt = (
    GT(top_15, rowname_col="Town")
    # Format density columns
    .fmt_number(columns=density_cols, decimals=1, use_seps=True)
    # Format percent change columns
    .fmt_percent(columns=pct_cols, decimals=1, force_sign=True)
    # Color density (sequential Blue gradient)
    .data_color(
        columns=density_cols,
        palette="Blues",
        domain=[density_lo, density_hi],
        truncate=False,
        na_color="#808080",
    )
    # Color percent change (diverging RdYlGn)
    .data_color(
        columns=pct_cols,
        palette="RdYlGn",
        domain=pct_domain,
        truncate=False,
        na_color="#808080",
    )
    # Column spanners
    .tab_spanner(label="Population Density (persons/km²)", columns=density_cols)
    .tab_spanner(label="Population Change (%)", columns=pct_cols)
    # Heading band
    .tab_options(
        column_labels_background_color="#08306B",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # White text in header
    .tab_style(
        style=style.text(color="white"),
        locations=loc.column_labels(),
    )
    # Body row hairlines
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
    # Stub tint
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # Column dividers at spanner boundaries
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.body(columns="Density 2021"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.column_labels(columns="Density 2021"),
    )
    # Row striping
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
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
    # Column widths (compact layout)
    .cols_width(cases={
        "Density 1996": "110px",
        "Density 2001": "110px",
        "Density 2006": "110px",
        "Density 2011": "110px",
        "Density 2016": "110px",
        "Density 2021": "110px",
        "% Change 1996-2001": "110px",
        "% Change 2001-2006": "110px",
        "% Change 2006-2011": "110px",
        "% Change 2011-2016": "110px",
        "% Change 2016-2021": "110px",
    })
    # Padding
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    # Titles
    .tab_header(
        title="Ontario's Fastest-Growing Towns (1996–2021)",
        subtitle="Population Density and Growth Rates Across Census Periods",
    )
    # Footer notes
    .tab_source_note(source_note="Fastest-growing is ranked by highest percent population change from 1996 to 2021. Density is population per square kilometer.")
    .tab_source_note(source_note="Source: Statistics Canada Census subdivisions, 1996–2021 (towny.csv).")
)

# Render
gt.gtsave("table.png", expand=15)
print("Table rendered successfully to table.png")
