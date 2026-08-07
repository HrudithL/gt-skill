import pandas as pd
from great_tables import GT

df = pd.read_csv("airquality.csv")

monthly_stats = df.groupby("Month").agg({
    "Temp": "mean",
    "Wind": "mean",
    "Ozone": "mean"
}).round(2)

month_names = {
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September"
}

monthly_stats.index = monthly_stats.index.map(month_names)
monthly_stats.columns = ["Avg Temperature (°F)", "Avg Wind Speed (mph)", "Avg Ozone (ppb)"]

gt_table = (
    GT(monthly_stats.reset_index().rename(columns={"index": "Month"}))
    .tab_header(
        title="Air Quality Monthly Summary",
        subtitle="Average Temperature, Wind Speed, and Ozone Levels"
    )
    .fmt_number(
        columns=["Avg Temperature (°F)", "Avg Wind Speed (mph)", "Avg Ozone (ppb)"],
        decimals=2
    )
)

gt_table.gtsave("table.png")
print("Table saved to table.png")
