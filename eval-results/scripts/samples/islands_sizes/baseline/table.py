import pandas as pd
from great_tables import GT

# Read the island data
df = pd.read_csv('islands.csv')

# Create the table
gt = (
    GT(df)
    .tab_header(
        title="World Islands by Size",
        subtitle="Area in thousands of square kilometers"
    )
    .fmt_integer(columns="size")
)

# Render to PNG
gt.gtsave("table.png")
