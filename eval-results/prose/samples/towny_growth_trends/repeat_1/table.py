import pandas as pd
import numpy as np
from great_tables import GT, md, loc, style

df = pd.read_csv("./towny.csv")

density_cols = [
    "density_1996",
    "density_2001",
    "density_2006",
    "density_2011",
    "density_2016",
    "density_2021",
]

pct_change_cols = [
    "pop_change_1996_2001_pct",
    "pop_change_2001_2006_pct",
    "pop_change_2006_2011_pct",
    "pop_change_2011_2016_pct",
    "pop_change_2016_2021_pct",
]

df["overall_growth"] = (
    (df["population_2021"] - df["population_1996"]) / df["population_1996"]
)

top_15 = df.nlargest(15, "overall_growth")[
    ["name"] + density_cols + pct_change_cols
].reset_index(drop=True)

density_domain = [
    float(np.nanmin(top_15[density_cols].to_numpy())),
    float(np.nanmax(top_15[density_cols].to_numpy())),
]

pct_min = float(np.nanmin(top_15[pct_change_cols].to_numpy()))
pct_max = float(np.nanmax(top_15[pct_change_cols].to_numpy()))
pct_change_range = max(abs(pct_min), abs(pct_max))
pct_change_domain = [-pct_change_range, pct_change_range]

density_display_cols = [
    "Density 1996",
    "Density 2001",
    "Density 2006",
    "Density 2011",
    "Density 2016",
    "Density 2021",
]

pct_change_display_cols = [
    "Change 1996-2001 (%)",
    "Change 2001-2006 (%)",
    "Change 2006-2011 (%)",
    "Change 2011-2016 (%)",
    "Change 2016-2021 (%)",
]

top_15.columns = (
    ["Town"]
    + density_display_cols
    + pct_change_display_cols
)

gt = (
    GT(top_15, rowname_col="Town")
    .fmt_number(columns=density_display_cols, decimals=1)
    .fmt_number(
        columns=pct_change_display_cols,
        decimals=1,
    )
    .data_color(
        columns=density_display_cols,
        palette="Blues",
        domain=density_domain,
        truncate=False,
        na_color="#808080",
    )
    .data_color(
        columns=pct_change_display_cols,
        palette="RdYlGn",
        domain=pct_change_domain,
        truncate=False,
        na_color="#808080",
    )
    .tab_header(
        title="Population Growth Trends in Ontario's Fastest-Growing Towns",
        subtitle="Density levels (people/km²) and percentage population change across census periods, 1996–2021",
    )
    .tab_stubhead(label="Town")
    .tab_options(
        table_font_size="11px",
        data_row_padding="8px",
        table_layout="fixed",
        container_width="95%",
        table_border_top_style="solid",
        table_border_top_width="1px",
        table_border_top_color="#E8E8E8",
        table_border_bottom_style="solid",
        table_border_bottom_width="1px",
        table_border_bottom_color="#E8E8E8",
        table_border_left_style="solid",
        table_border_left_width="1px",
        table_border_left_color="#E8E8E8",
        table_border_right_style="solid",
        table_border_right_width="1px",
        table_border_right_color="#E8E8E8",
        column_labels_background_color="#08306B",
        column_labels_font_weight="bold",
        column_labels_text_transform="none",
        row_group_background_color=None,
        summary_row_background_color=None,
        stub_background_color="#EAF0F6",
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
    .opt_row_striping()
    .tab_style(
        style=style.borders(sides="bottom", color="#CCCCCC", weight="2px"),
        locations=loc.column_labels(),
    )
)

gt = gt.tab_source_note(
    "Density and percent change calculated from 2021 Census population (top 15 fastest-growing towns by overall growth 1996–2021)."
)
gt = gt.tab_source_note("Data source: Statistics Canada Census data via towny.csv")

gt.gtsave("table.png")
