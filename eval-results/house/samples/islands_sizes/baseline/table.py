import pandas as pd
from great_tables import GT

df = pd.read_csv("islands.csv")
gt = GT(df)
gt.gtsave("table.png")
