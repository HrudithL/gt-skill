import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc

# Step 1: Data cleaning
df = pd.read_csv("towny.csv")

# Calculate overall growth rate (1996-2021)
df["overall_growth_pct"] = (
    (df["population_2021"] - df["population_1996"]) / df["population_1996"]
)

# Get top 15 fastest-growing towns
df_top15 = df.nlargest(15, "overall_growth_pct").copy()
df_top15 = df_top15.reset_index(drop=True)

# Build display table with density values and density percent changes
display_data = []
for idx, row in df_top15.iterrows():
    display_data.append({
        "Town": row["name"],
        "Growth_Overall": row["overall_growth_pct"],
        "Density_1996": row["density_1996"],
        "Density_2001": row["density_2001"],
        "Density_2006": row["density_2006"],
        "Density_2011": row["density_2011"],
        "Density_2016": row["density_2016"],
        "Density_2021": row["density_2021"],
        "Density_Chg_9601": row["pop_change_1996_2001_pct"],
        "Density_Chg_0106": row["pop_change_2001_2006_pct"],
        "Density_Chg_0611": row["pop_change_2006_2011_pct"],
        "Density_Chg_1116": row["pop_change_2011_2016_pct"],
        "Density_Chg_1621": row["pop_change_2016_2021_pct"],
    })

display_df = pd.DataFrame(display_data)

# Ensure all numeric columns are float
numeric_cols = display_df.select_dtypes(include=["number"]).columns
for col in numeric_cols:
    display_df[col] = display_df[col].astype(float)

# Step 2: Organize columns
# Stub: Town; Density columns; Percent-change columns

# Step 3: Determine coloring
# Density levels are a neutral magnitude (Blues)
density_cols = ["Density_1996", "Density_2001", "Density_2006", "Density_2011", "Density_2016", "Density_2021"]
pct_change_cols = ["Density_Chg_9601", "Density_Chg_0106", "Density_Chg_0611", "Density_Chg_1116", "Density_Chg_1621"]

# Compute domains for color fills
density_lo = float(np.nanmin(display_df[density_cols].to_numpy()))
density_hi = float(np.nanmax(display_df[density_cols].to_numpy()))

# For percent-change (diverging): symmetric domain
pct_max_abs = float(np.nanmax(np.abs(display_df[pct_change_cols].to_numpy())))
pct_domain = [-pct_max_abs, pct_max_abs]

# Step 4 & 5: Build the table
gt = (
    GT(display_df, rowname_col="Town")
    # Step 4: Heading band (dark navy, built-in)
    .tab_header(
        title="Top 15 Fastest-Growing Ontario Towns",
        subtitle="Population density evolution and period-over-period growth, 1996–2021"
    )
    # Step 2b: Column organization with spanners
    .tab_spanner(label="Population Density (persons/km²)", columns=density_cols)
    .tab_spanner(label="Percent Change", columns=pct_change_cols)
    # Reorder to ensure density is before percent change
    .cols_move_to_start(columns=["Growth_Overall"])
    # Column labels
    .cols_label(
        Growth_Overall="Overall Growth",
        Density_1996="1996",
        Density_2001="2001",
        Density_2006="2006",
        Density_2011="2011",
        Density_2016="2016",
        Density_2021="2021",
        Density_Chg_9601="1996–2001",
        Density_Chg_0106="2001–2006",
        Density_Chg_0611="2006–2011",
        Density_Chg_1116="2011–2016",
        Density_Chg_1621="2016–2021",
    )
    # Step 5a: Cell borders (hairlines)
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Step 3: Big Color — density (Blues, sequential)
    .data_color(
        columns=density_cols,
        palette="Blues",
        domain=[density_lo, density_hi],
        truncate=False,
        na_color="#808080",
    )
    # Step 3: Big Color — percent change (RdYlGn diverging, symmetric)
    .data_color(
        columns=pct_change_cols,
        palette="RdYlGn",
        domain=pct_domain,
        truncate=False,
        na_color="#808080",
    )
    # Step 5e: Formatting
    .fmt_number(columns=density_cols, decimals=1, use_seps=True)
    .fmt_percent(columns=pct_change_cols, decimals=1, force_sign=True)
    .fmt_percent(columns=["Growth_Overall"], decimals=1, force_sign=True)
    .sub_missing(columns=display_df.columns.tolist(), missing_text="—")
    # Step 5b: Column-group dividers
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.body(columns="Density_2021"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.column_labels(columns="Density_2021"),
    )
    # Step 5c: Row striping
    .opt_row_striping()
    # Step 5d: Stub tint
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # Step 5: Column widths (compact layout)
    .cols_width(cases={
        "Town": "160px",
        "Growth_Overall": "110px",
        "Density_1996": "100px",
        "Density_2001": "100px",
        "Density_2006": "100px",
        "Density_2011": "100px",
        "Density_2016": "100px",
        "Density_2021": "100px",
        "Density_Chg_9601": "100px",
        "Density_Chg_0106": "100px",
        "Density_Chg_0611": "100px",
        "Density_Chg_1116": "100px",
        "Density_Chg_1621": "100px",
    })
    # Step 5: Padding (compact layout)
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    # Step 4: Frame border
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
    # Step 6: Titles & annotations (two footer calls)
    .tab_source_note(
        source_note="Fastest-growing defined as highest overall population growth from 1996–2021. Density measured as population per square kilometre."
    )
    .tab_source_note(
        source_note="Source: Statistics Canada Census subdivisions, 1996–2021."
    )
)

# Step 7: Render
gt.gtsave("table.png", expand=15, zoom=2.0)
print("Table rendered successfully to table.png")
