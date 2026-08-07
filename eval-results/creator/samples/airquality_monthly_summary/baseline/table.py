import pandas as pd
from great_tables import GT

# Read the data
df = pd.read_csv('airquality.csv')

# Calculate monthly averages
monthly_avg = df.groupby('Month')[['Temp', 'Wind', 'Ozone']].mean()

# Create mapping for month names
month_names = {
    5: 'May',
    6: 'June',
    7: 'July',
    8: 'August',
    9: 'September'
}

# Add month names to the index
monthly_avg['Month'] = monthly_avg.index.map(month_names)
monthly_avg = monthly_avg[['Month', 'Temp', 'Wind', 'Ozone']]
monthly_avg = monthly_avg.reset_index(drop=True)

# Round to 2 decimal places
monthly_avg = monthly_avg.round(2)

# Create the GT table
gt = (
    GT(monthly_avg)
    .tab_header(
        title="Air Quality Monthly Summary",
        subtitle="Average Temperature, Wind Speed, and Ozone Levels by Month"
    )
    .cols_label(
        Month="Month",
        Temp="Avg Temperature (°F)",
        Wind="Avg Wind Speed (mph)",
        Ozone="Avg Ozone (ppb)"
    )
    .fmt_number(
        columns=['Temp', 'Wind', 'Ozone'],
        decimals=2
    )
)

# Save as PNG
gt.gtsave("table.png")
print("Table saved to table.png")
