#%%
import numpy as np
from scipy import stats
import datetime
import pandas as pd

from utils.file_io import read_in_data
from utils.company_data import fundamental_data, nd_timeseries, nd_div, orderPriceRounding



# momentum score function
def momentum_score(ts):
    """
    Input:  Price time series.
    Output: Annualized exponential regression slope, 
            multiplied by the R2
    """
    # Make a list of consecutive numbers
    x = np.arange(len(ts)) 
    # Get logs
    log_ts = np.log(ts) 
    # Calculate regression values
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, log_ts)
    # Annualize percent
    annualized_slope = (np.power(np.exp(slope), 52) - 1) * 100
    #Adjust for fitness
    score = annualized_slope * (r_value ** 2)

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

            dividends.append(nd_div(ticker, start, end, freq).iloc[-1])

        except ValueError:
            
            try:
                ticker = stock + 'DA.au'
                
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
        
                dividends.append(nd_div(ticker, start, end, freq).iloc[-1])
                        
            except:
                # symbols = symbols.remove(stock)
                omit.append(stock)
                # print('Hi, there seems to be an issue with this line of code above. Cant assign the removal of an item to the variable. Ive commented out the offending line. Do the SMALL CAP UNC OMIT METHOD')
                continue

    symbols = [element for element in symbols if element not in omit]

    df = pd.DataFrame({'Symbol':symbols,'Close':closes,'Volume':volume,'Turnover':turnover,'High':highs,'Low':lows,'2 Week High':twowkh,'Week High':wkh,'From High':fromhigh,'Momentum Score':momo_scores, 'Dividend':dividends})

    df.set_index('Symbol',inplace=True)

    # dataframe for index filter
    index_df = nd_timeseries(index, start, end, freq)
    index_df['MA'] = index_df['Close'].rolling(window=indexfilter).mean()

    if index_df['Close'] <= index_df['MA']:
        buydf = pd.DataFrame()
        selldf = df.loc[df['Close'] <= df['2 Week High'] * (1 - tightstop)]
    else:
        buydf = df.loc[df['Close'] >= df['High']].sort_values(by='Momentum Score', ascending=False)
        selldf = df.loc[df['Close'] <= df['Low']].sort_values(by='Momentum Score', ascending=False)
    
    return buydf, selldf


def check_sells(positions, selldf):

    positions_to_sell = [pos for pos in positions[:3] if pos in selldf.index]

    return positions_to_sell

def update_portfolio_sells(positions_to_sell, trades):

    if len(positions_to_sell) == 0:
        return trades
    else:
        for sym in positions_to_sell:
            mask = (trades['Code:'] == f"{sym}.ASX") & (trades['Trade:'] == "Open")

            # Update Ex. Date: to today's date
            trades.loc[mask, 'Ex. Date:'] = datetime.date.today().strftime('%Y-%m-%d') # NEED TO FIDDLE WITH THIS DEPENDING ON THE TIME/WAY WE RUN IT

            # Replace other columns with "-"
            cols_to_replace = ['Ex. Price:', '% chg:', 'Profit:', '% Profit:']
            trades.loc[mask, cols_to_replace] = "-"








































def process_signals(strat_name, index_sym, frequency, highwindow, stopwindow, indexfilter, indexstop, fromhighrtn, maxpos, turnover_avg, nav, date, ed):

    last_sunday = date
    olddf = read_in_data('large_cap/live_sheets/', f"{last_sunday}-companies_in_portfolio")
    # olddf = pd.read_csv('live_sheets/2025-01-19-companies_in_portfolio.csv')

    # update data for positions
    updated_data = []
    for _, row in olddf.iterrows():
        updated_data.append(fundamental_data(row['Code:']))
    olddf_updated = pd.DataFrame(updated_data,columns=olddf.columns)
    
    if strat_name == 'large_cap':
        uni_sym = 'xjo'
        symbols = read_in_data('../SMAs/watchlists/', uni_sym)
        symbols = [symbols.columns[0]] + symbols[symbols.columns[0]].tolist()
    elif strat_name == 'mid_cap':
        uni_sym = 'xao'
        symbols = read_in_data('../SMAs/watchlists/', uni_sym)
        symbols = [symbols.columns[0]] + symbols[symbols.columns[0]].tolist()
    elif strat_name == 'income':
        xjo = read_in_data('../SMAs/watchlists/', 'xjo')
        xjo = [xjo.columns[0]] + xjo[xjo.columns[0]].tolist()
        xao = read_in_data('../SMAs/watchlists/', 'xao')
        xao = [xao.columns[0]] + xao[xao.columns[0]].tolist()
        symbols = [s for s in xao if s not in xjo]


    # time period for data collection
    end = ed
    # end='2025-05-04'
    start = datetime.datetime.now() - datetime.timedelta(days=2*365)

    # frequency of data
    freq = frequency

    # weights
    w = 1/maxpos

    # initialise lists for dataframe
    data = [] # for sheet output
    # for old style
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
    # print('____________________________________________________________________________________________________________')
    for stock in symbols:
        
        try:
            
            ticker = stock + '.au'
            
            # collect company data from norgate
            data.append(fundamental_data(stock + '.ASX'))
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
            dividends.append(nd_div(ticker, start, end, freq).iloc[-1])
            # print(closes)

        except ValueError:
            
            try:
                ticker = stock + 'DA.au'
                
                # collect company data from norgate
                data.append(fundamental_data(stock + '.ASX'))
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
                dividends.append(nd_div(ticker, start, end, freq).iloc[-1])
                        
            except:
                symbols = symbols.remove(stock)
                continue

    df = pd.DataFrame(data,
                      columns = [
                        "Name:", "Code:", "Sector:", "Last Price:", "52-Week High:", "52-Week Low:", "Market Cap:", "Franking Level:", "Business Summary:",
                        "P/E Ratio:", "Dividend Yield:", "P/S Ratio:", "P/FCF Ratio:",
                        "Net Debt:", "Debt-to-Equity Ratio:", "Current Ratio:", "Free Cash Flow:", "Net Profit Margin:",
                        "Revenue Growth (3-Year CAGR):", "EPS Growth (3-Year CAGR):", "ROE:"                     
                      ])
    df['Symbol']=symbols
    df['Close']=closes
    df['Volume']=volume
    df['Turnover']=turnover
    df['High']=highs
    df['Low']=lows
    df['2 Week High']=twowkh
    df['Week High']=wkh
    df['From High']=fromhigh
    df['Momentum Score']=momo_scores
    df['Dividend']=dividends

    # df.set_index('Symbol'
    # inplace=True)

    # dataframe for index filter
    index_df = nd_timeseries(index_sym, start, end, freq)
    index_df['MA'] = index_df['Close'].rolling(window=indexfilter).mean()

    # read in positions
    positions = olddf_updated.copy()

    # initialise lists for email
    buylist = []
    selllist = []
    selltype = []
    pos_closes = [] # add close price to positions dataframe
    stops = [] # add stop to positions dataframe
    twh = []
    pos_div = []
    # print('____________________________________________________________________________________________________________')
    # ignore the following suffixes
    for position in positions['Code:'].values:
        # position = position[:3]       
        # 40wk low stop
        stops.append(round(df.loc[df[df['Code:']==position].index.values]['Low'].values[0],2))
        twh.append(round(df.loc[df[df['Code:']==position].index.values]['Week High'].values[0] , 4))
        pos_closes.append(round(df.loc[df[df['Code:']==position].index.values]['Close'].values[0],2))
        # pos_div.append(df.loc[position]['Dividend'])
        if df.loc[df[df['Code:']==position].index.values]['Close'].values[0] <= df.loc[df[df['Code:']==position].index.values]['Low'].values[0]:
            selllist.append(position) 
            selltype.append('Trend Stop')
        # index filter 10% from 2 week high stop
        elif index_df['Close'].iloc[-1] < index_df['MA'].iloc[-1]:
            stops.pop() # remove previous stop
            stops.append(round(df.loc[df[df['Code:']==position].index.values]['Week High'].values[0]*0.9,2))
            if df.loc[df[df['Code:']==position].index.values]['From High'].values[0] <= fromhighrtn:
                selllist.append(position)
                selltype.append('Momentum Stop')

    # positions['Dividend'] = pos_div
    positions['Close'] = pos_closes
    positions['Stop'] = stops
    positions['Week High'] = twh
    # positions = positions.drop(positions[positions['Position'] == 0].index.values.tolist())

    # reset dataframe
    # df = pd.DataFrame({'Symbol':symbols,'Close':closes,'Volume':volume,'Turnover':turnover,'High':highs,'Low':lows,'From High':fromhigh,'Momentum Score':momo_scores})

    buydf = df.loc[df['Close'] >= df['High']].sort_values(by='Momentum Score', ascending=False)
    selldf = df.loc[df['Close'] <= df['Low']].sort_values(by='Momentum Score', ascending=False)
    # print('____________________________________________________________________________________________________________')
    # time since last 52 week high and rsi
    numshares = pd.DataFrame(columns = ['Symbol', 'Shares to Buy'])
    for ticker in buydf['Symbol']:
        # print(ticker)
        try:
            
            symbol = ticker + '.au'
            # print(ticker)
            # print(start)
            # print(end)
            # print(freq)
            data = nd_timeseries(symbol, start, end, freq)

            # print(data)
            data['20wkhigh'] = data['Close'].rolling(window = highwindow).max()
            rmlag = lambda xs: np.argmax(xs[::-1])
            data['days_since_high'] = data['Close'].rolling(window = highwindow).apply(func = rmlag)
            # print(((nav * w)/(buydf.loc[buydf['Symbol']==ticker].Close.values[0])))
            # print(buydf.loc[buydf['Symbol'] == ticker])
            ns = ((nav * w)/(buydf.loc[buydf['Symbol']==ticker].Close.values[0]))
            print(ns)
            print(ticker)
            nsdf = pd.DataFrame({'Symbol':[ticker], 'Shares to Buy':[ns]})
            print(nsdf)
            numshares = pd.concat([numshares, nsdf], ignore_index=True)
            print(numshares)
        
        except:
            
            try:
                
                symbol = ticker + 'DA.au'
                data = nd_timeseries(symbol, start, end, freq)
                data['20wkhigh'] = data['Close'].rolling(window = highwindow).max()
                rmlag = lambda xs: np.argmax(xs[::-1])
                data['days_since_high'] = data['Close'].rolling(window = highwindow).apply(func = rmlag)
                numshares = pd.concat(numshares, pd.DataFrame({'Symbol':ticker, 'Shares to Buy':((nav * w)/(buydf.loc[buydf['Symbol']==ticker].Close.values[0]))}), ignore_index=True)

            except:
                continue
            
            
    buydf = pd.merge(buydf, numshares, on = 'Symbol') # add shares to buy to buydf

    # remove positions we already have
    holding = positions['Code:'].values # current holdings
    buy = buydf['Symbol'].values # 52wk highs
    duplicates = [s for s in buy if s in holding] # duplicated
    for stock in duplicates: # remove duplicates from buydf
        buydf = buydf.drop(buydf[buydf['Symbol'] == stock].index.values[0])

    activitydf = pd.DataFrame()

    if index_df['Close'].iloc[-1] < index_df['MA'].iloc[-1]: # index filter triggered
        market_state = 'The momentum filter has been activated, indicating the market is no longer trending.'
    else:
        market_state = 'The momentum filter is off, indicating the market is continuing to trend.'

    # to buy
    if index_df['Close'].iloc[-1] < index_df['MA'].iloc[-1]: # index filter triggered
        pass
    elif len(positions) == maxpos: # max size
        pass
    elif maxpos - len(positions) >= len(buydf):
        activitydf = pd.concat([activitydf, buydf], ignore_index=True)
    else:
        open_pos = maxpos - len(positions)
        to_buy = len(buydf)
        buydf = buydf[0:open_pos]
        activitydf = pd.concat([activitydf, buydf], ignore_index=True)
        
    if len(activitydf) == 0:
        pass
    else:
        # activitydf.columns = ['Symbol', 'Close', 'Shares']
        activitydf.loc[:, 'Shares:'] = round(activitydf['Shares to Buy'], 0)
        activitydf.loc[:,'Action:'] = ['BUY'] * len(activitydf)
        activitydf.loc[:,'Stop Type:'] = ['Not Applicable'] * len(activitydf)
        activitydf.loc[:,'Stop Type:'] = ['Not Applicable'] * len(activitydf)
        activitydf.loc[:,'Stop Price:'] = activitydf['Low'].apply(orderPriceRounding)
        activitydf.loc[:,'Stop Price:'] = activitydf['Stop Price:'].apply(lambda x: f"${x}")
        activitydf.loc[:,'Buy Trigger Reason:'] = activitydf['Code:'].apply(lambda x: f"{x[:3]} has closed above its previous 20 week high and is exhibiting momentum.")
        activitydf = activitydf.drop(columns=['Volume', 'Turnover', 'High', 'Low', 'From High', 'Momentum Score'])
        activitydf.loc[:, 'Market State:'] = [market_state] * len(activitydf)

    # send sell df
    to_sell = pd.DataFrame()
    for stock in selllist:
        to_sell = to_sell.append(positions.loc[positions[positions['Code:']==stock].index.values])

    to_sell.loc[:, 'Stop Type:'] = selltype
    
    if len(to_sell) == 0:
        pass
    else:
        to_sell = to_sell.drop(columns = ['Close', 'Stop', 'Week High'])
        # to_sell = to_sell.reset_index()
        # to_sell.columns = ['Symbol', 'Close', 'Shares']
        to_sell.loc[:, 'Action:'] = ['SELL'] * len(to_sell)
        to_sell.loc[:, 'Stop Price:'] = ['Not Applicable'] * len(to_sell)
        to_sell.loc[:, 'Buy Trigger Reason:'] = ['Not Applicable'] * len(to_sell)
        to_sell.loc[:, 'Market State:'] = [market_state] * len(to_sell)
        activitydf =  activitydf.append(to_sell)

    # if len(activitydf) != 0:
    #     activitydf = activitydf.set_index(activitydf['Symbol'])
    #     activitydf = activitydf.drop(columns=['Symbol'])
    # else:
    #     pass

    positions.drop(columns=['Close', 'Stop', 'Week High'], inplace=True)

    if len(to_sell) != 0:
        for share in selllist:
            positions = positions.drop(positions[positions['Code:']==share].index.values[0])
    elif len(activitydf) != 0:
        if len(activitydf[activitydf['Action:']=='BUY']) != 0:
            buydf.drop(columns=['Symbol', 'Close', 'Volume', 'Turnover', 'High', 'Low', '2 Week High',
                                'Week High', 'From High', 'Momentum Score', 'Dividend', 'Shares to Buy'],
                                inplace=True)
            for index, row in buydf.iterrows():
                positions.loc[len(positions)] = row
    else:
        pass


    desired_columns = ['Code:','Last Price:','Action:','Stop Type:','Stop Price:','Buy Trigger Reason:','Market State:','Name:','Sector:','Last Price:',
                       '52-Week High:','52-Week Low:','Market Cap:','Franking Level:','Business Summary:','P/E Ratio:','Dividend Yield:','P/S Ratio:',
                       'P/FCF Ratio:','Net Debt:','Debt-to-Equity Ratio:','Current Ratio:','Free Cash Flow:','Net Profit Margin:',
                       'Revenue Growth (3-Year CAGR):','EPS Growth (3-Year CAGR):','ROE:']
    if activitydf.empty:
        activitydf = pd.DataFrame(columns=desired_columns)
    else:
        activitydf = activitydf[desired_columns]
    
    return activitydf, positions