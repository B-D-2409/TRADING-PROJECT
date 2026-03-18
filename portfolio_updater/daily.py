#%%
import pandas as pd 
import numpy as np
from datetime import datetime, timedelta
import logging
from utils.file_io import read_excel_sheet
from utils.company_data import nd_timeseries

logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

#%%
# Read in excel sheet
date = datetime.now().strftime("%Y-%m-%d")
path = f"./test/2025-08-03-data-large-UPDATED.xlsx"
logger.info(f"Reading in data from {path}")
df_bs_alerts = read_excel_sheet(path, sheet='Buy Sell Alerts')
logger.info(f"Data read successfully from {path}")
logger.info(f"Buy Sell Alert: \n{df_bs_alerts}")
# Check if the market traded 
# (i.e. if there is a gap of more than 1 day between the most recent 2 daily bars)
#%%
unique_symbols = df_bs_alerts["Code:"].unique()
logger.info(f"Unique symbols in Buy Sell Alerts: {unique_symbols}")
# each symbol has .asx replace that with .au
unique_symbols = [symbol.replace('.ASX', '.au') for symbol in unique_symbols]
#%%
# Loop through each symbol and check if the market traded
# (i.e. if there is a gap of more than 1 day between the most recent 2 daily bars)
for symbol in unique_symbols:
    logger.info(f"Processing symbol: {symbol}")
    df = nd_timeseries(symbol, date, 'D')
    # Check if the market traded
    if df.empty:
        logger.warning(f"No data found for symbol: {symbol}")
        continue
    
    print(f"Data for {symbol}:\n{df.head()}")
    # df['Date'] = pd.to_datetime(df['Date'])
    # df.sort_values(by='Date', ascending=False, inplace=True)
    # df['Date'] = df['Date'].dt.date
    # logger.info(f"Data for {symbol}:\n{df.head()}")
    # if len(df) < 2:
    #     logger.warning(f"Not enough data to check trading for symbol: {symbol}")
    #     continue
    # last_date = df['Date'].iloc[0]
    # second_last_date = df['Date'].iloc[1]
    # if last_date - second_last_date > timedelta(days=1):
    #     logger.warning(f"Market did not trade for symbol: {symbol} on {last_date}")
    # else:
    #     logger.info(f"Market traded for symbol: {symbol} on {last_date}")
    # # Get the last price
    # last_price = df['Close'].iloc[0]
    # logger.info(f"Last price for {symbol} on {last_date}: {last_price}")
    # # Get the last price for the symbol
    # if last_price is not None:
    #     logger.info(f"Last price for {symbol} on {last_date}: {last_price}")
    # else:
    #     logger.warning(f"No last price found for {symbol} on {last_date}")
        

# %%
