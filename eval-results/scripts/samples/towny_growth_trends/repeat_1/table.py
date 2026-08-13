import pandas as pd
import numpy as np
from great_tables import GT, md, html, style, loc
from gt_consistency import PALETTE, frame, finalize, heatmap, band, stripe, stub_tint, hairlines

# Step 1: Load and clean the data
df = pd.read_csv("./towny.csv")

# Calculate overall growth rate from 1996 to 2021
df["overall_growth_pct"] = ((df["population_2021"] - df["population_1996"]) / df["population_1996"]) * 100

# Find top 15 fastest-growing towns
top_15 = df.nlargest(15, "overall_growth_pct")[
    ["name", "population_1996", "population_2001", "population_2006",
     "population_2011", "population_2016", "population_2021",
     "density_1996", "density_2001", "density_2006", "density_2011",
     "density_2016", "density_2021",
     "pop_change_1996_2001_pct", "pop_change_2001_2006_pct",
     "pop_change_2006_2011_pct", "pop_change_2011_2016_pct", "pop_change_2016_2021_pct"]
].reset_index(drop=True)

# Calculate density percentage changes
top_15["density_change_1996_2001_pct"] = ((top_15["density_2001"] - top_15["density_1996"]) / top_15["density_1996"]) * 100
top_15["density_change_2001_2006_pct"] = ((top_15["density_2006"] - top_15["density_2001"]) / top_15["density_2001"]) * 100
top_15["density_change_2006_2011_pct"] = ((top_15["density_2011"] - top_15["density_2006"]) / top_15["density_2006"]) * 100
top_15["density_change_2011_2016_pct"] = ((top_15["density_2016"] - top_15["density_2011"]) / top_15["density_2011"]) * 100
top_15["density_change_2016_2021_pct"] = ((top_15["density_2021"] - top_15["density_2016"]) / top_15["density_2016"]) * 100

# Create a cleaner display table
display_data = top_15[["name", "density_1996", "density_2001", "density_2006",
                        "density_2011", "density_2016", "density_2021",
                        "density_change_1996_2001_pct", "density_change_2001_2006_pct",
                        "density_change_2006_2011_pct", "density_change_2011_2016_pct",
                        "density_change_2016_2021_pct"]].copy()

# Rename columns for display
display_data.columns = ["Town",
                         "Density 1996", "Density 2001", "Density 2006",
                         "Density 2011", "Density 2016", "Density 2021",
                         "% Change 96-01", "% Change 01-06", "% Change 06-11",
                         "% Change 11-16", "% Change 16-21"]

# Create the GT table with rowname_col for stub
gt = (GT(display_data, rowname_col="Town")
      .fmt_number(
          columns=["Density 1996", "Density 2001", "Density 2006",
                   "Density 2011", "Density 2016", "Density 2021"],
          decimals=1
      )
      .fmt_percent(
          columns=["% Change 96-01", "% Change 01-06", "% Change 06-11",
                   "% Change 11-16", "% Change 16-21"],
          decimals=1,
          force_sign=True
      )
      .tab_header(
          title="Ontario's Fastest-Growing Towns: Population Density Trends",
          subtitle="Top 15 Towns by Overall Growth (1996-2021), Showing Density Changes Across Census Periods"
      )
      .tab_spanner(
          label="Population Density (persons/km²)",
          columns=["Density 1996", "Density 2001", "Density 2006",
                   "Density 2011", "Density 2016", "Density 2021"]
      )
      .tab_spanner(
          label="Density % Change Between Periods",
          columns=["% Change 96-01", "% Change 01-06", "% Change 06-11",
                   "% Change 11-16", "% Change 16-21"]
      )
      .tab_options(
          table_body_hlines_style="solid",
          table_body_hlines_color="#E8E8E8",
          table_body_hlines_width="1px",
          column_labels_border_bottom_color="#CCCCCC",
          column_labels_border_bottom_width="2px",
          row_striping_background_color="#F6F6F6"
      )
      .tab_style(
          style=style.text(color="white"),
          locations=loc.column_labels()
      )
      .tab_style(
          style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
          locations=loc.body(columns="Density 2021")
      )
      .tab_style(
          style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
          locations=loc.column_labels(columns="Density 2021")
      )
      .tab_style(
          style=style.fill(color="#EAF0F6"),
          locations=loc.stub()
      )
      .opt_row_striping()
      .cols_width(cases={
          "Town": "140px",
          "Density 1996": "110px",
          "Density 2001": "110px",
          "Density 2006": "110px",
          "Density 2011": "110px",
          "Density 2016": "110px",
          "Density 2021": "110px",
          "% Change 96-01": "100px",
          "% Change 01-06": "100px",
          "% Change 06-11": "100px",
          "% Change 11-16": "100px",
          "% Change 16-21": "100px"
      })
)

# Apply heatmap to density change columns using diverging palette
gt = heatmap(
    gt,
    columns=["% Change 96-01", "% Change 01-06", "% Change 06-11",
             "% Change 11-16", "% Change 16-21"],
    kind="diverging",
    hue="default"
)

# Apply branding band to header
gt = band(gt)

# Apply hairlines and frame
gt = hairlines(gt)
gt = frame(gt)

# Add footer notes
gt = (gt.tab_source_note(
          source_note=md("Fastest-growing towns identified by overall population growth rate from 1996 to 2021. Density changes show population concentration across 5-year census periods.")
      )
      .tab_source_note(
          source_note=md("**Source:** Statistics Canada Census Data, 1996-2021")
      )
)

# Apply padding
gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px"
)

# Finalize and render
finalize(gt, "table.png")
