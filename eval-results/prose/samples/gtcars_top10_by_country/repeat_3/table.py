import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc

# Load and clean data
df = pd.read_csv("gtcars.csv")

# Sort by MSRP descending and take top 10
df_top = df.nlargest(10, "msrp").copy()

# Sort by country, then by MSRP descending for grouped presentation
df_top = df_top.sort_values(["ctry_origin", "msrp"], ascending=[True, False]).reset_index(drop=True)

# Create a display name combining manufacturer and model
df_top["car_name"] = df_top["mfr"] + " " + df_top["model"]

# Format drivetrain and transmission for display
df_top["drivetrain_transmission"] = df_top["drivetrain"].str.upper() + " / " + df_top["trsmn"]

# Select and reorder columns for display
display_cols = ["ctry_origin", "car_name", "drivetrain_transmission", "msrp"]
df_display = df_top[display_cols].copy()
df_display.columns = ["country", "car", "drivetrain_transmission", "price"]

# Compute domain for MSRP gradient
price_min = float(np.nanmin(df_display["price"].to_numpy()))
price_max = float(np.nanmax(df_display["price"].to_numpy()))

# Build the table
gt = (
    GT(df_display, rowname_col="car", groupname_col="country")
    .fmt_currency(columns=["price"], currency="USD")
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle="Grouped by country of origin with drivetrain and transmission details"
    )
    .data_color(
        columns=["price"],
        palette="Blues",
        domain=[price_min, price_max],
        truncate=False,
        na_color="#808080",
    )
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
        table_font_size="11pt",
        row_group_font_weight="bold",
        row_group_border_top_color="#BDBDBD",
        row_group_border_bottom_color="#BDBDBD",
    )
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    .opt_row_striping()
    .tab_source_note(
        "Top 10 vehicles ranked by MSRP (manufacturer's suggested retail price)"
    )
    .tab_source_note(
        "Data source: gtcars.csv"
    )
)

gt.gtsave("table.png")
