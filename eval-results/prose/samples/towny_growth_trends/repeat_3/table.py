import pandas as pd
import numpy as np
from great_tables import GT, loc, style

# STEP 1: UNDERSTAND & CLEAN DATA
df = pd.read_csv("towny.csv")

# Identify the fastest-growing towns based on overall population change 1996-2021
df["overall_pct_change"] = (df["population_2021"] - df["population_1996"]) / df["population_1996"]

# Get top 15 fastest-growing towns
top_15 = df.nlargest(15, "overall_pct_change")[["name", "population_1996", "density_1996",
                                                   "population_2001", "density_2001",
                                                   "population_2006", "density_2006",
                                                   "population_2011", "density_2011",
                                                   "population_2016", "density_2016",
                                                   "population_2021", "density_2021",
                                                   "pop_change_1996_2001_pct",
                                                   "pop_change_2001_2006_pct",
                                                   "pop_change_2006_2011_pct",
                                                   "pop_change_2011_2016_pct",
                                                   "pop_change_2016_2021_pct"]].copy()

# Reorganize for display: town name | density measurements across years | pct changes between periods
display_df = top_15[["name"]].copy()

# Add density columns for each census year
display_df["Density 1996"] = top_15["density_1996"].round(2)
display_df["Density 2001"] = top_15["density_2001"].round(2)
display_df["Density 2006"] = top_15["density_2006"].round(2)
display_df["Density 2011"] = top_15["density_2011"].round(2)
display_df["Density 2016"] = top_15["density_2016"].round(2)
display_df["Density 2021"] = top_15["density_2021"].round(2)

# Add percentage change columns between periods
display_df["Change 1996-2001 %"] = (top_15["pop_change_1996_2001_pct"] * 100).round(1)
display_df["Change 2001-2006 %"] = (top_15["pop_change_2001_2006_pct"] * 100).round(1)
display_df["Change 2006-2011 %"] = (top_15["pop_change_2006_2011_pct"] * 100).round(1)
display_df["Change 2011-2016 %"] = (top_15["pop_change_2011_2016_pct"] * 100).round(1)
display_df["Change 2016-2021 %"] = (top_15["pop_change_2016_2021_pct"] * 100).round(1)

display_df.reset_index(drop=True, inplace=True)

# STEP 2: ORGANIZE COLUMNS
# Stub is 'name', hero measures are the density columns (left edge after stub) and pct changes
# Columns are already well-organized: town name, then densities by year, then pct changes

# STEP 3: BIG COLOR
# Two distinct measures: density (ordered magnitude) and percent change (ordered magnitude)
# Both qualify and both are distinct dimensions of growth
# Density: population per unit area (sequential, more = denser)
# Percent change: growth rate (sequential)

# STEP 4: HEADING BAND - unconditional navy band
# Set in tab_header call below

# STEP 5 & 6: BUILD TABLE WITH FORMATTING
gt = (GT(display_df, rowname_col="name")
      .tab_header(
          title="Population Growth Trends in Ontario's Fastest-Growing Towns",
          subtitle="Density changes across census years (1996-2021) with inter-period growth rates"
      )
      .cols_label(
          **{
              "Density 1996": "1996",
              "Density 2001": "2001",
              "Density 2006": "2006",
              "Density 2011": "2011",
              "Density 2016": "2016",
              "Density 2021": "2021",
              "Change 1996-2001 %": "1996-2001",
              "Change 2001-2006 %": "2001-2006",
              "Change 2006-2011 %": "2006-2011",
              "Change 2011-2016 %": "2011-2016",
              "Change 2016-2021 %": "2016-2021",
          }
      )
      .tab_stubhead(label="Town")
)

# Format density columns as numbers with 1 decimal
for col in ["Density 1996", "Density 2001", "Density 2006", "Density 2011", "Density 2016", "Density 2021"]:
    gt = gt.fmt_number(columns=col, decimals=1)

# Format percent change columns
for col in ["Change 1996-2001 %", "Change 2001-2006 %", "Change 2006-2011 %", "Change 2011-2016 %", "Change 2016-2021 %"]:
    gt = gt.fmt_number(columns=col, decimals=1)

# STEP 3 (continued): Apply color to density columns (gradient fill for ordered magnitude)
# Using sequential palette for density (higher = denser towns)
density_cols = ["Density 1996", "Density 2001", "Density 2006", "Density 2011", "Density 2016", "Density 2021"]
density_values = display_df[density_cols].values.flatten()
density_min = np.nanmin(density_values)
density_max = np.nanmax(density_values)

gt = gt.data_color(
    columns=density_cols,
    domain=[density_min, density_max],
    palette="Greens"
)

# Apply color to percent change columns (sequential palette)
pct_cols = ["Change 1996-2001 %", "Change 2001-2006 %", "Change 2006-2011 %", "Change 2011-2016 %", "Change 2016-2021 %"]
pct_values = display_df[pct_cols].values.flatten()
pct_min = np.nanmin(pct_values)
pct_max = np.nanmax(pct_values)

gt = gt.data_color(
    columns=pct_cols,
    domain=[pct_min, pct_max],
    palette="Blues"
)

# STEP 5: SMALL COLOR POLISH
# Heading band, row striping, stub tint
gt = gt.tab_options(
    column_labels_background_color="#08306B",
    column_labels_font_weight="bold",
    column_labels_border_bottom_color="#CCCCCC",
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    row_striping_background_color="#F6F6F6"
)

# Row striping (since not all body columns are fully colored)
gt = gt.opt_row_striping()

# Column widths for compact layout
gt = gt.cols_width(
    cases={
        "name": "180px",
        "Density 1996": "100px",
        "Density 2001": "100px",
        "Density 2006": "100px",
        "Density 2011": "100px",
        "Density 2016": "100px",
        "Density 2021": "100px",
        "Change 1996-2001 %": "110px",
        "Change 2001-2006 %": "110px",
        "Change 2006-2011 %": "110px",
        "Change 2011-2016 %": "110px",
        "Change 2016-2021 %": "110px",
    }
)

# Apply stub tint
gt = gt.tab_style(
    style=style.fill(color="#EAF0F6"),
    locations=loc.body(columns="name")
)

# STEP 6: TITLES & ANNOTATIONS
gt = gt.tab_source_note(
    "Density measured in persons per square kilometer. Top 15 towns selected by overall population growth 1996–2021."
)
gt = gt.tab_source_note(
    "Source: towny.csv (Ontario municipal census data)"
)

# STEP 7: RENDER & VERIFY
gt.gtsave("table.png", zoom=1.5, expand=15)
print("Table rendered successfully to table.png")
