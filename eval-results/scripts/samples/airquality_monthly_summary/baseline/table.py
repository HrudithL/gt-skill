import pandas as pd
from great_tables import GT

# Load the data
df = pd.read_csv('airquality.csv')

# Group by month and calculate means
monthly_summary = df.groupby('Month')[['Temp', 'Wind', 'Ozone']].mean().round(2)

# Create month names for better readability
month_names = {
    5: 'May',
    6: 'June',
    7: 'July',
    8: 'August',
    9: 'September'
}

# Reset index and rename columns
monthly_summary = monthly_summary.reset_index()
monthly_summary['Month'] = monthly_summary['Month'].map(month_names)
monthly_summary = monthly_summary.rename(columns={
    'Month': 'Month',
    'Temp': 'Avg Temperature (°F)',
    'Wind': 'Avg Wind Speed (mph)',
    'Ozone': 'Avg Ozone (ppb)'
})

# Create the GT table
gt = (
    GT(monthly_summary)
    .tab_header(
        title="Air Quality Monthly Summary",
        subtitle="Average Temperature, Wind Speed, and Ozone Levels"
    )
)

# Save to PNG
gt.gtsave("table.png")
