import pandas as pd
from great_tables import GT

df = pd.read_csv("gtcars.csv")
df_subset = df[["mfr", "model", "hp", "msrp"]].copy()
df_subset.columns = ["Manufacturer", "Model", "Horsepower", "Price"]

gt_table = (
    GT(df_subset)
    .fmt_integer(columns="Horsepower")
    .fmt_currency(columns="Price", currency="USD")
)

gt_table.gtsave("table.png")
