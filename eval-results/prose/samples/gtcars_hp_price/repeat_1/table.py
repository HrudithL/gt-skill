import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc

df = pd.read_csv("gtcars.csv")

df["car_name"] = df["mfr"] + " " + df["model"]
display_cols = ["car_name", "hp", "msrp"]
df_display = df[display_cols].copy()
df_display.columns = ["Car", "Horsepower", "Price"]

df_display = df_display.reset_index(drop=True)

cols_to_color = ["Price"]
lo = float(np.nanmin(df_display[cols_to_color].to_numpy()))
hi = float(np.nanmax(df_display[cols_to_color].to_numpy()))

gt = (
    GT(df_display, rowname_col="Car")
    .fmt_number(columns=["Horsepower"], decimals=0, use_seps=True)
    .fmt_currency(columns=["Price"], currency="USD", decimals=0)
    .data_color(
        columns=["Price"],
        palette="Blues",
        domain=[lo, hi],
        truncate=False,
        na_color="#808080",
    )
    .tab_header(
        title="GT Cars",
        subtitle="Horsepower and Price"
    )
    .tab_options(
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
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    .opt_row_striping()
    .cols_width(cases={"Car": "200px", "Horsepower": "120px", "Price": "120px"})
    .tab_header(
        title="GT Cars",
        subtitle="Horsepower and Price"
    )
    .tab_source_note(source_note="Price is the primary hero measure; horsepower is shown for context but not color-encoded as it is a near-redundant proxy for the same underlying 'performance' concept.")
    .tab_source_note(source_note="Source: gtcars.csv")
)

gt.gtsave("table.png", expand=15)
