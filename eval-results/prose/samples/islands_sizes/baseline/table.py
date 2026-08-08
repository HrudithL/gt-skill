import pandas as pd
from great_tables import GT

df = pd.read_csv("islands.csv")

gt = (
    GT(df)
    .tab_header(title="Islands and Their Sizes")
    .cols_label(name="Island Name", size="Size (1000 km²)")
    .cols_align(align="center")
)

gt.gtsave("table.png")
