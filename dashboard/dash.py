# Import required libraries
import os
import pandas as pd
import numpy as np
import requests
import time
import streamlit as st
import plotly
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from stqdm import stqdm

import seaborn as sns; sns.set()
import matplotlib.pyplot as plt

# Function to retrieve power load data
def get_powerLoad(end_date, lookback=False):
    # Define the range of dates to fetch data for
    if lookback:
        end_date = datetime.now() + timedelta(days=1)
        start_date = datetime.now() - timedelta(days=lookback)
        dates = pd.date_range(start=start_date, end=end_date, inclusive='left')
    else:
        dates = [datetime.strptime(date, '%Y/%m/%d').date()]
    
    # Initialize an empty list to hold DataFrame objects
    df_list = []
    
    # Fetch data for each date in the range
    for date in stqdm(dates, desc="下載 powerLoad 中 "):
        payload = {'date': date.strftime('%Y/%m/%d')}
        r = requests.get('https://purbao.lass-net.org/powerLoad', params=payload)
        
        # Convert the response to a DataFrame
        df_temp = pd.DataFrame(r.json())
        df_temp = df_temp.rename(columns={'_id':'time'})
        df_temp['date'] = date.strftime('%Y/%m/%d')
        df_temp['time'] = pd.to_datetime(df_temp['time'], format='%H:%M:%S').dt.time.astype('str')
        df_temp['datetime'] = pd.to_datetime(df_temp['date'] + ' ' + df_temp['time'], errors='coerce')
        df_temp = df_temp.drop(['time','date'], axis=1)
        df_temp = df_temp.melt(id_vars='datetime', var_name='area', value_name='load')
        
        # Append the DataFrame to the list
        df_list.append(df_temp)
    
    # Combine all DataFrames in the list
    result_df = pd.concat(df_list)
    return result_df

# Function to retrieve power ratio data
def get_powerRatio(end_date, lookback=False):

    if lookback:
        end_date = datetime.now() + timedelta(days=1)
        start_date = datetime.now() - timedelta(days=lookback)
        dates = pd.date_range(start=start_date, end=end_date, inclusive='left')
    else:
        dates = [datetime.strptime(date, '%Y/%m/%d').date()]
    
    df_list = []
    
    for date in stqdm(dates, desc="下載 powerRatio 中 "):
        payload = {'date': date.strftime('%Y/%m/%d')}
        r = requests.get('https://purbao.lass-net.org/powerRatio', params=payload)
        
        df_temp = pd.DataFrame(r.json())
        df_temp = df_temp.rename(columns={'_id':'time'})
        df_temp['date'] = date.strftime('%Y/%m/%d')
        df_temp['time'] = pd.to_datetime(df_temp['time'], format='%H:%M:%S').dt.time.astype('str')
        df_temp['datetime'] = pd.to_datetime(df_temp['date'] + ' ' + df_temp['time'], errors='coerce')
        df_temp = df_temp.drop(['time','date'], axis=1)
        df_temp = df_temp.melt(id_vars='datetime', var_name='area', value_name='power')
        
        df_list.append(df_temp)
    
    result_df = pd.concat(df_list)
    return result_df

# Function to retrieve power weather data
def get_weatherData(end_date, lookback=False):
    if lookback:
        end_date = datetime.now() + timedelta(days=1)
        start_date = datetime.now() - timedelta(days=lookback)
        dates = pd.date_range(start=start_date, end=end_date, inclusive='left')
    else:
        dates = [datetime.strptime(date, '%Y/%m/%d').date()]

    df_list = []

    for date in stqdm(dates, desc="下載 weatherData 中 "):
        date_string = date.strftime('%Y/%m/%d')
        formatted_date = "/".join(str(int(x)) for x in date_string.split("/"))

        payload = {'date': formatted_date}
        r = requests.get('https://purbao.lass-net.org/weatherData', params=payload)

        df_temp = pd.DataFrame(r.json())
        df_temp = df_temp.rename(columns={'_id':'time'})
        df_temp['date'] = formatted_date
        df_temp['time'] = pd.to_datetime(df_temp['time'], format='%H:%M:%S').dt.time.astype('str')
        df_temp['datetime'] = pd.to_datetime(df_temp['date'] + ' ' + df_temp['time'], errors='coerce')
        df_temp = df_temp.drop(['time','date'], axis=1)
        df_temp['h'] = df_temp['h'].astype('float')
        df_temp = df_temp.pivot_table(index='datetime',  values=['t','h','wSpeed','wDir'], aggfunc='median')

        df_list.append(df_temp)

    result_df = pd.concat(df_list)
    return result_df

# Functions to plot different types of charts using plotly
def plotly_linechart(data, columns):
    # This function creates and returns a line chart.
    fig = go.Figure()
    fig.update_layout(autosize=False, width=1000, height=500)

    if isinstance(columns, str):
        columns = [columns]  # Convert single column string to list

    for column in columns:
        fig.add_trace(go.Scatter(x=data.index, y=data[column], mode='lines', name=column))

    return fig

def plotly_areachart(data, columns):
    # This function creates and returns an area chart.
    fig = go.Figure()
    fig.update_layout(autosize=False, width=1000, height=500)

    if isinstance(columns, str):
        columns = [columns]  # Convert single column string to list

    for column in columns:
        fig.add_trace(go.Scatter(x=data.index, y=data[column], mode='lines', stackgroup='one', name=column, fill='tozeroy'))

    return fig

def plotly_barchart(data, columns):
    # This function creates and returns a bar chart.
    fig = go.Figure()
    fig.update_layout(autosize=False, width=1000, height=500)

    if isinstance(columns, str):
        columns = [columns]  # Convert single column string to list

    for column in columns:
        fig.add_trace(go.Bar(x=data.index, y=data[column], name=column))

    fig.update_layout(barmode='stack')

    return fig

# Get the current date and time
date = datetime.now().strftime('%Y/%m/%d')
time = datetime.now().strftime('%H:%M:%S')

# Define the app layout and logic
st.title("台灣能源的數據儀表板")
st.markdown("""
    
    本儀表板提供電力消耗數據的可視化。它包括折線圖、面積圖和柱狀圖，用於表示電力負載、發電比例和尖峰用電比例。
    
    """)

# Create a slider to control the number of days to look back
lookback = st.sidebar.slider("選擇 lookback 天數", 1, 7, 7)

# Display the selected number of days to look back
st.sidebar.write(f"選擇了 {lookback} 天")

# Get power load and power ratio data
weatherData = get_weatherData(date, lookback=1)
powerLoad = get_powerLoad(date, lookback)
powerRatio = get_powerRatio(date, lookback)

# Convert data to a more convenient format for plotting
powerLoad = powerLoad.pivot_table(index='datetime',columns='area',values='load')
powerRatio = powerRatio.pivot_table(index='datetime',columns='area',values='power')

# Map column names to more readable labels
column_mapping = {
    'pumpGen': '抽蓄發電',
    'solar': '太陽能',
    'wind': '風力',
    'hydro': '水力',
    'diesel': '輕油',
    'oil': '重油',
    'ippLng': '民營-燃氣',
    'lng': '燃氣',
    'ippCoal': '民營-燃煤',
    'coGen': '汽電共生',
    'coal': '燃煤',
    'nuclear': '核能',
    'north': '北部用電量',
    'central': '中部用電量',
    'south': '南部用電量',
    'east': '東部用電量',
    't': '溫度',
    'h': '相對溼度',
    'wSpeed': '風速',
    'wDir': '風向',
}

# Rename columns in powerLoad and powerRatio for readability
powerLoad = powerLoad.rename(columns=column_mapping)
powerRatio = powerRatio.rename(columns=column_mapping)
weatherData = weatherData.rename(columns=column_mapping)

# Calculate total power load by summing up load for all areas
powerLoad['總用電量'] = powerLoad[['中部用電量', '東部用電量', '北部用電量', '南部用電量']].sum(axis=1)

# Prepare weather data
present_weather = weatherData.iloc[-1]
baseline_weather = weatherData.iloc[-2]
delta_weather = round(present_weather - baseline_weather,2)

# Define columns for Streamlit dashboard
col1, col2, col3 = st.columns(3)


# Define metrics for each column
col1.metric("Temperature", present_weather['溫度'].astype('str')+"°C", delta_weather['溫度'].astype('str')+"°C")
col2.metric("Wind", present_weather['風速'].astype('str')+" mph", delta_weather['風速'].astype('str')+" mph")
col3.metric("Humidity", (present_weather['相對溼度']*100).astype('str')+"%", (delta_weather['相對溼度']*100).astype('str')+"%")

# Plot total power load over time using line chart
fig1 = plotly_linechart(powerLoad, ['總用電量'])
st.plotly_chart(fig1)

# Plot power ratios over time for each area using an area chart
fig4 = plotly_areachart(powerRatio, powerRatio.columns)
st.plotly_chart(fig4)