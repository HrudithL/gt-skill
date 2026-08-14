import pandas as pd
import great_tables as gt

# Read the air quality data
df = pd.read_csv('airquality.csv')

# Calculate monthly averages
monthly_avg = df.groupby('Month')[['Temp', 'Wind', 'Ozone']].mean().reset_index()

# Map month numbers to names
month_names = {
    5: 'May',
    6: 'June',
    7: 'July',
    8: 'August',
    9: 'September'
}
monthly_avg['Month'] = monthly_avg['Month'].map(month_names)

# Rename columns for display
monthly_avg = monthly_avg.rename(columns={
    'Month': 'Month',
    'Temp': 'Avg Temperature (°F)',
    'Wind': 'Avg Wind Speed (mph)',
    'Ozone': 'Avg Ozone (ppb)'
})

# Create the table
gt_table = (
    gt.GT(monthly_avg)
    .fmt_number(columns=['Avg Temperature (°F)', 'Avg Wind Speed (mph)', 'Avg Ozone (ppb)'], decimals=1)
    .tab_header(
        title='Air Quality Monthly Summary',
        subtitle='Average Temperature, Wind Speed, and Ozone Levels'
    )
    .opt_align_table_header('center')
)

# Render and save
gt_table.gtsave('table.png')
print("Table created and saved to table.png")
