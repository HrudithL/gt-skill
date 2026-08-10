import pandas as pd
from great_tables import GT, style, loc
from gt_consistency import frame, finalize, heatmap, band, stripe, stub_tint, PALETTE

# Step 1: Load and clean data
df = pd.read_csv("gtcars.csv")

# Create a display DataFrame with relevant columns
display_df = df[["mfr", "model", "hp", "msrp"]].copy()
display_df.columns = ["Manufacturer", "Model", "Horsepower", "Price"]

# Step 2: Organize columns
# Create a combined identifier column for the stub (manufacturer + model)
display_df["car"] = display_df["Manufacturer"] + " " + display_df["Model"]
display_df = display_df[["car", "Horsepower", "Price"]]
display_df.columns = ["Car", "Horsepower", "Price"]

# Step 3 & 5: Build table with Big Color (price colored with Blues) and light band
gt = (
    GT(display_df, rowname_col="Car")
    # Step 5e: Format columns
    .fmt_currency(columns="Price", decimals=0, use_seps=True)
    .fmt_number(columns="Horsepower", decimals=0, use_seps=True)
    # Step 5a: Cell borders
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Step 5e: Make Horsepower (secondary measure) bold since Price is colored
    .tab_style(
        style=style.text(weight="bold"),
        locations=loc.body(columns="Horsepower"),
    )
    # Step 5c: Row striping for ≥10 rows
)

gt = stripe(gt)

# Step 5d: Stub tint
gt = stub_tint(gt, hue="navy")

# Step 3: Apply color gradient to Price column (primary measure, neutral magnitude = Blues)
gt = heatmap(gt, columns="Price", kind="sequential", hue="neutral")

# Step 4: Apply light heading band (with Big Color present)
gt = band(gt, shade="light", hue="navy")

# Step 6: Add titles and annotations
gt = (
    gt
    .tab_header(
        title="GT Cars: Horsepower and Price",
        subtitle="A collection of high-performance vehicles"
    )
    .tab_source_note(source_note="Price shown in USD; Horsepower measured at engine RPM.")
    .tab_source_note(source_note="Source: gtcars dataset.")
)

# Step 7: Apply frame and finalize
gt = frame(gt)
finalize(gt)
