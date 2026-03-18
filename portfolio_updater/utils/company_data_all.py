#%% 

import pandas as pd
import norgatedata as nd
from utils.company_data import *
import datetime

def get_stop_price(df, stopwindow):
    templow = df['Low'][-stopwindow:]
    stop = templow[:-1].min() # exclude last bar
    return stop
def company_data(symbol:str, stopwindow:int):
    """
    Inputs a symbol and collects name, sector, last price, 52wk range,
    market cap, franking level, business summary, p/e ratio, div yield, 
    p/s ratio, p/fcf ratio, net debt, debt/equity ratio, current ratio
    free cash flow, net profit margin, revenue growth, earnings growth,
    return on equity
    """
    try:
        ticker = symbol[:3] + '.au'
        # if ticker == 'SUN.au':
        #     ticker='SUNDD.au'
        company_name = nd.security_name(ticker)
        gics_sector = nd.classification_at_level(ticker, 'GICS', 'Name', 1)
        
        end = datetime.datetime.now()
        # end = '2024-12-29'
        start = datetime.datetime.now() - datetime.timedelta(days=2*365)
        
        # Last price
        prices = nd_timeseries(
            symbol=ticker, 
            # sd=start,
            ed=end,
            freq='W'
        )
        
        last_price = prices.iloc[-1]['Close']
        lp = f"${orderPriceRounding(last_price):.2f}" if last_price is not None else None

        # 52 week range
        high = f"${orderPriceRounding(prices['High'].rolling(window=52).max().iloc[-1])}"
        low = f"${orderPriceRounding(prices['Low'].rolling(window=52).min().iloc[-1])}"
        # range_52_week = f"${orderPriceRounding(low)} - ${orderPriceRounding(high)}" if high is not None and low is not None else None

        # stops
        sp = get_stop_price(prices, stopwindow)

        # Market cap
        market_cap, _ = nd.fundamental(ticker, 'mktcap')
        mc = f"${round(market_cap / 1000, 1)}B" if market_cap is not None else None

        # Franking
        franking_level, _ = nd.fundamental(ticker, 'FrankedPct')
        fl = f"{round(franking_level, 1)}%" if franking_level is not None else None

        # Summary
        business_summary = nd.business_summary(ticker)

        trailing_pe, _ = nd.fundamental(ticker, 'pebexclxor')
        tpe = f"{round(trailing_pe, 1)}x" if trailing_pe is not None else None

        dividend_yield, _ = nd.fundamental(ticker, 'divyield_curttm')
        dy = f"{round(dividend_yield, 1)}%" if dividend_yield is not None else None

        ps_ratio, _ = nd.fundamental(ticker, 'apr2rev')
        psr = f"{round(ps_ratio, 1)}x" if ps_ratio is not None else None

        pfcf_ratio, _ = nd.fundamental(ticker, 'aprfcfps')
        pfcf = f"{round(pfcf_ratio, 1)}x" if pfcf_ratio is not None else None

        net_debt, _ = nd.fundamental(ticker, 'netdebt_i')
        ndt = f"${round(net_debt, 1)}M" if net_debt is not None else None

        debt_to_equity, _ = nd.fundamental(ticker, 'qtotd2eq')
        de = f"{round(debt_to_equity, 1)}%" if debt_to_equity is not None else None

        current_ratio, _ = nd.fundamental(ticker, 'qcurratio')
        cr = f"{round(current_ratio, 1)}%" if current_ratio is not None else None

        free_cash_flow, _ = nd.fundamental(ticker, 'a1fcf')
        fcf = f"${round(free_cash_flow, 1)}M" if free_cash_flow is not None else None

        net_profit_margin, _ = nd.fundamental(ticker, 'ttmnpmgn')
        npm = f"{round(net_profit_margin, 1)}%" if net_profit_margin is not None else None

        revenue_growth_3y, _ = nd.fundamental(ticker, 'revgrpct')
        rg = f"{round(revenue_growth_3y, 1)}%" if revenue_growth_3y is not None else None

        eps_growth_3y, _ = nd.fundamental(ticker, 'epsgrpct')
        eg = f"{round(eps_growth_3y, 1)}%" if eps_growth_3y is not None else None

        roe, _ = nd.fundamental(ticker, 'ttmroepct')
        req = f"{round(roe, 1)}%" if roe is not None else None
    except:
        ticker = symbol[:3] + 'DA.au'
        # if ticker == 'SUN.au':
        #     ticker='SUNDD.au'
        company_name = nd.security_name(ticker)
        gics_sector = nd.classification_at_level(ticker, 'GICS', 'Name', 1)
        
        end = datetime.datetime.now()
        # end = '2024-12-29'
        start = datetime.datetime.now() - datetime.timedelta(days=2*365)
        
        # Last price
        prices = nd_timeseries(
            symbol=ticker, 
            # sd=start,
            ed=end,
            freq='W'
        )
        
        last_price = prices.iloc[-1]['Close']
        lp = f"${orderPriceRounding(last_price):.2f}" if last_price is not None else None

        # 52 week range
        high = f"${orderPriceRounding(prices['High'].rolling(window=52).max().iloc[-1])}"
        low = f"${orderPriceRounding(prices['Low'].rolling(window=52).min().iloc[-1])}"
        # range_52_week = f"${orderPriceRounding(low)} - ${orderPriceRounding(high)}" if high is not None and low is not None else None

        # stops
        sp = get_stop_price(prices, stopwindow)

        # Market cap
        market_cap, _ = nd.fundamental(ticker, 'mktcap')
        mc = f"${round(market_cap / 1000, 1)}B" if market_cap is not None else None

        # Franking
        franking_level, _ = nd.fundamental(ticker, 'FrankedPct')
        fl = f"{round(franking_level, 1)}%" if franking_level is not None else None

        # Summary
        business_summary = nd.business_summary(ticker)

        trailing_pe, _ = nd.fundamental(ticker, 'pebexclxor')
        tpe = f"{round(trailing_pe, 1)}x" if trailing_pe is not None else None

        dividend_yield, _ = nd.fundamental(ticker, 'divyield_curttm')
        dy = f"{round(dividend_yield, 1)}%" if dividend_yield is not None else None

        ps_ratio, _ = nd.fundamental(ticker, 'apr2rev')
        psr = f"{round(ps_ratio, 1)}x" if ps_ratio is not None else None

        pfcf_ratio, _ = nd.fundamental(ticker, 'aprfcfps')
        pfcf = f"{round(pfcf_ratio, 1)}x" if pfcf_ratio is not None else None

        net_debt, _ = nd.fundamental(ticker, 'netdebt_i')
        ndt = f"${round(net_debt, 1)}M" if net_debt is not None else None

        debt_to_equity, _ = nd.fundamental(ticker, 'qtotd2eq')
        de = f"{round(debt_to_equity, 1)}%" if debt_to_equity is not None else None

        current_ratio, _ = nd.fundamental(ticker, 'qcurratio')
        cr = f"{round(current_ratio, 1)}%" if current_ratio is not None else None

        free_cash_flow, _ = nd.fundamental(ticker, 'a1fcf')
        fcf = f"${round(free_cash_flow, 1)}M" if free_cash_flow is not None else None

        net_profit_margin, _ = nd.fundamental(ticker, 'ttmnpmgn')
        npm = f"{round(net_profit_margin, 1)}%" if net_profit_margin is not None else None

        revenue_growth_3y, _ = nd.fundamental(ticker, 'revgrpct')
        rg = f"{round(revenue_growth_3y, 1)}%" if revenue_growth_3y is not None else None

        eps_growth_3y, _ = nd.fundamental(ticker, 'epsgrpct')
        eg = f"{round(eps_growth_3y, 1)}%" if eps_growth_3y is not None else None

        roe, _ = nd.fundamental(ticker, 'ttmroepct')
        req = f"{round(roe, 1)}%" if roe is not None else None

    return [company_name, symbol, gics_sector, lp, sp, high, low, mc, fl, business_summary, tpe, dy, psr, pfcf, ndt, de, cr, fcf, npm, rg, eg, req]

#%% income stops
stops = []
syms = ['DBI', 'ANZ', 'AMC','AGL','NHC', 'EDV','APA','CIP','BWP','TLS', 'BOQ', 'NSR']
mccd = []
for n in syms:
    mccd.append(company_data(n, 30))
inc_comp_data = pd.DataFrame(mccd)

inc_comp_data.to_csv('Y:\AusBiz/inc_comp_data.csv')

#%% large stops
syms = ['RIO', 'DBI', 'ANZ', 'AMC', 'JHX', 'AGL', 'NAB','AAI','DMP','SGM','S32','CIP','CGF','BWP','DOW']
stops = []
mccd = []
for n in syms:
    mccd.append(company_data(n, 30))
large_comp_data = pd.DataFrame(mccd)

large_comp_data.to_csv('Y:\AusBiz/large_comp_data.csv')

#%% mid stops
syms = ['SXE', 'GNG', 'HZN', 'SRG','SKC','GRX','JMS','RDX','ASK','RUL','SVR','IGL']
stops = []
mccd = []
for n in syms:
    mccd.append(company_data(n, 12))
mc_comp_data = pd.DataFrame(mccd)

mc_comp_data.to_csv('Y:\AusBiz/mid_comp_data.csv')

# %%
