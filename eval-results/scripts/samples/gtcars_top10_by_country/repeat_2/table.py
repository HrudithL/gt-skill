import pandas as pd
import numpy as np
from great_tables import GT, style, loc
from gt_consistency import band, frame, finalize, heatmap, stripe, stub_tint, PALETTE

# Step 1: Load and clean data
df = pd.read_csv("gtcars.csv")

# Select top 10 by MSRP and group by country
df_top = df.nlargest(10, "msrp").sort_values(["ctry_origin", "msrp"], ascending=[True, False])

# Create display columns
df_display = df_top[[
    "ctry_origin",
    "mfr",
    "model",
    "year",
    "drivetrain",
    "trsmn",
    "msrp"
]].copy()

df_display.columns = [
    "Country",
    "Manufacturer",
    "Model",
    "Year",
    "Drivetrain",
    "Transmission",
    "Price"
]

# Ensure MSRP is numeric
df_display["Price"] = pd.to_numeric(df_display["Price"], errors="coerce")

# Step 2: Create GT with grouping and stub
gt = GT(df_display, rowname_col="Manufacturer", groupname_col="Country")

# Step 3: Color MSRP (numeric magnitude = Blues)
# Domain: min to max across the Price column
lo = float(np.nanmin(df_display["Price"].to_numpy()))
hi = float(np.nanmax(df_display["Price"].to_numpy()))

gt = heatmap(gt, "Price", kind="sequential", hue="neutral", domain=[lo, hi])

# Step 5: Format Price as currency
gt = gt.fmt_currency(columns="Price", currency="USD", decimals=0)

# Apply small-color polish
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

# Add hairlines
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
    column_labels_border_bottom_color="#CCCCCC",
    column_labels_border_bottom_width="2px",
)

# Row group styling
gt = gt.tab_options(
    row_group_background_color="#EAF0F6",
    row_group_font_weight="bold",
    row_group_border_top_color="#BDBDBD",
    row_group_border_bottom_color="#BDBDBD",
    row_group_padding="6px",
)

# Step 4: Light heading band (Big Color present)
gt = band(gt, shade="light", hue="navy")

# Step 6: Add title and annotations
gt = gt.tab_header(
    title="Top 10 Most Expensive GT Cars by Country",
    subtitle="Grouped by country of origin with drivetrain and transmission details"
)

gt = (
    gt.tab_source_note(
        source_note="Price is the manufacturer's suggested retail price (MSRP) in USD."
    )
    .tab_source_note(
        source_note="Source: GT cars dataset, 2014-2017 model years."
    )
)

# Step 7: Frame and render
gt = frame(gt)
finalize(gt, "table.png")
