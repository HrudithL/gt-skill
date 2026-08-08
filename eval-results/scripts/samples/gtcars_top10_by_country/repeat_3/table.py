"""Top 10 most expensive GT cars, grouped by country of origin.

Data: gtcars.csv (47 high-performance cars)
Story: Top 10 most expensive cars, organized by their country of origin,
       showing drivetrain and transmission details.
"""
import pandas as pd
from great_tables import GT, loc, style

df = pd.read_csv("gtcars.csv")

# Compose a single human label per car
df["car"] = df["mfr"] + " " + df["model"]

# Sort by MSRP descending and take the top 10
top = df.sort_values("msrp", ascending=False).head(10).reset_index(drop=True)
top["rank"] = top.index + 1

# Map transmission codes to readable format
trans_map = {
    "6a": "6-speed auto",
    "6m": "6-speed manual",
    "7a": "7-speed auto",
    "7m": "7-speed manual",
    "8a": "8-speed auto",
    "8am": "8-speed auto manual",
    "9a": "9-speed auto",
    "1dd": "Direct Drive",
}
top["transmission"] = top["trsmn"].map(trans_map)

# Map drivetrain codes to readable format
drive_map = {
    "rwd": "Rear-wheel drive",
    "awd": "All-wheel drive",
    "fwd": "Front-wheel drive",
}
top["drive_type"] = top["drivetrain"].map(drive_map)

# Select and order columns for display
top = top[["rank", "car", "ctry_origin", "drive_type", "transmission", "msrp"]]

gt = (
    GT(top, groupname_col="ctry_origin")
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle="Ranked by MSRP, grouped by country of origin",
    )
    .cols_label(
        rank="#",
        car="Car",
        ctry_origin="Country",
        drive_type="Drivetrain",
        transmission="Transmission",
        msrp="MSRP",
    )
    .fmt_currency(columns=["msrp"], currency="USD", decimals=0, use_seps=True)
    # Styling: bold the rank column
    .tab_style(style=style.text(weight="bold"), locations=loc.body(columns=["rank"]))
    # Align left for text, right for numeric
    .cols_align(align="left", columns=["car", "drive_type", "transmission"])
    .cols_align(align="right", columns=["rank", "msrp"])
    # Row striping and group styling
    .tab_options(
        row_group_background_color="#F0F0F0",
        row_group_font_weight="bold",
        row_group_border_top_color="#BDBDBD",
        row_group_border_bottom_color="#BDBDBD",
        row_group_padding="6px",
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
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
    )
    .tab_source_note(source_note="Source: gtcars dataset (Posit / great_tables sample data).")
)

gt.gtsave("table.png", expand=15)
