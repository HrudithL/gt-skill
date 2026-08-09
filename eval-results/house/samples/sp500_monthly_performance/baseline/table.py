import pandas as pd
import numpy as np
from great_tables import GT

# Read the S&P 500 data
df = pd.read_csv("sp500.csv")
df["date"] = pd.to_datetime(df["date"])

# Filter for 2010-2015
df = df[(df["date"].dt.year >= 2010) & (df["date"].dt.year <= 2015)]
df = df.sort_values("date").reset_index(drop=True)

# Extract year and month
df["year"] = df["date"].dt.year
df["month"] = df["date"].dt.month

# Group by year and month to calculate metrics
monthly_data = []

for (year, month), group in df.groupby(["year", "month"]):
    group = group.sort_values("date")

    opening_price = group.iloc[0]["open"]
    closing_price = group.iloc[-1]["close"]
    percent_change = ((closing_price - opening_price) / opening_price) * 100
    avg_volume = group["volume"].mean()

    # Calculate daily gains/losses
    group["daily_change"] = group["high"] - group["low"]
    group["daily_gain"] = group["close"] - group["open"]

    highest_gain = group["daily_gain"].max()
    highest_loss = group["daily_gain"].min()

    monthly_data.append({
        "Date": f"{year}-{month:02d}",
        "Open": opening_price,
        "Close": closing_price,
        "Change %": percent_change,
        "Avg Volume": avg_volume,
        "Highest Gain": highest_gain,
        "Highest Loss": highest_loss,
    })

result_df = pd.DataFrame(monthly_data)

# Create the GT table
gt = (
    GT(result_df)
    .fmt_number(columns=["Open", "Close", "Highest Gain", "Highest Loss"], decimals=2)
    .fmt_number(columns=["Change %"], decimals=2)
    .fmt_number(columns=["Avg Volume"], decimals=0)
)

gt.gtsave("table.png")
print("Table saved to table.png")
