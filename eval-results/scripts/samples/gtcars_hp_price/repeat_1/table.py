import pandas as pd
from great_tables import GT, style, loc

df = pd.read_csv("gtcars.csv")

df = df[["mfr", "model", "hp", "msrp"]].copy()
df.columns = ["Manufacturer", "Model", "Horsepower", "Price"]

df = df.sort_values("Price", ascending=False).reset_index(drop=True)

gt = (
    GT(df, rowname_col="Manufacturer")
    .cols_label(
        Model="Model",
        Horsepower="Horsepower",
        Price="Price (USD)"
    )
    .fmt_number(
        columns="Horsepower",
        decimals=0,
        use_seps=True
    )
    .fmt_currency(
        columns="Price",
        currency="USD",
        decimals=0
    )
    .tab_header(
        title="GT Cars: Horsepower and Price",
        subtitle="Sorted by price (highest to lowest)"
    )
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
        row_striping_background_color="#F6F6F6"
    )
    .tab_style(
        style=style.fill(color="#F0F0F0"),
        locations=loc.stub()
    )
    .opt_row_striping()
    .tab_source_note(source_note="Source: gtcars.csv dataset")
)

gt.gtsave("table.png")
