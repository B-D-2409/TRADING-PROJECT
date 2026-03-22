#%%
import numpy as np
from scipy import stats
import datetime
import pandas as pd
import math
from utils.company_data import nd_timeseries, nd_div

# momentum score function
def momentum_score(ts):

    # Make a list of consecutive numbers
    x = np.arange(len(ts)) 
    # Get logs
    log_ts = np.log(ts) 
    # Calculate regression values
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, log_ts)
    
    # Използваме type: ignore, за да заглушим фалшивите аларми на Pylance
    annualized_slope = ((math.exp(float(slope)) ** 52) - 1) * 100  # type: ignore
    
    # Adjust for fitness
    score = annualized_slope * (float(r_value) ** 2)  # type: ignore

    return score

def get_buys_and_sells(symbols, index, indexfilter, end, freq, turnover_avg, highwindow, stopwindow, indexstop, tightstop):
    # initialise lists for dataframe
    closes = []
    volume = []
    turnover = []
    highs = []
    lows = []
    twowkh = []
    wkh = []
    fromhigh = []
    momo_scores = []
    dividends = []
    omit = []

    start = end - datetime.timedelta(days=2*365)

    for stock in symbols:
        try:
            ticker = stock + '.au'
            # collect data from norgate
            df = nd_timeseries(ticker, start, end, freq)
            closes.append(df['Close'].iloc[-1])
            volume.append(df['Volume'][-turnover_avg:].mean())
            turnover.append(df['Turnover'][-turnover_avg:].mean())
            temphigh = df['High'][-highwindow:]
            highs.append(temphigh[:-1].max()) # exclude last bar
            templow = df['Low'][-stopwindow:]
            lows.append(templow[:-1].min()) # exclude last bar
            twowkh.append(df['High'][-indexstop:].max())
            wkh.append(df['High'].iloc[-1])
            fromhigh.append(df['Close'].iloc[-1]/df['High'][-indexstop:].max() - 1)
            momo_scores.append(momentum_score(df['Close'][-highwindow:]))
            dividends.append(nd_div(ticker, start, end).iloc[-1])

        except ValueError:
            try:
                ticker = stock + 'DA.au'
                # ТУК БЕШЕ ИЗТРИТО freq ПО ПОГРЕШКА - ВЪРНАТО Е!
                df = nd_timeseries(ticker, start, end, freq) 
                closes.append(df['Close'].iloc[-1])
                volume.append(df['Volume'][-turnover_avg:].mean())
                turnover.append(df['Turnover'][-turnover_avg:].mean())
                temphigh = df['High'][-highwindow:]
                highs.append(temphigh[:-1].max()) # exclude last bar
                templow = df['Low'][-stopwindow:]
                lows.append(templow[:-1].min()) # exclude last bar
                twowkh.append(df['High'][-indexstop:].max())
                wkh.append(df['High'].iloc[-1])
                fromhigh.append(df['Close'].iloc[-1]/df['High'][-indexstop:].max() - 1)
                momo_scores.append(momentum_score(df['Close'][-highwindow:]))
                dividends.append(nd_div(ticker, start, end).iloc[-1])
                        
            except:
                omit.append(stock)
                continue

    symbols = [element for element in symbols if element not in omit]

    df = pd.DataFrame({'Symbol':symbols,'Close':closes,'Volume':volume,'Turnover':turnover,'High':highs,'Low':lows,'2 Week High':twowkh,'Week High':wkh,'From High':fromhigh,'Momentum Score':momo_scores, 'Dividend':dividends})

    df.set_index('Symbol',inplace=True)

    # dataframe for index filter
    index_df = nd_timeseries(index, start, end, freq)
    index_df['MA'] = index_df['Close'].rolling(window=indexfilter).mean()

    # Compare only the latest bar's close vs MA (not the entire Series)
    if index_df['Close'].iloc[-1] <= index_df['MA'].iloc[-1]:
        buydf = pd.DataFrame()
        selldf = df.loc[df['Close'] <= df['2 Week High'] * (1 - tightstop)]
    else:
        buydf = df.loc[df['Close'] >= df['High']].sort_values(by='Momentum Score', ascending=False)
        selldf = df.loc[df['Close'] <= df['Low']].sort_values(by='Momentum Score', ascending=False)
    
    return buydf, selldf