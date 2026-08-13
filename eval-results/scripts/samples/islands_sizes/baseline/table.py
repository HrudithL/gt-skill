import pandas as pd
from great_tables import GT

df = pd.read_csv('islands.csv')
gt = GT(df).tab_header(
    title="Islands and Their Sizes",
    subtitle="Size in thousands of square kilometers"
).fmt_integer(columns="size")

gt.gtsave("table.png")
