import pandas as pd
from great_tables import GT

# Load the data
df = pd.read_csv("gtcars.csv")

# Select relevant columns and rename for display
table_df = df[["mfr", "model", "hp", "msrp"]].copy()
table_df.columns = ["Manufacturer", "Model", "Horsepower", "Price"]

# Format the table
gt_table = (
    GT(table_df)
    .fmt_integer(columns="Horsepower")
    .fmt_currency(columns="Price", currency="USD")
    .tab_header(
        title="GT Cars: Horsepower and Price",
        subtitle="Performance specifications and MSRP"
    )
)

# Render to PNG
gt_table.gtsave("table.png")
