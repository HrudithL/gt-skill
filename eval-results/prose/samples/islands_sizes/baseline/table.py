import pandas as pd
from great_tables import GT

# Read the CSV data
df = pd.read_csv('islands.csv')

# Create the table
gt_table = (
    GT(df)
    .tab_header(
        title="Islands by Size",
        subtitle="Size measurements in thousands of square kilometers"
    )
    .cols_label(
        name="Island",
        size="Size (1000 km²)"
    )
    .cols_align(align="left", columns="name")
    .cols_align(align="right", columns="size")
    .tab_options(
        container_width="500px"
    )
)

# Save as PNG
gt_table.gtsave("table.png")
