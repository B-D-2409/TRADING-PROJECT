import pandas as pd
import datetime
import numpy as np
from company_data import nd_timeseries


def update_trade_prices(df, cash, comms, end_date):
    
    entries = df[df['Price:']=='-']
    exits = df[df['Ex. Price:']=='-']

    if not entries.empty:
        for index, row in entries:
            symbol = row['Code:']
            prices = nd_timeseries(symbol, 'D', end_date)
            open_price = prices.iloc[-1]['Open']
            cash -= row['Shares:'] * open_price - row['Shares:'] * open_price * comms
            df.iloc[index, 'Price:'] = open_price
    
    if not exits.empty:
        for index, row in entries:
            symbol = row['Code:']
            prices = nd_timeseries(symbol, 'D', end_date)
            open_price = prices.iloc[-1]['Open']
            cash += row['Shares:'] * open_price - row['Shares:'] * open_price * comms
            df.iloc[index, 'Ex. Price:'] = open_price
    
    return df, cash


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

    # check if any entry prices are to be confirmed and fill them in
    missing_entry = new_tradelist[new_tradelist['Price:'].isnull()]
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

    # check if any exit prices are to be confirmed and fill them in
    missing_exit = new_tradelist[new_tradelist['Ex. Price:'].isnull()]
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

    # change sold positions from open long to open and edit exit price to nan
    sold_sym = activitydf[activitydf['Action:']=='SELL']['Code:'].to_list()
    sol_pos = new_tradelist[(new_tradelist['Trade:']=='Open Long') & (new_tradelist['Code:'].isin(sold_sym))]
    idx = sol_pos.index.values
    new_tradelist.loc[idx, 'Ex. Price:'] = np.nan
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

    buydf = pd.DataFrame(
        {
        'Code:':buy_sym,
        'Trade:':['Open Long'] * len(buy_sym),
        'Date:': [buydate_str] * len(buy_sym),
        'Price:': [np.nan] * len(buy_sym),
        'Ex. Date:': [buydate_str] * len(buy_sym),
        'Ex. Price:': [np.nan] * len(buy_sym),
        '% chg:': [np.nan] * len(buy_sym),
        'Profit:': [np.nan] * len(buy_sym),
        '% Profit:': [np.nan] * len(buy_sym),
        'Shares:':numshares
    })
    
    new_tradelist = pd.concat([new_tradelist, buydf], ignore_index=True)
    new_tradelist.sort_values(by=['Trade:','Date:','Code:'], ascending=[False, True, True], inplace=True)

    return new_tradelist
