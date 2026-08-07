import pandas as pd
from great_tables import GT

df = pd.read_csv("gtcars.csv")

# Select relevant columns and rename for clarity
table_df = df[["mfr", "model", "hp", "msrp"]].copy()
table_df.columns = ["Manufacturer", "Model", "Horsepower", "Price"]

# Create GT table
gt = (
    GT(table_df)
    .fmt_currency(columns="Price", currency="USD")
    .fmt_number(columns="Horsepower", decimals=0)
    .tab_header(title="GT Cars: Horsepower and Price")
)

gt.gtsave("table.png")
