import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: UNDERSTAND & CLEAN DATA
df = pd.read_csv("gtcars.csv")

# Get top 10 by msrp (price)
df_top = df.nlargest(10, "msrp").copy()

# Create composite stub label for readability
df_top["vehicle"] = df_top["mfr"] + " " + df_top["model"]

# Select and organize columns
cols = ["vehicle", "ctry_origin", "drivetrain", "trsmn", "msrp"]
df_display = df_top[cols].copy()
df_display.columns = ["Vehicle", "Country", "Drivetrain", "Transmission", "MSRP"]

# Clean transmission codes to readable format
transmission_map = {
    "6m": "6-speed Manual",
    "6a": "6-speed Auto",
    "7a": "7-speed Auto",
    "7m": "7-speed Manual",
    "8a": "8-speed Auto",
    "8am": "8-speed Auto/Manual",
    "9a": "9-speed Auto",
    "1dd": "Dual Motor"
}
df_display["Transmission"] = df_display["Transmission"].map(transmission_map)

# Clean drivetrain to readable format
drivetrain_map = {
    "rwd": "RWD",
    "awd": "AWD",
    "fwd": "FWD"
}
df_display["Drivetrain"] = df_display["Drivetrain"].map(drivetrain_map)

# Sort by Country then by MSRP (descending) for grouped display
df_display = df_display.sort_values(["Country", "MSRP"], ascending=[True, False])

# Step 2: ORGANIZE COLUMNS
# Stub: Vehicle (already created)
# Group: Country
# Measures: Drivetrain, Transmission, MSRP

# Step 3: BIG COLOR - which measure(s) earn fill
# MSRP qualifies (ordered numeric, 10 rows >= 5)
# Drivetrain and Transmission are categorical, not measures
# Color MSRP only (it's the focal measure - price range shows the "expensiveness")

# Compute domain for MSRP
cols_msrp = ["MSRP"]
lo = float(np.nanmin(df_display[cols_msrp].to_numpy()))
hi = float(np.nanmax(df_display[cols_msrp].to_numpy()))

# Step 4: BUILD TABLE WITH HEADING BAND
gt = (
    GT(df_display, rowname_col="Vehicle", groupname_col="Country")
    # Step 5: SMALL COLOR POLISH
    # (a) Cell borders - hairlines on all body rows
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Row-group emphasis: bold weight + structural rule
    # (c) Row striping (not all body is colored, so apply by default)
    .tab_options(
        row_group_font_weight="bold",
        row_group_border_top_color="#BDBDBD",
        row_group_border_bottom_color="#BDBDBD",
        row_group_padding="6px",
        row_striping_background_color="#F6F6F6",
    )
    .opt_row_striping()
    # (d) Stub tint
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # (e) Formatting per column
    .fmt_currency(columns="MSRP", currency="USD", decimals=0)
    .sub_missing(columns=["Drivetrain", "Transmission", "MSRP"], missing_text="—")
    # Step 4: Heading band (branding) - dark navy band with white text
    .tab_options(
        heading_background_color="#08306B",
        column_labels_background_color="#08306B",
        column_labels_font_weight="bold",
    )
    .tab_style(
        style=style.text(color="white"),
        locations=loc.column_labels(),
    )
    .tab_style(
        style=style.text(color="white"),
        locations=loc.header(),
    )
    # Step 3: BIG COLOR - gradient fill on MSRP
    .data_color(
        columns="MSRP",
        palette="Blues",
        domain=[lo, hi],
        truncate=False,
        na_color="#808080",
    )
    # Step 6: TITLES & ANNOTATIONS
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle="Grouped by Country of Origin"
    )
    .tab_source_note(
        source_note="Prices (MSRP) shown in USD; color intensity indicates relative cost within the top 10."
    )
    .tab_source_note(
        source_note="Source: gtcars.csv"
    )
)

# Step 7: RENDER & VERIFY
gt.gtsave("table.png")
