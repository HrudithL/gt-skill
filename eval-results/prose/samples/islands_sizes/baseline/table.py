import pandas as pd
from great_tables import GT

# Read the islands data
df = pd.read_csv("islands.csv")

# Create a table
gt = (
    GT(df)
    .tab_header(
        title="Islands of the World",
        subtitle="Island sizes in thousands of square miles"
    )
    .cols_label(
        name="Island Name",
        size="Size (1,000 sq mi)"
    )
    .fmt_integer(
        columns="size"
    )
    .opt_align_table_header("center")
)

# Save the table as PNG
gt.gtsave("table.png")
print("Table saved to table.png")
