import pandas as pd
from great_tables import GT

df = pd.read_csv("islands.csv")
df = df.sort_values("size", ascending=False).reset_index(drop=True)

gt = (
    GT(df)
    .tab_header(title="Islands and Their Sizes")
    .cols_label(name="Island", size="Size (1000 km²)")
    .fmt_number(columns="size", decimals=0)
    .opt_stylize(style=3, color="blue")
)

gt.gtsave("table.png")
