import pandas as pd
import numpy as np
from great_tables import GT, style, loc
from gt_consistency import frame, band, finalize, stripe, stub_tint, PALETTE

# Load data
df = pd.read_csv("towny.csv")

# Calculate overall growth 1996-2021 as percentage change
df["overall_growth"] = (df["population_2021"] - df["population_1996"]) / df["population_1996"]

# Get top 15 fastest-growing towns by overall population growth
top_15 = df.nlargest(15, "overall_growth")[["name", "density_1996", "density_2001", "density_2006",
                                             "density_2011", "density_2016", "density_2021",
                                             "pop_change_1996_2001_pct", "pop_change_2001_2006_pct",
                                             "pop_change_2006_2011_pct", "pop_change_2011_2016_pct",
                                             "pop_change_2016_2021_pct"]].reset_index(drop=True)

# Rename columns for display
top_15 = top_15.rename(columns={
    "name": "Town",
    "density_1996": "1996",
    "density_2001": "2001",
    "density_2006": "2006",
    "density_2011": "2011",
    "density_2016": "2016",
    "density_2021": "2021",
    "pop_change_1996_2001_pct": "1996-2001",
    "pop_change_2001_2006_pct": "2001-2006",
    "pop_change_2006_2011_pct": "2006-2011",
    "pop_change_2011_2016_pct": "2011-2016",
    "pop_change_2016_2021_pct": "2016-2021"
})

# Ensure percentage columns are in decimal form (they already are)
# The data is already in decimal form (0.15 = 15%)

# Calculate domain for density gradient (Step 3)
density_cols = ["1996", "2001", "2006", "2011", "2016", "2021"]
density_lo = float(np.nanmin(top_15[density_cols].to_numpy()))
density_hi = float(np.nanmax(top_15[density_cols].to_numpy()))

# Calculate domain for percentage change columns
pct_cols = ["1996-2001", "2001-2006", "2006-2011", "2011-2016", "2016-2021"]
pct_lo = float(np.nanmin(top_15[pct_cols].to_numpy()))
pct_hi = float(np.nanmax(top_15[pct_cols].to_numpy()))

# Build the table with Step 3 color, Step 4 band, Step 5 polish, Step 6 titles
gt = (
    GT(top_15, rowname_col="Town")
    # Step 2: Column spanners
    .tab_spanner(label="Population Density (per km²)", columns=density_cols)
    .tab_spanner(label="% Population Change", columns=pct_cols)
    # Step 3: Big Color - density gradient (ordered magnitude)
    .data_color(
        columns=density_cols,
        palette="Blues",
        domain=[density_lo, density_hi],
        truncate=False,
        na_color=PALETTE["neutral"]["na_cell"],
    )
    # Step 3: Big Color - percentage change gradient (growth measures)
    .data_color(
        columns=pct_cols,
        palette="Greens",
        domain=[pct_lo, pct_hi],
        truncate=False,
        na_color=PALETTE["neutral"]["na_cell"],
    )
    # Step 5: Cell borders
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color=PALETTE["neutral"]["hairline"],
        table_body_hlines_width="1px",
    )
    # Step 5: Column group dividers
    .tab_style(
        style=style.borders(sides="right", color=PALETTE["neutral"]["vertical_divider"], weight="1px"),
        locations=loc.body(columns="2021"),
    )
    .tab_style(
        style=style.borders(sides="right", color=PALETTE["neutral"]["vertical_divider"], weight="1px"),
        locations=loc.column_labels(columns="2021"),
    )
    # Step 5: Format columns
    .fmt_number(columns=density_cols, decimals=1, use_seps=True)
    .fmt_percent(columns=pct_cols, decimals=1)
    # Step 6: Titles and footer
    .tab_header(
        title="Top 15 Fastest-Growing Ontario Towns",
        subtitle="Population Density Changes (1996–2021) and Inter-Census Period Growth Rates"
    )
    .tab_source_note(source_note="Fastest-growing means highest overall population growth from 1996 to 2021.")
    .tab_source_note(source_note="Source: Statistics Canada Census subdivisions, 1996–2021.")
)

# Step 4: Apply the heading band (light shade with navy hue since Big Color is present)
gt = band(gt, shade="light", hue="navy")

# Step 5: Row striping and stub tint (conditional)
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

# Step 7: Frame and finalize
gt = frame(gt)
gt = finalize(gt, vwidth=1200, vheight=800)
