import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc
from gt_consistency import frame, finalize, heatmap, band, stripe, stub_tint, PALETTE

df = pd.read_csv("towny.csv")

# Calculate total percentage change from 1996 to 2021
df["total_pct_change"] = (df["population_2021"] - df["population_1996"]) / df["population_1996"]

# Get top 15 fastest-growing towns by total growth percentage
top_15 = df.nlargest(15, "total_pct_change")[["name", "population_1996", "population_2001",
                                               "population_2006", "population_2011", "population_2016",
                                               "population_2021", "density_1996", "density_2001",
                                               "density_2006", "density_2011", "density_2016",
                                               "density_2021", "pop_change_1996_2001_pct",
                                               "pop_change_2001_2006_pct", "pop_change_2006_2011_pct",
                                               "pop_change_2011_2016_pct", "pop_change_2016_2021_pct"]].copy()

# Reorder columns to group census years
top_15 = top_15[["name",
                 "population_1996", "density_1996",
                 "population_2001", "density_2001",
                 "population_2006", "density_2006",
                 "population_2011", "density_2011",
                 "population_2016", "density_2016",
                 "population_2021", "density_2021",
                 "pop_change_1996_2001_pct", "pop_change_2001_2006_pct",
                 "pop_change_2006_2011_pct", "pop_change_2011_2016_pct",
                 "pop_change_2016_2021_pct"]]

# Reset index for cleaner display
top_15 = top_15.reset_index(drop=True)

# Create the base table
gt = GT(top_15, rowname_col="name")

# Format population columns as integers
pop_cols = ["population_1996", "population_2001", "population_2006", "population_2011", "population_2016", "population_2021"]
gt = gt.fmt_number(columns=pop_cols, decimals=0)

# Format density columns with 1 decimal
density_cols = ["density_1996", "density_2001", "density_2006", "density_2011", "density_2016", "density_2021"]
gt = gt.fmt_number(columns=density_cols, decimals=1)

# Format percentage change columns as percentages
pct_change_cols = ["pop_change_1996_2001_pct", "pop_change_2001_2006_pct", "pop_change_2006_2011_pct",
                   "pop_change_2011_2016_pct", "pop_change_2016_2021_pct"]
gt = gt.fmt_percent(columns=pct_change_cols, decimals=1, scale_values=True)

# Add column labels with better names
gt = gt.cols_label(
    population_1996="Pop 1996",
    density_1996="Dens 1996",
    population_2001="Pop 2001",
    density_2001="Dens 2001",
    population_2006="Pop 2006",
    density_2006="Dens 2006",
    population_2011="Pop 2011",
    density_2011="Dens 2011",
    population_2016="Pop 2016",
    density_2016="Dens 2016",
    population_2021="Pop 2021",
    density_2021="Dens 2021",
    pop_change_1996_2001_pct="1996-2001",
    pop_change_2001_2006_pct="2001-2006",
    pop_change_2006_2011_pct="2006-2011",
    pop_change_2011_2016_pct="2011-2016",
    pop_change_2016_2021_pct="2016-2021"
)

# Create column groups for better organization
gt = gt.tab_spanner(label="1996", columns=["population_1996", "density_1996"])
gt = gt.tab_spanner(label="2001", columns=["population_2001", "density_2001"])
gt = gt.tab_spanner(label="2006", columns=["population_2006", "density_2006"])
gt = gt.tab_spanner(label="2011", columns=["population_2011", "density_2011"])
gt = gt.tab_spanner(label="2016", columns=["population_2016", "density_2016"])
gt = gt.tab_spanner(label="2021", columns=["population_2021", "density_2021"])
gt = gt.tab_spanner(label="% Change Between Periods", columns=pct_change_cols)

# Add vertical dividers at spanner boundaries
gt = gt.tab_style(
    style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
    locations=loc.body(columns=["density_1996", "density_2001", "density_2006", "density_2011", "density_2016", "density_2021"]),
)
gt = gt.tab_style(
    style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
    locations=loc.column_labels(columns=["density_1996", "density_2001", "density_2006", "density_2011", "density_2016", "density_2021"]),
)

# Apply data_color to percentage changes for the hero measure
gt = heatmap(
    gt,
    columns=pct_change_cols,
    kind="sequential",
    hue="positive"
)

# Apply hairlines and column label border
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
    column_labels_border_bottom_color="#CCCCCC",
    column_labels_border_bottom_width="2px"
)

# Apply band and finalize
gt = band(gt, shade="light", hue="forest")
gt = stripe(gt)
gt = stub_tint(gt, hue="forest")

# Add titles and annotations
gt = gt.tab_header(
    title="Ontario's Fastest-Growing Towns: Population & Density Trends (1996-2021)",
    subtitle="Top 15 by growth percentage, with density changes across census years"
)

# Add footer notes
gt = gt.tab_source_note(source_note="Population and density changes measured across census periods from 1996 to 2021.")
gt = gt.tab_source_note(source_note="Data source: towny.csv (Ontario census data)")

# Apply frame and finalize styling
gt = frame(gt)
finalize(gt, "table.png", expand=15, zoom=2.0)
