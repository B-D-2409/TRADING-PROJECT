import datetime
from utils.company_data import nd_timeseries

def get_equity_value(trades_df, cash, target_date):
    if trades_df.empty:
        return cash
        
    # Filter only open positions
    open_positions = trades_df[trades_df['Trade:'] == 'Open']
    if open_positions.empty:
        return cash
        
    holdings_value = 0
    for _, row in open_positions.iterrows():
        sym = row['Code:']
        # We look for price data
        data = nd_timeseries(sym, target_date, 'D')
        
        # Check if data is empty (the 'armored' placeholder case)
        if data is None or data.empty:
            print(f"--- WARNING: No price data for {sym}, skipping in equity calculation ---")
            continue
            
        closeprice = data.iloc[-1]['Close']
        holdings_value += (row['Shares:'] * closeprice)
        
    return holdings_value + cash

def update_equity_curve(equitydf, equityvalue, d, cash):

    date = d
    drawdown = equityvalue - max(equitydf['Portfolio Equity:'].max(), equityvalue)
    drawdownpct = drawdown / max(equitydf['Portfolio Equity:'].max(), equityvalue)

    newrow = [date, equityvalue, cash, drawdown, drawdownpct]

    equitydf.loc[len(equitydf)] = newrow

    return equitydf
