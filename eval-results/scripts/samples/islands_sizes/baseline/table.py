import pandas as pd
from great_tables import GT

df = pd.read_csv("islands.csv")

gt = (
    GT(df)
    .tab_header(title="Islands of the World", subtitle="Land area in thousands of square miles")
    .cols_label(name="Island", size="Size")
    .fmt_number(columns="size", decimals=0)
    .opt_table_font(font="system-ui")
)

gt.gtsave("table.png")
