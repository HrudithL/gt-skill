import pandas as pd
from great_tables import GT

df = pd.read_csv('islands.csv')

gt = (
    GT(df)
    .tab_header(
        title="Islands by Size",
        subtitle="World's largest islands (in thousands of square miles)"
    )
    .cols_label(name="Island", size="Size (thousands of sq mi)")
    .fmt_number(columns="size", decimals=0)
    .cols_align(align="center", columns="size")
)

gt.gtsave("table.png")
