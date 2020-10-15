import sys
print(sys.version)

import pandas as pd
import numpy as np
import pickle
import cleaning

query = "SELECT date, temp_avg, dp_avg, humid_avg, ws_avg, press_avg, precip FROM daily ORDER BY date"
wdf = cleaning.get_df_from_sql(query)


wdf = pd.read_pickle('src/EWRweather.pickle')

humdf = wdf[['date', 'humid_avg']]
humdf = humdf.set_index('date')
humdf.shift(-1)
humdf.reset_index(inplace=True)
humdf.rename(columns={'humid_avg': 'humid_avg_lag1'}, inplace=True)

wdf.merge(humdf, on='date')

def set_precip_level(thresh):
    """
    Sets the threshold on precipitation level to be considered rain
    args:
        df : (DataFrame) df with precipitation level
        thresh : (float) Sets the decimal threshold for how many inches of precipitation to consider it raining

    returns:
        df : (DataFrame) with new column with 1 or 0 for rain or no
    """

    wdf['raining'] = wdf.precip.map(lambda x: int(x > thresh))

def difference(dataset, lag=1):
    d = [(dataset[i] - dataset[i-lag]) for i in range(lag, len(dataset))]
    return d

def rolling_difference_mean(dataset, window):
    """
    Creates rolling difference between the current value and the mean
    """
    return dataset-dataset.rolling(window=window).mean()
# n day diff
# n day rolling average minus prev day val
# Convert temp into Kelvin
# Use Autoregression on humidity time series to predict the next humidity
# features would be Humidity rolling diff, predicted humidity from trend

test = pd.Series(np.linspace(0,100,101))