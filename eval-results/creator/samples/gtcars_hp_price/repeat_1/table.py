import pandas as pd
from great_tables import GT

df = pd.read_csv("gtcars.csv")

# Select and rename columns
tbl_df = df[["mfr", "model", "hp", "msrp"]].copy()
tbl_df.columns = ["Manufacturer", "Model", "Horsepower", "Price"]

tbl = (
    GT(tbl_df, rowname_col="Model")
    .tab_header(
        title="GT Cars: Horsepower and Price"
    )
    .fmt_integer(columns="Horsepower")
    .fmt_currency(columns="Price", currency="USD")
    .sub_missing(missing_text="—")
)

tbl.gtsave("table.png", zoom=2, expand=10)
print("Table saved to table.png")
