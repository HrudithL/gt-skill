import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc

# STEP 1: UNDERSTAND AND CLEAN DATA
df = pd.read_csv("towny.csv")

# Identify density columns and percentage change columns
density_cols = [col for col in df.columns if col.startswith("density_")]
pct_change_cols = [col for col in df.columns if col.startswith("pop_change_")]

# Calculate total population growth 1996-2021 for ranking
df["total_growth_pct"] = ((df["population_2021"] - df["population_1996"]) / df["population_1996"])

# Get top 15 fastest-growing towns
top_15 = df.nlargest(15, "total_growth_pct").copy()
top_15 = top_15.reset_index(drop=True)

# Create display dataframe with selected columns
display_cols = ["name"] + density_cols + pct_change_cols
display_df = top_15[display_cols].copy()
display_df.columns = ["Town"] + [f"Density {y}" for y in ["1996", "2001", "2006", "2011", "2016", "2021"]] + \
                     [f"Change {p}" for p in ["96-01", "01-06", "06-11", "11-16", "16-21"]]

# STEP 2: ORGANIZE COLUMNS
# Town name is the stub (rowname_col), density values in first group, pct changes in second group

# STEP 3: BIG COLOR
# Two measures qualify: density values (magnitude) and percentage changes (growth).
# Priority: percentage changes are more directly the hero (growth) based on the prompt "growth trends"
# Color the percentage change columns with Greens palette

pct_cols_display = [f"Change {p}" for p in ["96-01", "01-06", "06-11", "11-16", "16-21"]]
lo_pct = float(np.nanmin(top_15[pct_change_cols].to_numpy()))
hi_pct = float(np.nanmax(top_15[pct_change_cols].to_numpy()))

# Percentage changes can be negative or positive - but growth is "more is better"
# So we use a sequential palette (Greens) not diverging
density_cols_display = [f"Density {y}" for y in ["1996", "2001", "2006", "2011", "2016", "2021"]]
lo_density = float(np.nanmin(top_15[density_cols].to_numpy()))
hi_density = float(np.nanmax(top_15[density_cols].to_numpy()))

# STEP 4: HEADING BAND
# Since we have Big Color (the percentage changes), use light washed-DA tint
# Growth theme suggests Forest hue, but let's use Greens palette - so Navy/default band with washed tint
# Actually, for growth/Greens, use Forest hue: #EAF1EC washed tint

# STEP 5: SMALL COLOR & CONSTRUCTION
gt = (
    GT(display_df, rowname_col="Town")
    # Organize into column groups (spanners)
    .tab_spanner(label="Population Density (per km²)", columns=density_cols_display)
    .tab_spanner(label="Population % Change", columns=pct_cols_display)

    # Format density columns as numbers with 1 decimal
    .fmt_number(columns=density_cols_display, decimals=1, use_seps=True)

    # Format percentage change columns
    .fmt_percent(columns=pct_cols_display, decimals=1, scale_values=False)

    # BIG COLOR: Color percentage change columns (growth = Greens palette)
    .data_color(
        columns=pct_cols_display,
        palette="Greens",
        domain=[lo_pct, hi_pct],
        truncate=False,
        na_color="#808080",
    )

    # HEADING BAND: Light washed tint (Forest hue for growth theme)
    .tab_options(
        column_labels_background_color="#EAF1EC",  # Forest washed tint
        column_labels_font_weight="bold",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )

    # SMALL COLOR: Frame with borders
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

    # Body row hairlines
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )

    # Column group vertical dividers (between Density and Change groups)
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.body(columns="Density 2021"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.column_labels(columns="Density 2021"),
    )

    # Row striping (≥10 rows and not fully filled by color)
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")

    # Stub tint (harmonized to Forest washed tint for grey-budget consistency)
    .tab_style(
        style=style.fill(color="#EAF1EC"),
        locations=loc.stub(),
    )

    # TITLES & ANNOTATIONS
    .tab_header(
        title="Fastest-Growing Ontario Towns (1996-2021)",
        subtitle="Population density and growth rates across Census periods",
    )
)

# Add source notes (two separate calls per small_color.md requirement)
gt = (
    gt.tab_source_note(
        source_note="Fastest-growing determined by total population percent change from 1996 to 2021. Percentage changes shown for each 5-year Census period."
    )
    .tab_source_note(
        source_note="Source: Statistics Canada Census subdivisions, 1996–2021."
    )
)

# STEP 7: RENDER & VERIFY
gt.gtsave("table.png", expand=15)
