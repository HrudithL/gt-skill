import pandas as pd
from great_tables import GT

# Load the data
df = pd.read_csv('airquality.csv')

# Calculate monthly averages
monthly_avg = df.groupby('Month')[['Ozone', 'Wind', 'Temp']].mean().round(2)

# Rename columns and reset index for better display
monthly_avg = monthly_avg.reset_index()
monthly_avg.columns = ['Month', 'Ozone (ppb)', 'Wind (mph)', 'Temperature (°F)']

# Create month names for better readability
month_names = {5: 'May', 6: 'June', 7: 'July', 8: 'August', 9: 'September'}
monthly_avg['Month'] = monthly_avg['Month'].map(month_names)

# Create the GT table
gt = GT(monthly_avg)
gt = gt.tab_header(
    title='Air Quality Monthly Summary',
    subtitle='Average Temperature, Wind Speed, and Ozone Levels by Month'
)
gt = gt.fmt_number(columns=['Ozone (ppb)', 'Wind (mph)', 'Temperature (°F)'], decimals=1)

# Save to PNG
gt.gtsave('table.png')
