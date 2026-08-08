import pandas as pd
import numpy as np
from great_tables import GT, loc, style

# Step 1: Load and clean the data
df = pd.read_csv("towny.csv")

# Identify numeric columns for population and density
pop_cols = [col for col in df.columns if col.startswith("population_")]
density_cols = [col for col in df.columns if col.startswith("density_")]
pct_change_cols = [col for col in df.columns if col.startswith("pop_change_")]

# Calculate overall population growth from 1996 to 2021 as a ranking metric
df["overall_growth_pct"] = (df["population_2021"] - df["population_1996"]) / df["population_1996"]

# Get top 15 fastest-growing towns
top_15 = df.nlargest(15, "overall_growth_pct").copy()

# Organize columns for display
display_cols = ["name"] + pop_cols + density_cols + pct_change_cols
display_df = top_15[display_cols].reset_index(drop=True)

# Step 3: Identify Big Color measures
# The percentage change columns are signed measures (positive=good growth)
# These columns carry the growth story and qualify for diverging fill

# Step 2: Create the GT object with stub column
gt = GT(
    display_df,
    rowname_col="name",
)

# Add column labels with better formatting
labels = {
    "population_1996": "1996",
    "population_2001": "2001",
    "population_2006": "2006",
    "population_2011": "2011",
    "population_2016": "2016",
    "population_2021": "2021",
    "density_1996": "1996",
    "density_2001": "2001",
    "density_2006": "2006",
    "density_2011": "2011",
    "density_2016": "2016",
    "density_2021": "2021",
    "pop_change_1996_2001_pct": "1996–2001",
    "pop_change_2001_2006_pct": "2001–2006",
    "pop_change_2006_2011_pct": "2006–2011",
    "pop_change_2011_2016_pct": "2011–2016",
    "pop_change_2016_2021_pct": "2016–2021",
}

gt = gt.cols_label(**labels)

# Add spanners for grouping
gt = (
    gt
    .tab_spanner(label="Population", columns=pop_cols)
    .tab_spanner(label="Density (persons/km²)", columns=density_cols)
    .tab_spanner(label="Population Growth (%)", columns=pct_change_cols)
)

# Format population columns as integers
gt = gt.fmt_integer(columns=pop_cols, use_seps=True)

# Format density columns as numbers with 1 decimal
gt = gt.fmt_number(columns=density_cols, decimals=1, use_seps=False)

# Format percentage change columns with 1 decimal and force sign
gt = gt.fmt_percent(
    columns=pct_change_cols,
    decimals=1,
    scale_values=False,
    force_sign=True
)

# Step 3: BIG COLOR — Apply diverging fill to percentage change columns
# Percentage changes are signed measures where positive=good (growth is favorable)
# Use RdYlGn with positive=good (no reverse)
cols_for_color = pct_change_cols
lo = float(np.nanmin(display_df[cols_for_color].to_numpy()))
hi = float(np.nanmax(display_df[cols_for_color].to_numpy()))
M = max(abs(lo), abs(hi))

gt = gt.data_color(
    columns=cols_for_color,
    palette="RdYlGn",
    reverse=False,
    domain=[-M, M],
    truncate=False,
    na_color="#808080",
)

# Step 4: HEADING BAND — Light washed tint (Navy theme)
gt = gt.tab_header(
    title="Top 15 Fastest-Growing Ontario Towns",
    subtitle="Population growth from 1996 to 2021, with density and period-over-period growth rates"
)

# Step 5: SMALL COLOR POLISH
# Apply row striping with proper styling
gt = gt.opt_row_striping()

# Add caption/source note
gt = gt.tab_source_note(
    "Ontario municipalities ranked by overall population growth (1996–2021). "
    "Density calculated as population ÷ land area (km²). "
    "Growth rates shown as percentages between consecutive census periods."
)

# Render the table
gt.gtsave("table.png")
print("Table successfully saved as table.png")
