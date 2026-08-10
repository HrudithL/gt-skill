import pandas as pd
from great_tables import GT
from great_tables.data import exibble

df = pd.read_csv("gtcars.csv")

# Select relevant columns: manufacturer, model, horsepower, and price (msrp)
df_display = df[["mfr", "model", "hp", "msrp"]].copy()
df_display.columns = ["Manufacturer", "Model", "Horsepower", "Price"]

# Create and render the table
gt = GT(df_display)
gt = gt.fmt_number(columns="Price", decimals=0, use_seps=True)
gt = gt.cols_label(Horsepower="HP", Price="Price ($)")
gt.gtsave("table.png")
