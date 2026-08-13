import pandas as pd
from great_tables import GT

df = pd.read_csv("gtcars.csv")

# Select and rename relevant columns
display_df = df[["mfr", "model", "hp", "msrp"]].copy()
display_df.columns = ["Manufacturer", "Model", "Horsepower", "Price ($)"]

# Sort by horsepower descending
display_df = display_df.sort_values("Horsepower", ascending=False).reset_index(drop=True)

# Format the table
gt = (
    GT(display_df)
    .fmt_integer(columns="Horsepower")
    .fmt_currency(columns="Price ($)", currency="USD")
)

gt.gtsave("table.png")
