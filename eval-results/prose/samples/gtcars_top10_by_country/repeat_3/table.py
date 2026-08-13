import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc

# Step 1: Load and clean data
df = pd.read_csv("gtcars.csv")

# Select top 10 most expensive cars
df_top = df.nlargest(10, "msrp").copy()

# Group by country and sort by price within group
df_top = df_top.sort_values(["ctry_origin", "msrp"], ascending=[True, False])

# Create display columns
df_top["car_name"] = df_top["mfr"] + " " + df_top["model"]
df_top["price"] = df_top["msrp"]

# Clean up drivetrain display
drivetrain_map = {"rwd": "RWD", "awd": "AWD", "fwd": "FWD"}
df_top["drivetrain_display"] = df_top["drivetrain"].map(drivetrain_map)

# Clean up transmission display (extract key parts: "7a" -> "7-Speed Auto", "6m" -> "6-Speed Manual", etc)
def clean_transmission(trsmn):
    if pd.isna(trsmn):
        return "—"
    trsmn = str(trsmn).strip()
    if trsmn.endswith("a"):
        speeds = trsmn[:-1]
        return f"{speeds}-Speed Auto"
    elif trsmn.endswith("m"):
        speeds = trsmn[:-1]
        return f"{speeds}-Speed Manual"
    elif trsmn.endswith("am"):
        speeds = trsmn[:-2]
        return f"{speeds}-Speed Auto"
    elif trsmn.endswith("dd"):
        return "Direct Drive"
    else:
        return trsmn

df_top["transmission_display"] = df_top["trsmn"].apply(clean_transmission)

# Select and rename columns for display
display_cols = ["car_name", "ctry_origin", "drivetrain_display", "transmission_display", "price"]
col_labels = {
    "car_name": "Car",
    "ctry_origin": "Country",
    "drivetrain_display": "Drivetrain",
    "transmission_display": "Transmission",
    "price": "MSRP"
}

df_display = df_top[display_cols].copy()
df_display = df_display.rename(columns=col_labels)

# Step 2: Organize columns and set up grouping
gt = (
    GT(df_display, rowname_col=None, groupname_col="Country")
    .cols_move_to_start(columns=["Car"])
)

# Step 3: Apply Big Color (column gradient for MSRP)
cols_to_color = ["MSRP"]
lo = float(np.nanmin(df_display[cols_to_color].to_numpy()))
hi = float(np.nanmax(df_display[cols_to_color].to_numpy()))

gt = gt.data_color(
    columns=cols_to_color,
    palette="Blues",
    domain=[lo, hi],
    truncate=False,
    na_color="#808080",
)

# Step 4: Heading band - dark navy band with white bold text
gt = gt.tab_header(
    title="Top 10 Most Expensive GT Cars by Country",
    subtitle="Grouped by country of origin with drivetrain and transmission details"
)

# Step 4 continued: Set heading band styling (already done by tab_header, now color the band)
gt = gt.tab_options(
    heading_background_color="#08306B",
    heading_title_font_weight="bold",
    heading_title_font_size="18px",
    heading_subtitle_font_size="14px",
)

# Step 5: Small Color polish
# (a) Cell borders
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
    column_labels_border_bottom_color="#CCCCCC",
    column_labels_border_bottom_width="2px",
)

# (b) Column-group vertical dividers - not needed for single grouping
# (c) Row striping - apply by default
gt = (
    gt.opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
)

# (e) Format columns
gt = (
    gt.fmt_currency(columns="MSRP", currency="USD", decimals=0)
    .sub_missing(columns=["Drivetrain", "Transmission", "MSRP"], missing_text="—")
)

# (f) Row group styling - bold + structural rule
gt = gt.tab_options(
    row_group_font_weight="bold",
    row_group_border_top_color="#BDBDBD",
    row_group_border_bottom_color="#BDBDBD",
    row_group_padding="6px",
)

# (f) Titles & annotations
gt = (
    gt.tab_source_note(
        source_note="Includes the top 10 highest-priced GT cars from the dataset, displayed with their country of origin."
    )
    .tab_source_note(
        source_note="Source: gtcars.csv"
    )
)

# Frame and padding
gt = gt.tab_options(
    table_border_top_style="solid",
    table_border_top_color="#CCCCCC",
    table_border_top_width="1px",
    table_border_bottom_style="solid",
    table_border_bottom_color="#CCCCCC",
    table_border_bottom_width="1px",
    table_border_left_style="solid",
    table_border_left_color="#CCCCCC",
    table_border_left_width="1px",
    table_border_right_style="solid",
    table_border_right_color="#CCCCCC",
    table_border_right_width="1px",
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Adjust column widths for content
gt = gt.cols_width(
    cases={
        "Car": "140px",
        "Country": "110px",
        "Drivetrain": "90px",
        "Transmission": "140px",
        "MSRP": "130px",
    }
)

# Step 7: Render
gt.gtsave("table.png", expand=15)
print("Table rendered successfully to table.png")
