import pandas as pd
from utils import read_excel_sheet
from utils import nd_timeseries


def update_market_performance(df, market_sym, end_date, freq):

    prev_equity = df.iloc[-1]['Equity']
    
    market_data = nd_timeseries(market_sym, freq, end_date)
    new_row = market_data.iloc[-1][['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Turnover']]
    
    ret = new_row['Close'] / prev_equity
    new_row['Equity'] = prev_equity * ret

    df.loc[len(df)] = new_row

    return df


