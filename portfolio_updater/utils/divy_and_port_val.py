#%% 
import datetime
from utils.company_data import nd_timeseries
from utils.file_io import read_excel_sheet
import norgatedata as nd

def get_equity_value(tradelist, cash, ed):

    portfolio = tradelist[tradelist['Trade:']=='Open']['Code:'].to_list()
    numshares = tradelist[tradelist['Trade:']=='Open']['Shares:'].to_list()

    
    equityvalue = 0
    sd = datetime.datetime.now() - datetime.timedelta(days=2*365)
    for s, n in zip(portfolio, numshares):

        try:
            sym = f"{s[:3]}.au"
            # if sym == "SUN.au":
            #     sym ="SUNDD.au"
            data = nd_timeseries(sym, ed, 'W')
            closeprice = data.iloc[-1]['Close']
            value = closeprice * n
            print(f"{sym}: {value}")
            equityvalue += value
            # print(f"cum equity val = {equityvalue}")
        except:
            sym = f"{s[:3]}DA.au"
            # if sym == "SUN.au":
            #     sym ="SUNDD.au"
            data = nd_timeseries(sym, ed, 'W')
            closeprice = data.iloc[-1]['Close']
            value = closeprice * n
            print(f"{sym}: {value}")
            equityvalue += value
            # print(f"cum equity val = {equityvalue}")
    
    # get values of sold positions
    if tradelist[(tradelist['Ex. Price:'].isnull())&(tradelist['Trade:']=='Long')].empty:
        pass
    else:
        for s in tradelist[tradelist['Ex. Price:'].isnull()]['Code:'].to_list():
            sym = f"{s[:3]}.au"
            data = nd_timeseries(sym, sd, ed, 'W')
            openprice = data.iloc[-1]['Open']
            value = openprice * tradelist[tradelist['Code:']==s]['Shares:'].values[0]
            equityvalue += value
            print(f"{sym}: {value}")

    # add cash
    equityvalue += cash

    return equityvalue

def get_div_yield(tradelist, cash, ed):
    portfolio_value = get_equity_value(tradelist, cash, ed)

    portfolio = tradelist[tradelist['Trade:']=='Open']['Code:'].to_list()
    numshares = tradelist[tradelist['Trade:']=='Open']['Shares:'].to_list()
   
    weights = []
    dy = []
    sd = datetime.datetime.now() - datetime.timedelta(days=2*365)
    for s, n in zip(portfolio, numshares):
        
        try:
            sym = f"{s[:3]}.au"
            # if sym == "SUN.au":
            #     sym ="SUNDD.au"
            data = nd_timeseries(sym, ed, 'W')
            closeprice = data.iloc[-1]['Close']
            value = closeprice * n
            weights.append(value/portfolio_value)
            dividend_yield, _ = nd.fundamental(sym, 'divyield_curttm')
            dy.append(dividend_yield)
            # print(f"cum equity val = {equityvalue}")
        except:
            sym = f"{s[:3]}DA.au"
            # if sym == "SUN.au":
            #     sym ="SUNDD.au"
            data = nd_timeseries(sym, ed, 'W')
            closeprice = data.iloc[-1]['Close']
            value = closeprice * n
            weights.append(value/portfolio_value)
            dividend_yield, _ = nd.fundamental(sym, 'divyield_curttm')
            dy.append(dividend_yield)
            # print(f"cum equity val = {equityvalue}")
    port_div_yield = sum(x * y for x, y in zip(weights, dy))
    return port_div_yield


# %%
tradelist = read_excel_sheet("Y:\AusBiz\portfolio_updater\output\mid_cap/2025-12-21-data-mid.xlsx", "Trades")
portfolio_value = get_equity_value(tradelist, 5426135.61027, datetime.date(2025,12,22))
print(portfolio_value)
# print(dy)
#%% get div yield
dy = get_div_yield(tradelist, 3444751.95729, datetime.date(2025,11,30))
print(dy)
