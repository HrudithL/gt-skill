import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc

df = pd.read_csv("./towny.csv")

growth_col = "pop_change_2016_2021_pct"
df_sorted = df[df[growth_col].notna()].copy()
df_sorted = df_sorted.sort_values(growth_col, ascending=False).head(15).reset_index(drop=True)

display_cols = [
    "name",
    "density_1996", "density_2001", "density_2006", "density_2011", "density_2016", "density_2021",
    "pop_change_1996_2001_pct", "pop_change_2001_2006_pct", "pop_change_2006_2011_pct",
    "pop_change_2011_2016_pct", "pop_change_2016_2021_pct",
]
df_display = df_sorted[display_cols].copy()

density_cols = ["density_1996", "density_2001", "density_2006", "density_2011", "density_2016", "density_2021"]
change_cols = ["pop_change_1996_2001_pct", "pop_change_2001_2006_pct", "pop_change_2006_2011_pct",
               "pop_change_2011_2016_pct", "pop_change_2016_2021_pct"]

for col in density_cols + change_cols:
    df_display[col] = pd.to_numeric(df_display[col], errors="coerce")

lo_change = float(np.nanmin(df_display[change_cols].to_numpy()))
hi_change = float(np.nanmax(df_display[change_cols].to_numpy()))

gt = (
    GT(df_display, rowname_col="name")
    .tab_header(
        title="Top 15 Fastest-Growing Ontario Towns",
        subtitle="Population density trends and growth rates across census years (1996–2021)",
    )
    .cols_label(
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
    .tab_spanner(label="Population Change (%)", columns=change_cols)
    .fmt_number(columns=density_cols, decimals=1, use_seps=True)
    .fmt_percent(columns=change_cols, decimals=1, scale_values=False)
    .data_color(
        columns=change_cols,
        palette="Blues",
        domain=[lo_change, hi_change],
        truncate=False,
        na_color="#808080",
    )
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
        row_striping_background_color="#F6F6F6",
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
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.body(columns="density_2021"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.column_labels(columns="density_2021"),
    )
    .tab_source_note(
        md("**Source:** Towny dataset (census years 1996–2021). Density = population ÷ land area (km²). "
           "Population change is the percentage change from the start of each period."),
    )
)

gt.gtsave("table.png", expand=15)
