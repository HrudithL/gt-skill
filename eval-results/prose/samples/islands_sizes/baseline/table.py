import pandas as pd
from great_tables import GT

df = pd.read_csv("islands.csv")

gt = (
    GT(df)
    .tab_header(
        title="Islands and Their Sizes",
        subtitle="Size in thousands of square kilometers"
    )
    .cols_label(name="Island", size="Size (1000 km²)")
    .fmt_number(columns="size", decimals=0)
    .cols_align(align="center", columns="size")
)

gt.gtsave("table.png")
