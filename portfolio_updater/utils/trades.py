import pandas as pd
import datetime
import numpy as np
from utils.company_data import nd_timeseries


def update_trade_prices(trades_df, current_cash, commissions, target_date):
    original_cols = trades_df.columns.tolist()
    norm_cols = {c.replace(':', '').strip().lower(): c for c in original_cols}

    def get_c(key): return norm_cols.get(key.lower())

    c_code = get_c('Code')
    c_trade = get_c('Trade')
    c_ex_price = get_c('Ex Price')
    c_price = get_c('Price')
    c_qty = get_c('Shares') if get_c('Shares') in trades_df.columns else get_c('Qty')
    c_ex_date = get_c('Ex. Date')
    c_sale_val = get_c('Sale value')

    for idx, row in trades_df.iterrows():
        symbol = str(row[c_code]).strip()
        if symbol == '-' or not symbol: continue
        
        ticker = symbol.split('.')[0] + '.au'
        price_data = nd_timeseries(ticker, target_date, 'D')
        
        if price_data is None or price_data.empty: continue
        
        open_price = price_data.iloc[-1]['Open']

        if row[c_trade] == 'Sell' and row[c_ex_price] == '-':
            trades_df.at[idx, c_ex_price] = open_price
            if c_ex_date: trades_df.at[idx, c_ex_date] = target_date
            
            shares = float(row[c_qty])
            sale_value = (shares * open_price) - commissions
            if c_sale_val: trades_df.at[idx, c_sale_val] = sale_value
            
            current_cash += sale_value
            trades_df.at[idx, c_trade] = 'Closed'

        elif row[c_trade] == 'Buy' and row[c_price] == '-':
            trades_df.at[idx, c_price] = open_price
            
            shares = float(row[c_qty])
            buy_value = (shares * open_price) + commissions
            current_cash -= buy_value
            trades_df.at[idx, c_trade] = 'Open'
            
    return trades_df, current_cash

def update_trade_list(tradelist, enddate, brokerage):

    new_tradelist = tradelist.copy()

    # update the prices and metrics for the open long positions
    open_pos = new_tradelist[new_tradelist['Trade:']=='Open Long']
    ex_price = []
    for index, row in open_pos.iterrows():
        prices = nd_timeseries(
            row['Code:'][:3] + '.au',
            sd = '2000-01-01',
            ed = enddate,
            freq='W'
        )
        p = prices.iloc[-1]['Close']
        ex_price.append(p)
    idx = open_pos.index.values
    new_tradelist.loc[idx, 'Ex. Price:'] = ex_price

    new_tradelist.loc[idx, '% chg:'] = new_tradelist.loc[idx, 'Ex. Price:'] / new_tradelist.loc[idx, 'Price:'] - 1
    # new_tradelist.loc[idx, 'Profit:'] = (new_tradelist.loc[idx, 'Ex. Price:'] - new_tradelist.loc[idx, 'Price:']) * new_tradelist.loc[idx, 'Shares:']
    new_tradelist.loc[idx, '% Profit:'] = new_tradelist.loc[idx, '% chg:'] - brokerage * 2
    new_tradelist.loc[idx, 'Profit:'] = new_tradelist.loc[idx, 'Price:'] * new_tradelist.loc[idx, 'Shares:'] * new_tradelist.loc[idx, '% Profit:']
    new_tradelist.loc[idx, 'Profit:'] = new_tradelist.loc[idx, 'Profit:'].apply(lambda x: round(x, 2))

    new_tradelist.loc[idx, '% chg:'] = new_tradelist.loc[idx, '% chg:'].apply(lambda x: f"{round(x*100, 2)}%")
    new_tradelist.loc[idx, '% Profit:'] = new_tradelist.loc[idx, '% Profit:'].apply(lambda x: f"{round(x*100, 2)}%")

    new_tradelist.loc[idx, 'Ex. Date:'] = enddate.strftime(format='%d/%m/%Y')
    
    return new_tradelist






def update_trade_list_all(tradelist, activitydf, equitydf, enddate, numpos):

    brokerage = 0.001
    new_tradelist = tradelist.copy()

    # Check if any entry prices are to be confirmed — sentinel is the string '-'
    missing_entry = new_tradelist[new_tradelist['Price:']=='-']
    entry_prices = []
    for index, row in missing_entry.iterrows():
        prices = nd_timeseries(
            row['Code:'][:3] + '.au',
            sd = '2000-01-01',
            ed = enddate,
            freq='W'
        )
        p = prices.iloc[-1]['Open']
        entry_prices.append(p)
        # print(p)
    idx = missing_entry.index.values
    # print(entry_prices)
    new_tradelist.loc[idx, 'Price:'] = entry_prices
    # new_tradelist.loc[idx, 'Price:'] = new_tradelist.loc[idx, 'Price:'].apply(orderPriceRounding)

    # Check if any exit prices are to be confirmed — sentinel is the string '-'
    missing_exit = new_tradelist[new_tradelist['Ex. Price:']=='-']
    exit_prices = []
    for index, row in missing_exit.iterrows():
        prices = nd_timeseries(
            row['Code:'][:3] + '.au',
            sd = '2000-01-01',
            ed = enddate,
            freq='W'
        )
        p = prices.iloc[-1]['Open']
        exit_prices.append(p)
    idx = missing_exit.index.values
    new_tradelist.loc[idx, 'Ex. Price:'] = exit_prices
    # new_tradelist.loc[idx, 'Ex. Price:'] = new_tradelist.loc[idx, 'Ex. Price:'].apply(orderPriceRounding)
    new_tradelist.loc[idx, '% chg:'] = new_tradelist.loc[idx, 'Ex. Price:'] / new_tradelist.loc[idx, 'Price:'] - 1
    # new_tradelist.loc[idx, 'Profit:'] = (new_tradelist.loc[idx, 'Ex. Price:'] - new_tradelist.loc[idx, 'Price:']) * new_tradelist.loc[idx, 'Shares:']
    new_tradelist.loc[idx, '% Profit:'] = new_tradelist.loc[idx, '% chg:'] - brokerage * 2
    new_tradelist.loc[idx, 'Profit:'] = new_tradelist.loc[idx, 'Price:'] * new_tradelist.loc[idx, 'Shares:'] * new_tradelist.loc[idx, '% Profit:']
    new_tradelist.loc[idx, 'Profit:'] = new_tradelist.loc[idx, 'Profit:'].apply(lambda x: round(x, 2))

    # update the prices and metrics for the open long positions
    open_pos = new_tradelist[new_tradelist['Trade:']=='Open Long']
    ex_price = []
    for index, row in open_pos.iterrows():
        prices = nd_timeseries(
            row['Code:'][:3] + '.au',
            sd = '2000-01-01',
            ed = enddate,
            freq='W'
        )
        p = prices.iloc[-1]['Close']
        ex_price.append(p)
    idx = open_pos.index.values
    new_tradelist.loc[idx, 'Ex. Price:'] = ex_price

    new_tradelist.loc[idx, '% chg:'] = new_tradelist.loc[idx, 'Ex. Price:'] / new_tradelist.loc[idx, 'Price:'] - 1
    # new_tradelist.loc[idx, 'Profit:'] = (new_tradelist.loc[idx, 'Ex. Price:'] - new_tradelist.loc[idx, 'Price:']) * new_tradelist.loc[idx, 'Shares:']
    new_tradelist.loc[idx, '% Profit:'] = new_tradelist.loc[idx, '% chg:'] - brokerage * 2
    new_tradelist.loc[idx, 'Profit:'] = new_tradelist.loc[idx, 'Price:'] * new_tradelist.loc[idx, 'Shares:'] * new_tradelist.loc[idx, '% Profit:']
    new_tradelist.loc[idx, 'Profit:'] = new_tradelist.loc[idx, 'Profit:'].apply(lambda x: round(x, 2))

    new_tradelist.loc[idx, '% chg:'] = new_tradelist.loc[idx, '% chg:'].apply(lambda x: f"{round(x*100, 2)}%")
    new_tradelist.loc[idx, '% Profit:'] = new_tradelist.loc[idx, '% Profit:'].apply(lambda x: f"{round(x*100, 2)}%")

    # Change sold positions from Open Long to Long; reset exit price to '-' sentinel
    sold_sym = activitydf[activitydf['Action:']=='SELL']['Code:'].to_list()
    sol_pos = new_tradelist[(new_tradelist['Trade:']=='Open Long') & (new_tradelist['Code:'].isin(sold_sym))]
    idx = sol_pos.index.values
    new_tradelist.loc[idx, 'Ex. Price:'] = '-'  # standardised sentinel
    new_tradelist.loc[idx, 'Trade:'] = 'Long'

    # add in new buys
    buy_sym = activitydf[activitydf['Action:']=='BUY']['Code:'].to_list()
    buydate = pd.to_datetime(enddate, format='%Y-%m-%d') + datetime.timedelta(days=1)
    buydate_str = buydate.strftime(format='%Y-%m-%d')
    numshares = []
    for sym in buy_sym:
        prices = nd_timeseries(
            sym[:3] + '.au',
            sd = '2000-01-01',
            ed = enddate,
            freq='W'
        )
        w = 1/numpos
        eq = equitydf.iloc[-1]['Portfolio Equity:']
        ns = (eq * w) / prices.iloc[-1]['Close']
        numshares.append(round(ns, 0))

    # New buy rows use '-' as sentinel for prices not yet filled (standardised)
    buydf = pd.DataFrame(
        {
        'Code:':buy_sym,
        'Trade:':['Open Long'] * len(buy_sym),
        'Date:': [buydate_str] * len(buy_sym),
        'Price:': ['-'] * len(buy_sym),      # pending entry price
        'Ex. Date:': [buydate_str] * len(buy_sym),
        'Ex. Price:': ['-'] * len(buy_sym),  # pending exit price
        '% chg:': ['-'] * len(buy_sym),
        'Profit:': ['-'] * len(buy_sym),
        '% Profit:': ['-'] * len(buy_sym),
        'Shares:':numshares
    })
    
    new_tradelist = pd.concat([new_tradelist, buydf], ignore_index=True)
    new_tradelist.sort_values(by=['Trade:','Date:','Code:'], ascending=[False, True, True], inplace=True)

    return new_tradelist
