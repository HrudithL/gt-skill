import pandas as pd
import numpy as np
from great_tables import GT, md, html
from great_tables.data import gtcars

df = pd.read_csv("towny.csv")

# Calculate overall growth rate from 1996 to 2021
df["overall_growth_pct"] = ((df["population_2021"] - df["population_1996"]) / df["population_1996"] * 100).round(2)

# Get top 15 fastest-growing towns
top_15 = df.nlargest(15, "overall_growth_pct")

# Create summary table with density changes
summary = top_15[[
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
    "overall_growth_pct"
]].copy()

# Reset index for cleaner display
summary = summary.reset_index(drop=True)

# Create the GT table
gt = (
    GT(summary)
    .tab_header(
        title=md("**Top 15 Fastest-Growing Ontario Towns**"),
        subtitle=md("Population Growth & Density Changes (1996-2021)")
    )
    .cols_label(
        name="Town",
        population_1996="Pop 1996",
        population_2001="Pop 2001",
        population_2006="Pop 2006",
        population_2011="Pop 2011",
        population_2016="Pop 2016",
        population_2021="Pop 2021",
        density_1996="Dens 1996",
        density_2001="Dens 2001",
        density_2006="Dens 2006",
        density_2011="Dens 2011",
        density_2016="Dens 2016",
        density_2021="Dens 2021",
        pop_change_1996_2001_pct="Change 1996-01 %",
        pop_change_2001_2006_pct="Change 2001-06 %",
        pop_change_2006_2011_pct="Change 2006-11 %",
        pop_change_2011_2016_pct="Change 2011-16 %",
        pop_change_2016_2021_pct="Change 2016-21 %",
        overall_growth_pct="Total Growth %"
    )
    .fmt_integer(
        columns=[
            "population_1996", "population_2001", "population_2006",
            "population_2011", "population_2016", "population_2021"
        ]
    )
    .fmt_number(
        columns=[
            "density_1996", "density_2001", "density_2006",
            "density_2011", "density_2016", "density_2021"
        ],
        decimals=2
    )
    .fmt_percent(
        columns=[
            "pop_change_1996_2001_pct", "pop_change_2001_2006_pct",
            "pop_change_2006_2011_pct", "pop_change_2011_2016_pct",
            "pop_change_2016_2021_pct", "overall_growth_pct"
        ],
        decimals=1
    )
    .tab_options(
        table_font_size="11pt",
        heading_title_font_size="14pt"
    )
)

gt.gtsave("table.png")
