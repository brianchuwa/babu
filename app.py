import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Title and Intro
title = "Apef Trust Investment Calculator"
st.title(title)
st.write("Calculate and visualize your investments in Apef Trust.")

# Input Fields
investment = st.number_input("Investment Amount (Tsh):", min_value=100000.0, value=1000000.0, step=100000.0)
annual_growth = st.number_input("Apef Trust Annual Growth (%):", min_value=0.0, value=16.0, step=0.1) / 100
start_date = st.date_input("Start Date:", value=datetime(2025, 1, 1))
end_date = st.date_input("End Date:", value=datetime(2025, 12, 31))

custodian_fee = st.number_input("Custodian Fee (%):", min_value=0.0, value=0.1, step=0.01) / 100
management_fee = st.number_input("Management Fee (%):", min_value=0.0, value=1.8, step=0.1) / 100
other_fees = st.number_input("Expenses and Other Charges (%):", min_value=0.0, value=0.35, step=0.01) / 100

total_fees = custodian_fee + management_fee + other_fees

# Display Total Fees
st.write(f"Total Fees: {total_fees * 100:.2f}%")

# Date Calculations
date_range = pd.date_range(start=start_date, end=end_date)
number_of_days = len(date_range)
daily_growth_rate = (1 + annual_growth) ** (1 / 365) - 1

# Calculations
initial_value = investment
values = [initial_value]
fees_cumulative = [0]

for i in range(1, number_of_days):
    daily_value = values[-1] * (1 + daily_growth_rate)
    daily_fees = daily_value * total_fees / 365
    net_value = daily_value - daily_fees

    values.append(net_value)
    fees_cumulative.append(fees_cumulative[-1] + daily_fees)

data = {
    "Date": date_range,
    "Value": values,
    "Cumulative Fees": fees_cumulative,
    "Net Value": np.array(values) - np.array(fees_cumulative)
}

results_df = pd.DataFrame(data)

# Summary Metrics
final_value = results_df["Value"].iloc[-1]
final_cumulative_fees = results_df["Cumulative Fees"].iloc[-1]
final_net_value = results_df["Net Value"].iloc[-1]

# Scorecards
st.metric(label="Final Investment Value (Tsh)", value=f"{final_value:,.2f}")
st.metric(label="Net Investment Value (Tsh)", value=f"{final_net_value:,.2f}")
st.metric(label="Total Fees (Tsh)", value=f"{final_cumulative_fees:,.2f}")

# Charts
st.line_chart(results_df.set_index("Date")["Value"], height=300, use_container_width=True, title="Daily Investment Growth")
st.line_chart(results_df.set_index("Date")["Net Value"], height=300, use_container_width=True, title="Net Investment Growth")
st.line_chart(results_df.set_index("Date")["Cumulative Fees"], height=300, use_container_width=True, title="Cumulative Fees")

# Table
st.write("Daily Investment Data")
st.dataframe(results_df)
