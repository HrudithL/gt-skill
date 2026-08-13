import pandas as pd
from great_tables import GT

df = pd.read_csv("islands.csv")

gt_table = (
    GT(df)
    .tab_header(
        title="Islands and Their Sizes",
        subtitle="Area in thousands of square kilometers"
    )
    .cols_label(
        name="Island Name",
        size="Size (1000 km²)"
    )
    .tab_style(
        style=[],
        locations=[]
    )
)

gt_table.gtsave("table.png")
