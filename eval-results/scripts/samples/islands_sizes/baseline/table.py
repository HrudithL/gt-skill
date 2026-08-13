import pandas as pd
from great_tables import GT

df = pd.read_csv('islands.csv')

gt = (
    GT(df)
    .tab_header(title="Islands by Size")
    .cols_label(name="Island Name", size="Size (1000 sq km)")
    .fmt_integer(columns="size")
    .cols_align(align="left", columns="name")
    .cols_align(align="right", columns="size")
)

gt.gtsave("table.png")
