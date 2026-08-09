import pandas as pd
from great_tables import GT

df = pd.read_csv('islands.csv')

gt_table = (
    GT(df)
    .tab_header(
        title="Islands and Their Sizes",
        subtitle="Size in thousands of square kilometers"
    )
    .cols_label(
        name="Island",
        size="Size (1000 km²)"
    )
    .fmt_integer(
        columns='size'
    )
    .opt_align_table_header("center")
)

gt_table.gtsave("table.png")
