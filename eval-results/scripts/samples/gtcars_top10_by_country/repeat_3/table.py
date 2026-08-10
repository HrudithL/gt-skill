import pandas as pd
from great_tables import GT, style, loc
from gt_consistency import frame, finalize, PALETTE

# Step 1: Load and clean the data
df = pd.read_csv("gtcars.csv")

# Select top 10 most expensive cars overall, then group by country
top_10 = df.nlargest(10, "msrp")[["mfr", "model", "ctry_origin", "drivetrain", "trsmn", "msrp"]]

# Sort by country for grouping, then by MSRP descending within country
top_10_sorted = top_10.sort_values(["ctry_origin", "msrp"], ascending=[True, False]).reset_index(drop=True)

# Rename columns for display
top_10_sorted = top_10_sorted.rename(columns={
    "mfr": "Manufacturer",
    "model": "Model",
    "ctry_origin": "Country",
    "drivetrain": "Drivetrain",
    "trsmn": "Transmission",
    "msrp": "Price"
})

# Step 2: Organize columns and create GT table
gt = (
    GT(top_10_sorted, rowname_col="Manufacturer", groupname_col="Country")
    .cols_hide(columns=["Country"])
    # Step 5: Format columns
    .fmt_currency(columns="Price", currency="USD", decimals=0)
    # Add title and subtitle (Step 6)
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle="Grouped by Country of Origin"
    )
    # Add footer notes (Step 6)
    .tab_source_note(source_note="Prices shown are manufacturer suggested retail prices (MSRP).")
    .tab_source_note(source_note="Source: gtcars.csv")
    # Step 4: Heading band (dark band since no Big Color)
    .tab_options(
        column_labels_background_color=PALETTE["solid"]["navy"],
        column_labels_border_bottom_color=PALETTE["neutral"]["column_label_rule"],
        column_labels_border_bottom_width="2px",
    )
    # Small Color polish (Step 5)
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color=PALETTE["neutral"]["hairline"],
        table_body_hlines_width="1px",
    )
    .opt_row_striping()
    .tab_style(
        style=style.fill(color=PALETTE["neutral"]["label_band"]),
        locations=loc.stub(),
    )
)

# Apply frame and finalize
gt = frame(gt)
finalize(gt)
