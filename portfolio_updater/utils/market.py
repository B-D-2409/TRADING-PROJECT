import pandas as pd
from utils import read_excel_sheet
from utils import nd_timeseries


def update_market_performance(df, market_sym, end_date, freq):

    prev_equity = df.iloc[-1]['Equity']
    
    market_data = nd_timeseries(market_sym, freq, end_date)
    new_row = market_data.iloc[-1][['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Turnover']]
    
    # Calculate percentage return of the index from the previous bar
    prev_close = market_data.iloc[-2]['Close']
    ret = new_row['Close'] / prev_close  # return multiplier (e.g. 1.01 = +1%)
    # Apply that return to the previous equity to grow the equity curve
    new_row['Equity'] = prev_equity * ret

    df.loc[len(df)] = new_row

    return df


