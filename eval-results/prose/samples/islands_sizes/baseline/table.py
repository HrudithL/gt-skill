import pandas as pd
from great_tables import GT

df = pd.read_csv("islands.csv")

gt_tbl = (
    GT(df)
    .tab_header(
        title="World Islands by Size",
        subtitle="Land area in thousands of square miles"
    )
    .cols_label(name="Island", size="Size")
    .fmt_number(columns="size", decimals=0)
    .opt_align_table_header("left")
)

gt_tbl.gtsave("table.png")
