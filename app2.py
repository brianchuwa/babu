import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from datetime import datetime, timedelta

# Set page to wide mode by default
st.set_page_config(layout="wide")

def format_currency(value):
    """Format large numbers in TZS with commas"""
    return f"TZS {value:,.2f}"

def calculate_daily_values(investment_amount, annual_growth_rate, start_date, end_date, 
                         custodian_fee, management_fee, other_charges):
    # Convert dates to datetime objects
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    
    # Generate date range
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Calculate daily growth rate (compounded)
    daily_growth_rate = (1 + annual_growth_rate) ** (1/365) - 1
    
    # Initialize dataframe
    df = pd.DataFrame(index=date_range)
    df.index.name = 'Date'
    
    # Initialize the first day's values
    df['Opening_Value'] = 0.0  # Will fill this column
    df['Closing_Value'] = 0.0  # Will fill this column
    
    # Set first day's opening value
    df.loc[df.index[0], 'Opening_Value'] = investment_amount
    
    # Calculate daily values
    for i in range(len(df)):
        if i == 0:
            # First day: grow the opening value
            opening_value = investment_amount
        else:
            # Subsequent days: opening value is previous day's closing value
            opening_value = df['Closing_Value'].iloc[i-1]
        
        df.loc[df.index[i], 'Opening_Value'] = opening_value
        df.loc[df.index[i], 'Closing_Value'] = opening_value * (1 + daily_growth_rate)
    
    # Calculate daily fees based on closing values
    df['Custodian_Fee'] = df['Closing_Value'] * (custodian_fee / 365)
    df['Management_Fee'] = df['Closing_Value'] * (management_fee / 365)
    df['Other_Charges'] = df['Closing_Value'] * (other_charges / 365)
    df['Total_Daily_Fees'] = df['Custodian_Fee'] + df['Management_Fee'] + df['Other_Charges']
    
    # Calculate cumulative fees
    df['Cumulative_Fees'] = df['Total_Daily_Fees'].cumsum()
    
    # Calculate net value (closing value minus cumulative fees)
    df['Net_Value'] = df['Closing_Value'] - df['Cumulative_Fees']
    
    return df

def main():
    st.title('Apef Trust Investment Calculator')
    
    # Input fields
    col1, col2, col3 = st.columns(3)
    
    with col1:
        investment_amount = st.number_input('Investment Amount (TZS)', 
                                          min_value=0.0, 
                                          value=10_000_000_000.0, 
                                          step=1_000_000.0,
                                          format="%0.2f")
    
    with col2:
        annual_growth = st.number_input('Annual Growth Rate (%)', 
                                      min_value=0.0, 
                                      value=16.0, 
                                      step=0.1) / 100
    
    with col3:
        dates = st.date_input('Investment Period',
                            value=(datetime(2025, 1, 1), datetime(2025, 12, 31)),
                            min_value=datetime(2025, 1, 1),
                            max_value=datetime(2030, 12, 31))
    
    # Fee inputs
    fee_col1, fee_col2, fee_col3 = st.columns(3)
    
    with fee_col1:
        custodian_fee = st.number_input('Custodian Fee (%)', 
                                      min_value=0.0, 
                                      value=0.1, 
                                      step=0.01) / 100
    
    with fee_col2:
        management_fee = st.number_input('Management Fee (%)', 
                                       min_value=0.0, 
                                       value=1.8, 
                                       step=0.01) / 100
    
    with fee_col3:
        other_charges = st.number_input('Other Charges (%)', 
                                      min_value=0.0, 
                                      value=0.35, 
                                      step=0.01) / 100
    
    # Calculate values
    if len(dates) == 2:
        start_date, end_date = dates
        df = calculate_daily_values(investment_amount, annual_growth, start_date, end_date,
                                  custodian_fee, management_fee, other_charges)
        
        # Display metrics in rows of 2
        st.subheader('Investment Summary')
        
        # First row of metrics
        metric_row1_col1, metric_row1_col2 = st.columns(2)
        with metric_row1_col1:
            st.metric("Final Investment Value", 
                     format_currency(df['Closing_Value'].iloc[-1]))
        with metric_row1_col2:
            final_net = df['Closing_Value'].iloc[-1] - df['Cumulative_Fees'].iloc[-1]
            st.metric("Final Net Value", 
                     format_currency(final_net))
        
        # Second row of metrics
        metric_row2_col1, metric_row2_col2 = st.columns(2)
        with metric_row2_col1:
            st.metric("Total Custodian Fees", 
                     format_currency(df['Custodian_Fee'].sum()))
        with metric_row2_col2:
            st.metric("Total Management Fees", 
                     format_currency(df['Management_Fee'].sum()))
        
        # Third row of metrics
        metric_row3_col1, metric_row3_col2 = st.columns(2)
        with metric_row3_col1:
            st.metric("Total Other Charges", 
                     format_currency(df['Other_Charges'].sum()))
        with metric_row3_col2:
            st.metric("Total Fees", 
                     format_currency(df['Total_Daily_Fees'].sum()))
        
        # Line chart
        st.subheader('Value Over Time')
        chart_data = df.reset_index().melt('Date', 
                                         value_vars=['Closing_Value', 'Net_Value'],
                                         var_name='Category',
                                         value_name='Value')
        
        # Calculate minimum value for y-axis
        min_value = min(chart_data['Value'].min(), investment_amount) * 0.95  # 5% below the minimum
        max_value = chart_data['Value'].max() * 1.05  # 5% above the maximum

        line_chart = alt.Chart(chart_data).mark_line().encode(
            x='Date:T',
            y=alt.Y('Value:Q', 
                    axis=alt.Axis(format=',.0f', title='Value (TZS)'),
                    scale=alt.Scale(domain=[min_value, max_value])),
            color=alt.Color('Category:N', scale=alt.Scale(
                domain=['Closing_Value', 'Net_Value'],
                range=['#1f77b4', '#2ca02c']
            )),
            tooltip=[
                alt.Tooltip('Date:T'),
                alt.Tooltip('Value:Q', format=',.2f', title='Value (TZS)'),
                'Category'
            ]
        ).properties(
            height=400
        )
        
        st.altair_chart(line_chart, use_container_width=True)
        
        # Fees chart
        st.subheader('Daily Fees Breakdown')
        fees_data = df.reset_index().melt('Date', 
                                        value_vars=['Custodian_Fee', 'Management_Fee', 'Other_Charges'],
                                        var_name='Fee Type',
                                        value_name='Amount')
        
        fees_chart = alt.Chart(fees_data).mark_area().encode(
            x='Date:T',
            y=alt.Y('Amount:Q', axis=alt.Axis(format=',.0f', title='Amount (TZS)')),
            color='Fee Type:N',
            tooltip=[
                alt.Tooltip('Date:T'),
                alt.Tooltip('Amount:Q', format=',.2f', title='Amount (TZS)'),
                'Fee Type'
            ]
        ).properties(
            height=300
        )
        
        st.altair_chart(fees_chart, use_container_width=True)
        
        # Data table
        st.subheader('Daily Values')
        # Reorder columns for better readability
        columns_order = ['Opening_Value', 'Closing_Value', 'Custodian_Fee', 
                        'Management_Fee', 'Other_Charges', 'Total_Daily_Fees',
                        'Cumulative_Fees', 'Net_Value']
        df_display = df[columns_order].round(2)
        df_display.index = df_display.index.strftime('%Y-%m-%d')
        st.dataframe(df_display, use_container_width=True)

if __name__ == '__main__':
    main()