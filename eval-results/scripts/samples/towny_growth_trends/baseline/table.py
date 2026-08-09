import pandas as pd
from great_tables import GT, loc, md
import polars as pl

df = pd.read_csv("towny.csv")

df["overall_growth_pct"] = ((df["population_2021"] - df["population_1996"]) / df["population_1996"]) * 100

top_15_fastest = df.nlargest(15, "overall_growth_pct")

display_df = top_15_fastest[[
    "name",
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
]].copy()

display_df.columns = [
    "Town",
    "Density 1996",
    "Density 2001",
    "Density 2006",
    "Density 2011",
    "Density 2016",
    "Density 2021",
    "Change 1996-2001 %",
    "Change 2001-2006 %",
    "Change 2006-2011 %",
    "Change 2011-2016 %",
    "Change 2016-2021 %",
]

display_df = display_df.reset_index(drop=True)

gt = (
    GT(display_df)
    .tab_header(
        title="Population Growth Trends: Top 15 Fastest-Growing Ontario Towns",
        subtitle="Population Density Changes (persons/km²) and Percentage Changes Across Census Years (1996-2021)"
    )
    .fmt_number(
        columns=["Density 1996", "Density 2001", "Density 2006", "Density 2011", "Density 2016", "Density 2021"],
        decimals=2
    )
    .fmt_percent(
        columns=["Change 1996-2001 %", "Change 2001-2006 %", "Change 2006-2011 %", "Change 2011-2016 %", "Change 2016-2021 %"],
        decimals=2
    )
    .tab_spanner(
        label="Population Density (persons/km²)",
        columns=["Density 1996", "Density 2001", "Density 2006", "Density 2011", "Density 2016", "Density 2021"]
    )
    .tab_spanner(
        label="Population % Change Between Periods",
        columns=["Change 1996-2001 %", "Change 2001-2006 %", "Change 2006-2011 %", "Change 2011-2016 %", "Change 2016-2021 %"]
    )
    .opt_stylize(style=2, color="blue")
)

gt.gtsave("table.png")
