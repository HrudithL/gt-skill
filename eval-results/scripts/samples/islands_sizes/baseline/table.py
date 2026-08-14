import pandas as pd
from great_tables import GT

# Read the data
df = pd.read_csv("islands.csv")

# Create and format the table
gt = (
    GT(df)
    .tab_header(
        title="Islands and Their Sizes",
        subtitle="Size in thousands of square kilometers"
    )
    .cols_label(
        name="Island",
        size="Size (1000 km²)"
    )
    .cols_align(align="left", columns="name")
    .cols_align(align="right", columns="size")
    .fmt_number(columns="size", decimals=0)
    .tab_options(
        table_font_size="small"
    )
)

gt.gtsave("table.png")
