import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc
from gt_consistency import PALETTE, frame, finalize, heatmap, band, stripe, stub_tint

df = pd.read_csv("towny.csv")

# Calculate total population growth 1996-2021
df["total_growth_pct"] = (df["population_2021"] - df["population_1996"]) / df["population_1996"]

# Get top 15 fastest-growing towns by total growth percentage
top_15 = df.nlargest(15, "total_growth_pct")[
    [
        "name",
        "population_1996",
        "density_1996",
        "population_2001",
        "density_2001",
        "population_2006",
        "density_2006",
        "population_2011",
        "density_2011",
        "population_2016",
        "density_2016",
        "population_2021",
        "density_2021",
        "pop_change_1996_2001_pct",
        "pop_change_2001_2006_pct",
        "pop_change_2006_2011_pct",
        "pop_change_2011_2016_pct",
        "pop_change_2016_2021_pct",
    ]
].copy()

top_15 = top_15.reset_index(drop=True)

# Prepare display dataframe with organized columns
display_df = pd.DataFrame({
    "Town": top_15["name"],
    "Pop 1996": top_15["population_1996"],
    "Dens 1996": top_15["density_1996"],
    "Pop 2001": top_15["population_2001"],
    "Dens 2001": top_15["density_2001"],
    "Pop 2006": top_15["population_2006"],
    "Dens 2006": top_15["density_2006"],
    "Pop 2011": top_15["population_2011"],
    "Dens 2011": top_15["density_2011"],
    "Pop 2016": top_15["population_2016"],
    "Dens 2016": top_15["density_2016"],
    "Pop 2021": top_15["population_2021"],
    "Dens 2021": top_15["density_2021"],
    "Ch 96-01": top_15["pop_change_1996_2001_pct"],
    "Ch 01-06": top_15["pop_change_2001_2006_pct"],
    "Ch 06-11": top_15["pop_change_2006_2011_pct"],
    "Ch 11-16": top_15["pop_change_2011_2016_pct"],
    "Ch 16-21": top_15["pop_change_2016_2021_pct"],
})

# Compute domains for heatmaps
density_cols = ["Dens 1996", "Dens 2001", "Dens 2006", "Dens 2011", "Dens 2016", "Dens 2021"]
density_lo = float(np.nanmin(display_df[density_cols].to_numpy()))
density_hi = float(np.nanmax(display_df[density_cols].to_numpy()))

pct_cols = ["Ch 96-01", "Ch 01-06", "Ch 06-11", "Ch 11-16", "Ch 16-21"]
pct_lo = float(np.nanmin(display_df[pct_cols].to_numpy()))
pct_hi = float(np.nanmax(display_df[pct_cols].to_numpy()))
pct_max = max(abs(pct_lo), abs(pct_hi))

gt = (
    GT(display_df, rowname_col="Town")
    .tab_spanner(label="Population & Density", columns=["Pop 1996", "Dens 1996", "Pop 2001", "Dens 2001", "Pop 2006", "Dens 2006", "Pop 2011", "Dens 2011", "Pop 2016", "Dens 2016", "Pop 2021", "Dens 2021"])
    .tab_spanner(label="Period Growth %", columns=["Ch 96-01", "Ch 01-06", "Ch 06-11", "Ch 11-16", "Ch 16-21"])
    .cols_width(cases={
        "Town": "140px",
        "Pop 1996": "70px",
        "Dens 1996": "70px",
        "Pop 2001": "70px",
        "Dens 2001": "70px",
        "Pop 2006": "70px",
        "Dens 2006": "70px",
        "Pop 2011": "70px",
        "Dens 2011": "70px",
        "Pop 2016": "70px",
        "Dens 2016": "70px",
        "Pop 2021": "70px",
        "Dens 2021": "70px",
        "Ch 96-01": "65px",
        "Ch 01-06": "65px",
        "Ch 06-11": "65px",
        "Ch 11-16": "65px",
        "Ch 16-21": "65px",
    })
    .fmt_number(columns=["Pop 1996", "Pop 2001", "Pop 2006", "Pop 2011", "Pop 2016", "Pop 2021"], decimals=0, use_seps=True)
    .fmt_number(columns=density_cols, decimals=1, use_seps=False)
    .fmt_percent(columns=pct_cols, decimals=1, force_sign=True)
    .sub_missing(columns=display_df.columns.tolist(), missing_text="—")
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
        domain=[-pct_max, pct_max],
        truncate=False,
        na_color="#808080",
    )
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.body(columns="Dens 2021"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.column_labels(columns="Dens 2021"),
    )
    .opt_row_striping()
    .tab_header(
        title="Top 15 Fastest-Growing Ontario Towns (1996–2021)",
        subtitle="Population growth trends with density changes across census years"
    )
    .tab_source_note(source_note="Fastest-growing towns ranked by total population percent change from 1996 to 2021. Period growth percentages show changes between consecutive census years.")
    .tab_source_note(source_note="Source: Statistics Canada Census subdivisions, 1996–2021.")
)

gt = gt.tab_options(
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
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

gt = band(gt)

finalize(gt, "table.png")
