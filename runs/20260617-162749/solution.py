import pandas as pd
from great_tables import GT

# Load the CSV data
df = pd.read_csv('gtcars.csv')

# Sort by horsepower (hp) in descending order and get top 5
top_5_hp = df.nlargest(5, 'hp')[['mfr', 'model', 'year', 'hp', 'msrp', 'mpg_h']].reset_index(drop=True)

# Create a GT table with styling
gt = (
    GT(top_5_hp)
    .tab_header(
        title="Top 5 Cars by Horsepower",
        subtitle="High-performance vehicles ranked by power output"
    )
    .cols_label(
        mfr="Manufacturer",
        model="Model",
        year="Year",
        hp="Horsepower (HP)",
        msrp="MSRP",
        mpg_h="MPG (Highway)"
    )
    .fmt_currency(
        columns="msrp",
        currency="USD"
    )
    .fmt_number(
        columns="hp",
        decimals=0
    )
    .fmt_number(
        columns="mpg_h",
        decimals=1
    )
    .tab_options(
        table_layout="auto",
        table_font_size="14px"
    )
)

# Save as PNG
gt.gtsave('table.png')

print("Table created successfully and saved as table.png")
