import pandas as pd
from great_tables import GT

df = pd.read_csv('islands.csv')

gt = (
    GT(df)
    .tab_header(title="Islands and Their Sizes")
    .cols_label(name="Island", size="Size (thousands of km²)")
    .fmt_number(columns="size", decimals=0)
    .opt_align_table_header("center")
)

gt.gtsave("table.png")
