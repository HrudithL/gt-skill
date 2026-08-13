import pandas as pd
import great_tables as gt

# Read the air quality data
df = pd.read_csv('airquality.csv')

# Compute monthly averages
monthly_avg = df.groupby('Month')[['Ozone', 'Wind', 'Temp']].mean()

# Create a mapping for month names
month_names = {
    5: 'May',
    6: 'June',
    7: 'July',
    8: 'August',
    9: 'September'
}

# Reset index and add month names
monthly_avg = monthly_avg.reset_index()
monthly_avg['Month_Name'] = monthly_avg['Month'].map(month_names)
monthly_avg = monthly_avg[['Month_Name', 'Temp', 'Wind', 'Ozone']]

# Rename columns for display
monthly_avg.columns = ['Month', 'Avg Temperature (°F)', 'Avg Wind Speed (mph)', 'Avg Ozone (ppb)']

# Create and format the table
gt_table = (
    gt.GT(monthly_avg)
    .fmt_number(columns=['Avg Temperature (°F)', 'Avg Wind Speed (mph)', 'Avg Ozone (ppb)'], decimals=2)
    .tab_header(
        title='Monthly Air Quality Summary',
        subtitle='Average temperature, wind speed, and ozone levels by month'
    )
    .opt_stylize(style=1, color='blue')
)

# Render to PNG
gt_table.gtsave('table.png')
