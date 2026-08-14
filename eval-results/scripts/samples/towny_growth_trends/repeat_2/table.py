import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Load and clean data
df = pd.read_csv("towny.csv")

# Calculate total population growth from 1996 to 2021
df["total_growth_pct"] = (df["population_2021"] - df["population_1996"]) / df["population_1996"]

# Get top 15 fastest-growing towns
top15 = df.nlargest(15, "total_growth_pct").copy()

# Select and organize columns
cols_to_use = ["name", "density_1996", "density_2001", "density_2006", "density_2011", "density_2016", "density_2021",
               "pop_change_1996_2001_pct", "pop_change_2001_2006_pct", "pop_change_2006_2011_pct", "pop_change_2011_2016_pct", "pop_change_2016_2021_pct"]
top15 = top15[cols_to_use].reset_index(drop=True)

# Rename columns for display
top15 = top15.rename(columns={
    "name": "Town",
    "density_1996": "1996",
    "density_2001": "2001",
    "density_2006": "2006",
    "density_2011": "2011",
    "density_2016": "2016",
    "density_2021": "2021",
    "pop_change_1996_2001_pct": "1996–2001",
    "pop_change_2001_2006_pct": "2001–2006",
    "pop_change_2006_2011_pct": "2006–2011",
    "pop_change_2011_2016_pct": "2011–2016",
    "pop_change_2016_2021_pct": "2016–2021",
})

# Step 2: Organize columns
# Density columns: 1996, 2001, 2006, 2011, 2016, 2021
# Percent change columns: 1996–2001, 2001–2006, 2006–2011, 2011–2016, 2016–2021

# Step 3: Big Color - both density and percent change are ordered magnitudes
# Density: neutral magnitude → Blues
# Percent change: growth/positive direction → use appropriate palette with force_sign

# Density domain
density_cols = ["1996", "2001", "2006", "2011", "2016", "2021"]
density_lo = float(np.nanmin(top15[density_cols].to_numpy()))
density_hi = float(np.nanmax(top15[density_cols].to_numpy()))

# Percent change domain - symmetric for signed values
pct_cols = ["1996–2001", "2001–2006", "2006–2011", "2011–2016", "2016–2021"]
pct_lo = float(np.nanmin(top15[pct_cols].to_numpy()))
pct_hi = float(np.nanmax(top15[pct_cols].to_numpy()))
pct_domain_max = max(abs(pct_lo), abs(pct_hi))
pct_domain = [-pct_domain_max, pct_domain_max]

# Step 4 & 5: Create table with heading band, colors, and polish
gt = (
    GT(top15, rowname_col="Town")
    # Spanners for column groups
    .tab_spanner(label="Population Density (persons/km²)", columns=density_cols)
    .tab_spanner(label="Population Change (%)", columns=pct_cols)
    # Format columns
    .fmt_number(columns=density_cols, decimals=1, use_seps=True)
    .fmt_percent(columns=pct_cols, decimals=1, use_seps=True, force_sign=True)
    .sub_missing(columns=list(top15.columns), missing_text="—")
    # Big Color: density with Blues (neutral magnitude)
    .data_color(
        columns=density_cols,
        palette="Blues",
        domain=[density_lo, density_hi],
        truncate=False,
        na_color="#808080",
    )
    # Big Color: percent change with RdYlGn (diverging - positive = good/growth)
    .data_color(
        columns=pct_cols,
        palette="RdYlGn",
        domain=pct_domain,
        truncate=False,
        na_color="#808080",
    )
    # Step 4: Heading band (dark navy, white text)
    .tab_options(
        column_labels_background_color="#08306B",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    .tab_style(
        style=style.text(color="white"),
        locations=loc.column_labels(),
    )
    # Step 5a: Cell borders
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
    # Step 5b: Column-group vertical dividers
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.body(columns="2021"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.column_labels(columns="2021"),
    )
    # Step 5c: Row striping
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    # Step 5d: Stub tint
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # Step 5g: Compact layout
    .cols_width(cases={
        "Town": "180px",
        "1996": "100px",
        "2001": "100px",
        "2006": "100px",
        "2011": "100px",
        "2016": "100px",
        "2021": "100px",
        "1996–2001": "110px",
        "2001–2006": "110px",
        "2006–2011": "110px",
        "2011–2016": "110px",
        "2016–2021": "110px",
    })
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    # Frame - boxed border
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
    # Step 6: Titles & annotations
    .tab_header(
        title="Ontario's Fastest-Growing Towns: Population Density and Growth Trends",
        subtitle="Top 15 municipalities by total growth (1996–2021), with inter-Census period changes",
    )
    .tab_source_note(source_note="Fastest-growing means highest percent change across the full 1996–2021 span. Density = population ÷ land area (km²).")
    .tab_source_note(source_note="Source: Statistics Canada Census subdivisions, 1996–2021.")
)

# Render
gt.gtsave("table.png", expand=15, zoom=2.0)
print("Table rendered successfully to table.png")
