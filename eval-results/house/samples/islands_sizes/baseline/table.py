import pandas as pd
from great_tables import GT

# Read the CSV file
df = pd.read_csv("islands.csv")

# Create the GT table
gt = (
    GT(df)
    .tab_header(title="Islands of the World", subtitle="Size in thousands of square kilometers")
    .cols_label(name="Island", size="Size (1000 km²)")
    .fmt_number(columns="size", decimals=0)
    .opt_align_table_header("center")
    .tab_style(
        style=[],
        locations=[],
    )
)

gt.gtsave("table.png")
