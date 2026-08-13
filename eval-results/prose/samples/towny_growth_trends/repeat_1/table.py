import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc

# Step 1: UNDERSTAND & CLEAN THE DATA
df = pd.read_csv("./towny.csv")

# Calculate total growth 1996-2021 as the ranking metric
df["total_growth_pct"] = (df["population_2021"] - df["population_1996"]) / df["population_1996"]

# Get top 15 fastest-growing towns
top_15 = df.nlargest(15, "total_growth_pct").copy().reset_index(drop=True)

# Prepare columns for the table
# Keep: name, density columns, percent change columns
density_cols = ["density_1996", "density_2001", "density_2006", "density_2011", "density_2016", "density_2021"]
pct_change_cols = ["pop_change_1996_2001_pct", "pop_change_2001_2006_pct", "pop_change_2006_2011_pct", "pop_change_2011_2016_pct", "pop_change_2016_2021_pct"]

# Ensure all numeric columns are proper floats
for col in density_cols + pct_change_cols:
    top_15[col] = pd.to_numeric(top_15[col], errors="coerce")

# Keep only needed columns
display_df = top_15[["name"] + density_cols + pct_change_cols].copy()

# Rename columns for display
rename_map = {
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
}
display_df = display_df.rename(columns=rename_map)

# Step 2: ORGANIZE COLUMNS & Step 3: BIG COLOR DECISIONS
# Density columns: sequential fill (magnitude)
# Percent change columns: signed values, need to check range
print("Density range:", display_df[["1996", "2001", "2006", "2011", "2016", "2021"]].min().min(),
      "to", display_df[["1996", "2001", "2006", "2011", "2016", "2021"]].max().max())
print("Pct change range:", display_df[["1996–2001", "2001–2006", "2006–2011", "2011–2016", "2016–2021"]].min().min(),
      "to", display_df[["1996–2001", "2001–2006", "2006–2011", "2011–2016", "2016–2021"]].max().max())

# Compute domains for data_color
density_cols_display = ["1996", "2001", "2006", "2011", "2016", "2021"]
pct_change_cols_display = ["1996–2001", "2001–2006", "2006–2011", "2011–2016", "2016–2021"]

density_lo = float(np.nanmin(display_df[density_cols_display].to_numpy()))
density_hi = float(np.nanmax(display_df[density_cols_display].to_numpy()))

pct_lo = float(np.nanmin(display_df[pct_change_cols_display].to_numpy()))
pct_hi = float(np.nanmax(display_df[pct_change_cols_display].to_numpy()))

# Percent change is signed (has both negative and positive), so use diverging fill
# But first check if it actually spans both directions
if pct_lo < 0 and pct_hi > 0:
    # Use diverging palette for percent change
    pct_domain = [-max(abs(pct_lo), abs(pct_hi)), max(abs(pct_lo), abs(pct_hi))]
    use_diverging = True
else:
    # All positive or all negative, use sequential
    use_diverging = False
    pct_domain = [pct_lo, pct_hi]

print(f"Percent change diverging: {use_diverging}, domain: {pct_domain}")

# Step 4 & 5: Build the table
gt = (
    GT(display_df, rowname_col="Town")
    # Step 4: HEADING BAND (fixed, dark navy)
    .tab_header(
        title="Population Growth Trends: Ontario's Fastest-Growing Towns (1996–2021)",
        subtitle="Density (persons/km²) and Census Period Growth Rates"
    )
    # Column labels
    .cols_label(cases={})
    # Step 2: Add column spanners for grouping
    .tab_spanner(label="Density (persons/km²)", columns=density_cols_display)
    .tab_spanner(label="% Change per Period", columns=pct_change_cols_display)
    # Step 5: SMALL COLOR - Format all numeric columns
    .fmt_number(columns=density_cols_display, decimals=1, use_seps=True)
    .fmt_percent(columns=pct_change_cols_display, decimals=1, force_sign=True, scale_values=False)
    .sub_missing(columns=density_cols_display + pct_change_cols_display, missing_text="—")
    # Step 3: BIG COLOR - Apply gradient fills
    # Density: sequential Blues (neutral magnitude)
    .data_color(
        columns=density_cols_display,
        palette="Blues",
        domain=[density_lo, density_hi],
        truncate=False,
        na_color="#808080",
    )
    # Percent change: diverging RdYlGn if signed, else sequential Greens (growth)
    .data_color(
        columns=pct_change_cols_display,
        palette="RdYlGn" if use_diverging else "Greens",
        domain=pct_domain,
        truncate=False,
        na_color="#808080",
    )
    # Step 5: SMALL COLOR - Cell borders (hairlines between rows) & stripe color
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
        row_striping_background_color="#F6F6F6",
    )
    # Step 5: Column-group vertical dividers (seam between Density and % Change groups)
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.body(columns="2021"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.column_labels(columns="2021"),
    )
    # Step 5: Row striping
    .opt_row_striping()
    # Step 5: Stub tint
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # Step 5: Column widths (compact layout)
    .cols_width(cases={
        "Town": "180px",
        "1996": "90px",
        "2001": "90px",
        "2006": "90px",
        "2011": "90px",
        "2016": "90px",
        "2021": "90px",
        "1996–2001": "100px",
        "2001–2006": "100px",
        "2006–2011": "100px",
        "2011–2016": "100px",
        "2016–2021": "100px",
    })
    # Padding (compact)
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    # Frame border (all four sides + margin)
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
    # Step 6: TITLES & ANNOTATIONS (two separate footer calls)
    .tab_source_note(source_note="Fastest-growing towns ranked by total population growth 1996–2021. Density values are persons per square kilometer.")
    .tab_source_note(source_note="Source: Statistics Canada Census subdivisions, 1996–2021.")
)

# Step 7: RENDER & VERIFY
gt.gtsave("table.png", expand=15, zoom=2.0)
print("Table rendered to table.png")
