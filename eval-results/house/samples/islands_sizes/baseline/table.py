import pandas as pd
from great_tables import GT

# Read the CSV file
df = pd.read_csv('islands.csv')

# Create the GT table
gt = (
    GT(df)
    .tab_header(
        title="World's Largest Islands",
        subtitle="Island sizes in thousands of square kilometers"
    )
    .cols_label(
        name="Island",
        size="Size (1000 km²)"
    )
    .cols_align(align="left", columns="name")
    .cols_align(align="right", columns="size")
    .data_color(
        palette="viridis",
        columns="size"
    )
)

# Render to PNG
gt.gtsave("table.png")
print("Table rendered to table.png")
