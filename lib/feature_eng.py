import sys
print(sys.version)

import pandas as pd
import numpy as np
import pickle
import cleaning as cl

query = "SELECT date, temp_avg, dp_avg, humid_avg, ws_avg, press_avg, precip FROM daily ORDER BY date"
wdf = cl.get_df_from_sql(query)


wdf = pd.read_pickle('../src/EWRweather.pickle')

humdf = wdf[['date', 'humid_avg']]
humdf = humdf.set_index('date')
humdf.shift(-1)
humdf.reset_index(inplace=True)
humdf.rename(columns={'humid_avg': 'humid_avg_lag1'}, inplace=True)

wdf.merge(humdf, on='date')
def prep_wdf():
    ###################### Change the pickle to the clenaed pickle name
    wdf = pd.read_pickle('../src/EWRweather.pickle')
    wdf.set_index('date')
    lags = wdf.drop(columns='raining')
    lags = lags.shift(1)
    wdf.raining.merge(lags, left_index=True, right_index=True)

    
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


########## Not used? 
def rolling_difference_mean(dataset, window):
    """
    Creates rolling difference between the current value and the mean
    """
    return dataset-dataset.rolling(window=window).mean()

def ma_shifts(window, lags, wdf, col_name):
    """
    Calculates the rolling average based on windowsize.
    Generates the lagged differences between the target and lags

    args: 
        window (int): Size of window to take moving average
        l (int): Days of lag
        wdf (DataFrame): weather dataframe
        col_name (str): name of column to create lag differences
    returns: 
        ma_df (DataFrame): Dataframe with new lagged features
    """
    ma_df = wdf[[col_name]]
    # create rolling average
    roll_col = col_name + '_roll_' + str(window)
    ma_df.loc[:,roll_col] = ma_df.loc[:, col_name].rolling(window=window).mean()
    col_err = col_name + '_error'
    ma_df[col_err] = ma_df[col_name] - ma_df[roll_col]
    # get diff
    # lag columns 
    ma_df = ma_df.assign(**{col_err+'_lag_'+str(lag_n): ma_df[col_err].shift(lag_n) for lag_n in lags}) 
    return ma_df

def leading_trends(window, lags, wdf, col_name):
    """
    Generates the leading trend based on the number of days lagged

    Similar to the ma_shifts method with minor change.  
    Calculates the rolling average based on windowsize.
    Generates the lagged differences between the target and lags
    Sums the differences to get the trend of the change in the last 
    args: 
        window (int): Size of window to take moving average
        l (int): Days of lag
        wdf (DataFrame): weather dataframe
        col_name (str): name of column to create lag differences
    returns: 
        ma_df (DataFrame): Dataframe with new lagged features
    """
    ma_df = wdf[[col_name]]
    # create rolling average
    roll_col = col_name + '_roll_' + str(window)
    ma_df.loc[:,roll_col] = ma_df.loc[:, col_name].rolling(window=window).mean()
    col_err = col_name + '_error'
    ma_df[col_err] = ma_df[col_name] - ma_df[roll_col]
    # get diff
    # lag columns 
    ma_df = ma_df.assign(**{col_err+'_lag_'+str(lag_n): ma_df[col_err].shift(lag_n) for lag_n in lags}) 
    return ma_df

def feat_eng_v1():
    wdf = cl.get_cleaned_df()
    wdf.sort_values(by='date', ascending=True, inplace=True)
    
    wdf['press_delta'] = wdf.press_avg.diff()

    # set aside 2019 and 2020 data as holdout sets 
    wdf = wdf[wdf.year<2019].copy(deep=True)
    
    df = ma_shifts(3, [1,5,7,10], wdf, 'temp_kelvin')
    df = df.merge(ma_shifts(7, [1,2,3], wdf, 'press_avg'), left_index=True, right_index=True, )
    df = df.merge(ma_shifts(7, [1,2,3], wdf, 'humid_avg'), left_index=True, right_index=True, )
    df = df.merge(wdf[['raining', 'year', 'month']], left_index=True, right_index=True)

    df.dropna(inplace=True)

    return df

def feat_eng_v2():
    wdf = cl.get_cleaned_df()
    wdf.sort_values(by='date', ascending=True, inplace=True)
    
    wdf['press_delta'] = wdf.press_avg.diff()
    wdf['press_delta'] = (wdf['press_delta']>0).astype(int)


    wdf['temp_trend'] = ma_shifts(3, range(1,10), wdf, 'temp_kelvin').iloc[:,2:].sum(axis=1)
    wdf['press_trend'] = ma_shifts(3, range(1,10), wdf, 'press_avg').iloc[:,2:].sum(axis=1)
    wdf['humid_trend'] = ma_shifts(3, range(1,10), wdf, 'humid_avg').iloc[:,2:].sum(axis=1)
    wdf.drop(columns='date', inplace=True)
    wdf.dropna(inplace=True)

    return wdf
# newtemp = Yesterday's rolling(10) average + C1 * (Lag1 error) + C2*(lag2 error)
# n day diff
# n day rolling average minus prev day val
# Convert temp into Kelvin
# Use Autoregression on humidity time series to predict the next humidity
# features would be Humidity rolling diff, predicted humidity from trend
# 
##################
# Linear Model function. Rolling window of 10 days. 
# Average and lagged features for ten days passed into Linear Regression 

if __name__ == "__main__":
    wdf = cl.get_cleaned_df()
    wdf.sort_values(by='date', ascending=True, inplace=True)
    
    wdf['press_delta'] = wdf.press_avg.diff()
    wdf['press_delta'] = (wdf['press_delta']>0).astype(int)

    # set aside 2019 and 2020 data as holdout sets 
    wdf = wdf[wdf.year<2019].copy(deep=True)
    wdf['temp_trend'] = ma_shifts(5, range(1,6), wdf, 'temp_kelvin').iloc[:,2:].sum(axis=1)
    wdf['press_trend'] = ma_shifts(5, range(1,6), wdf, 'press_avg').iloc[:,2:].sum(axis=1)
    wdf['humid_trend'] = ma_shifts(5, range(1,6), wdf, 'humid_avg').iloc[:,2:].sum(axis=1)
    wdf.drop(columns='date', inplace=True)