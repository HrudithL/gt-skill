import pandas as pd
import numpy as np
from great_tables import GT, html, style, loc

# Read and clean the data
df = pd.read_csv("towny.csv")

# Calculate overall growth rate from 1996 to 2021 to identify fastest-growing
df["overall_growth"] = (df["population_2021"] - df["population_1996"]) / df["population_1996"]

# Filter to top 15 fastest-growing towns
top_15 = df.nlargest(15, "overall_growth")[["name", "density_1996", "density_2001", "density_2006", "density_2011", "density_2016", "density_2021"]].reset_index(drop=True)

# Calculate percentage change in density between periods
top_15["density_change_96_01_pct"] = np.where(
    top_15["density_1996"] > 0,
    (top_15["density_2001"] - top_15["density_1996"]) / top_15["density_1996"],
    None
)
top_15["density_change_01_06_pct"] = np.where(
    top_15["density_2001"] > 0,
    (top_15["density_2006"] - top_15["density_2001"]) / top_15["density_2001"],
    None
)
top_15["density_change_06_11_pct"] = np.where(
    top_15["density_2006"] > 0,
    (top_15["density_2011"] - top_15["density_2006"]) / top_15["density_2006"],
    None
)
top_15["density_change_11_16_pct"] = np.where(
    top_15["density_2011"] > 0,
    (top_15["density_2016"] - top_15["density_2011"]) / top_15["density_2011"],
    None
)
top_15["density_change_16_21_pct"] = np.where(
    top_15["density_2021"] > 0,
    (top_15["density_2021"] - top_15["density_2016"]) / top_15["density_2016"],
    None
)

# Reorder columns: density values, then density changes
display_df = top_15[["name", "density_1996", "density_2001", "density_2006", "density_2011", "density_2016", "density_2021", "density_change_96_01_pct", "density_change_01_06_pct", "density_change_06_11_pct", "density_change_11_16_pct", "density_change_16_21_pct"]].copy()

# Compute domain for density gradient
density_cols = ["density_1996", "density_2001", "density_2006", "density_2011", "density_2016", "density_2021"]
density_lo = float(np.nanmin(display_df[density_cols].to_numpy()))
density_hi = float(np.nanmax(display_df[density_cols].to_numpy()))

# Build the table
gt = (
    GT(display_df, rowname_col="name")
    .tab_header(
        title="Ontario's Fastest-Growing Towns — Population Density Trends",
        subtitle="Density by census year (1996–2021) and period-over-period growth rates"
    )
    .tab_spanner(label="Population Density (people/km²)", columns=density_cols)
    .tab_spanner(label="Density Growth (%)", columns=["density_change_96_01_pct", "density_change_01_06_pct", "density_change_06_11_pct", "density_change_11_16_pct", "density_change_16_21_pct"])
    .cols_label(
        density_1996="1996",
        density_2001="2001",
        density_2006="2006",
        density_2011="2011",
        density_2016="2016",
        density_2021="2021",
        density_change_96_01_pct="1996–2001",
        density_change_01_06_pct="2001–2006",
        density_change_06_11_pct="2006–2011",
        density_change_11_16_pct="2011–2016",
        density_change_16_21_pct="2016–2021"
    )
    .fmt_number(columns=density_cols, decimals=1)
    .fmt_percent(columns=["density_change_96_01_pct", "density_change_01_06_pct", "density_change_06_11_pct", "density_change_11_16_pct", "density_change_16_21_pct"], decimals=1)
    .data_color(
        columns=density_cols,
        palette="Blues",
        domain=[density_lo, density_hi],
        truncate=False,
        na_color="#808080"
    )
    .tab_style(
        style=style.borders(
            sides="bottom",
            color="#E8E8E8",
            weight="1px"
        ),
        locations=loc.body()
    )
    .tab_style(
        style=style.borders(
            sides="bottom",
            color="#CCCCCC",
            weight="2px"
        ),
        locations=loc.column_labels()
    )
    .sub_missing(missing_text="—")
    .tab_source_note("Ranked by overall population growth 1996–2021. Density measured in persons per square kilometer.")
)

gt.gtsave("table.png")
