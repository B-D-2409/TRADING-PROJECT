import datetime
from company_data import nd_timeseries

def get_equity_value(tradelist, cash, ed):

    portfolio = tradelist[tradelist['Trade:']=='Open']['Code:'].to_list()
    numshares = tradelist[tradelist['Trade:']=='Open']['Shares:'].to_list()

    
    equityvalue = 0
    sd = datetime.datetime.now() - datetime.timedelta(days=2*365)
    for s, n in zip(portfolio, numshares):
        
        sym = f"{s[:3]}.au"
        # if sym == "SUN.au":
        #     sym ="SUNDD.au"
        data = nd_timeseries(sym, sd, ed, 'W')
        closeprice = data.iloc[-1]['Close']
        value = closeprice * n
        print(f"{sym}: {value}")
        equityvalue += value
    
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

def update_equity_curve(equitydf, equityvalue, d, cash):

    date = d
    drawdown = equityvalue - max(equitydf['Portfolio Equity:'].max(), equityvalue)
    drawdownpct = drawdown / max(equitydf['Portfolio Equity:'].max(), equityvalue)

    newrow = [date, equityvalue, cash, drawdown, drawdownpct]

    equitydf.loc[len(equitydf)] = newrow

    return equitydf
