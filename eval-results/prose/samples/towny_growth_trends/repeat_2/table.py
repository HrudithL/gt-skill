import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc

df = pd.read_csv("towny.csv")

overall_growth = (df["population_2021"] - df["population_1996"]) / df["population_1996"]
df["overall_growth"] = overall_growth

top_15 = df.nlargest(15, "overall_growth")[
    [
        "name",
        "population_1996",
        "population_2001",
        "population_2006",
        "population_2011",
        "population_2016",
        "population_2021",
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
].reset_index(drop=True)

density_cols = [
    "density_1996",
    "density_2001",
    "density_2006",
    "density_2011",
    "density_2016",
    "density_2021",
]
pct_cols = [
    "pop_change_1996_2001_pct",
    "pop_change_2001_2006_pct",
    "pop_change_2006_2011_pct",
    "pop_change_2011_2016_pct",
    "pop_change_2016_2021_pct",
]

density_lo = float(np.nanmin(top_15[density_cols].to_numpy()))
density_hi = float(np.nanmax(top_15[density_cols].to_numpy()))

pct_lo = float(np.nanmin(top_15[pct_cols].to_numpy()))
pct_hi = float(np.nanmax(top_15[pct_cols].to_numpy()))
pct_domain = [-max(abs(pct_lo), abs(pct_hi)), max(abs(pct_lo), abs(pct_hi))]

gt = (
    GT(top_15, rowname_col="name")
    .cols_hide(columns=["population_1996", "population_2001", "population_2006", "population_2011", "population_2016", "population_2021"])
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
    .tab_spanner(
        label="Density (pop/km²)",
        columns=density_cols,
    )
    .tab_spanner(
        label="Population % Change",
        columns=pct_cols,
    )
    .fmt_number(columns=density_cols, decimals=1, use_seps=True)
    .fmt_percent(columns=pct_cols, decimals=1, force_sign=True)
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
        domain=pct_domain,
        truncate=False,
        na_color="#808080",
    )
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
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.body(columns="density_2021"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.column_labels(columns="density_2021"),
    )
    .opt_row_striping()
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    .cols_width(cases={
        "name": "200px",
        "density_1996": "95px",
        "density_2001": "95px",
        "density_2006": "95px",
        "density_2011": "95px",
        "density_2016": "95px",
        "density_2021": "95px",
        "pop_change_1996_2001_pct": "110px",
        "pop_change_2001_2006_pct": "110px",
        "pop_change_2006_2011_pct": "110px",
        "pop_change_2011_2016_pct": "110px",
        "pop_change_2016_2021_pct": "110px",
    })
    .tab_header(
        title="Ontario Towns with Fastest Population Growth (1996–2021)",
        subtitle="Density changes and census period growth rates for the top 15 fastest-growing towns",
    )
    .tab_source_note(
        source_note="Fastest-growing means highest percent change over the full 1996–2021 span. Density is population per square kilometre."
    )
    .tab_source_note(
        source_note="Source: Statistics Canada Census subdivisions, 1996–2021."
    )
)

gt.gtsave("table.png", expand=15)
