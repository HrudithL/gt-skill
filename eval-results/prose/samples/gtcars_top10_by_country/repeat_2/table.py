import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc

# Step 1: Load and clean the data
df = pd.read_csv("gtcars.csv")

# Clean drivetrain values
df["drivetrain"] = df["drivetrain"].str.upper()

# Clean transmission values (normalize to readable format)
def clean_transmission(trsmn):
    if pd.isna(trsmn):
        return "—"
    trsmn_str = str(trsmn).lower()
    if trsmn_str == "7a":
        return "7A"
    elif trsmn_str == "6a":
        return "6A"
    elif trsmn_str == "8a":
        return "8A"
    elif trsmn_str == "9a":
        return "9A"
    elif trsmn_str == "6m":
        return "6M"
    elif trsmn_str == "7m":
        return "7M"
    elif trsmn_str == "8am":
        return "8AM"
    elif trsmn_str == "7am":
        return "7AM"
    elif trsmn_str == "6am":
        return "6AM"
    elif trsmn_str == "1dd":
        return "1 Direct"
    return trsmn_str

df["transmission"] = df["trsmn"].map(clean_transmission)

# Create a display label combining make and model
df["car_display"] = df["mfr"] + " " + df["model"]

# Get top 10 most expensive cars overall
top_10 = df.nlargest(10, "msrp").copy()

# Sort by country, then by price within country
top_10 = top_10.sort_values(["ctry_origin", "msrp"], ascending=[True, False]).reset_index(drop=True)

# Select and prepare columns for display
display_df = top_10[["car_display", "ctry_origin", "drivetrain", "transmission", "msrp"]].copy()
display_df.columns = ["Car", "Country", "Drivetrain", "Transmission", "Price"]

# Ensure msrp is float for formatting
display_df["Price"] = pd.to_numeric(display_df["Price"], errors="coerce")

# Create the GT table
gt = (
    GT(display_df, rowname_col="Car", groupname_col="Country")
    .fmt_currency(columns=["Price"], currency="USD", decimals=0)
    .data_color(
        columns=["Price"],
        palette="Blues",
        domain=[float(np.nanmin(display_df["Price"].to_numpy())),
                float(np.nanmax(display_df["Price"].to_numpy()))],
        truncate=False,
        na_color="#808080",
    )
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle="Grouped by Country of Origin with Drivetrain and Transmission Details"
    )
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
        heading_background_color="#08306B",
        heading_align="center",
        column_labels_background_color="#08306B",
        column_labels_font_weight="bold",
    )
    .tab_style(
        style=style.fill(color="#08306B"),
        locations=loc.header(),
    )
    .tab_style(
        style=style.text(color="white", weight="bold"),
        locations=loc.header(),
    )
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    .opt_row_striping()
    .tab_source_note(
        "Sourced from the gtcars dataset showing the 10 highest MSRP values across all markets."
    )
    .tab_source_note(
        "Transmission codes: A = Automatic, M = Manual, AM = Automated Manual, DD = Direct Drive."
    )
)

gt.gtsave("table.png")
