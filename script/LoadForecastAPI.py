# Import necessary libraries
import pandas as pd
import numpy as np
import datetime
import requests
import os
import urllib

# Set directory path to save the data and get current date in 'YYYYMMDD' format
path_data = r'C:\Users\patri\Taipower\data\forecast'
date = datetime.datetime.now().strftime('%Y%m%d')

# ======================== Downloading Weekly Load Forecast ========================

# Define the URL for the weekly load forecast
url_weekly_load = 'https://www.taipower.com.tw/d006/loadGraph/loadGraph/data/reserve_forecast.txt'

# Read the data from the URL
weekly_load_pred = pd.read_csv(url_weekly_load, encoding='big5',header=None)

# Drop any rows with missing values
weekly_load_pred = weekly_load_pred.dropna()

# Save the cleaned data to a CSV file
weekly_load_pred.to_csv(os.path.join(path_data, date+'_weekly_load_pred.csv'), encoding='utf8', index=False)


# ======================== Downloading Monthly Load Forecast ========================

# Define the URL for the monthly load forecast
url_monthly_load = 'https://www.taipower.com.tw/d006/loadGraph/loadGraph/data/reserve_forecast_month.txt'

# Read the data from the URL
monthly_load_pred = pd.read_csv(url_monthly_load,header=None)

# Drop any rows with missing values
monthly_load_pred = monthly_load_pred.dropna()

# Save the cleaned data to a CSV file
monthly_load_pred.to_csv(os.path.join(path_data, date+'_monthly_load_pred.csv'), encoding='utf8', index=False)


# ======================== Downloading Weekly Weather Forecast ========================

# Define the URL for the weekly weather forecast
url_weather = 'https://www.cwb.gov.tw/V8/C/W/County/MOD/wf7dayNC_NCSEI/ALL_Week.html'

# Send a GET request to the URL and store the response
r = requests.get(url_weather)

# Read the HTML table from the response
weatehr_pred = pd.read_html(r.text)[0]

# Clean and reformat the column headers
weatehr_pred.columns = weatehr_pred.columns.str.split('星期',expand=True).get_level_values(0)

# Melt the dataframe to long format
weatehr_pred = weatehr_pred.melt(id_vars=['縣市', '時間'], var_name='Date')

# Convert the date column to datetime format with current year
weatehr_pred['Date'] = pd.to_datetime(str(datetime.datetime.now().year)+'/'+weatehr_pred['Date'])

# Extract low and high temperatures from the value column
weatehr_pred['Temperature_low'] = weatehr_pred['value'].str.split(' |-',expand=True).iloc[:, 0].astype('float')
weatehr_pred['Temperature_high'] = weatehr_pred['value'].str.split(' |-',expand=True).iloc[:, 1].astype('float')

# Drop the original value column
weatehr_pred = weatehr_pred.drop('value',axis=1)

# Save the cleaned weather data to a CSV file
weatehr_pred.to_csv(os.path.join(path_data, date+'_daily_weather_pred.csv'), encoding='utf8', index=False)


# ======================== Downloading Zipped Weather Data ========================

# Define the URL for the zipped weather data
url_weather_zip = 'https://opendata.cwb.gov.tw/fileapi/v1/opendataapi/F-D0047-093?Authorization=rdec-key-123-45678-011121314&format=ZIP'

# Download the zipped data and save it to the specified directory
urllib.request.urlretrieve(url_weather_zip, os.path.join(path_data, date+'_weather.zip'))