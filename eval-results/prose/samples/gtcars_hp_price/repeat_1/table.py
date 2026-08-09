import numpy as np
import pandas as pd
from great_tables import GT, style, loc

df = pd.read_csv("gtcars.csv")

df_table = df[["model", "hp", "msrp"]].copy()
df_table = df_table.sort_values("hp", ascending=False).reset_index(drop=True)

hp_lo = float(np.nanmin(df_table[["hp"]].to_numpy()))
hp_hi = float(np.nanmax(df_table[["hp"]].to_numpy()))

price_lo = float(np.nanmin(df_table[["msrp"]].to_numpy()))
price_hi = float(np.nanmax(df_table[["msrp"]].to_numpy()))

gt = (
    GT(df_table, rowname_col="model")
    .fmt_number(columns="hp", decimals=0, use_seps=True)
    .fmt_currency(columns="msrp", decimals=0)
    .sub_missing(columns=["hp", "msrp"], missing_text="—")
    .data_color(
        columns="hp",
        palette="Blues",
        domain=[hp_lo, hp_hi],
        truncate=False,
        na_color="#808080",
    )
    .data_color(
        columns="msrp",
        palette="Greens",
        domain=[price_lo, price_hi],
        truncate=False,
        na_color="#808080",
    )
    .tab_header(
        title="GT Cars: Horsepower and Price",
        subtitle="48 high-performance vehicles ranked by horsepower",
    )
    .tab_options(
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
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
    .opt_row_striping()
    .tab_source_note(source_note="Horsepower (hp) and Price (msrp) are the two colored measures.")
    .tab_source_note(source_note="Source: gtcars.csv")
)

gt.gtsave("table.png", expand=15)
