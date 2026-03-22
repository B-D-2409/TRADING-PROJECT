import yfinance as yf
import pandas as pd
import os

test_dir = "test"
os.makedirs(test_dir, exist_ok=True)

symbols = ['BHP', 'RIO', 'RHC', 'DBI', 'ANZ', 'CBA', 'NAB', 'WBC', 'TLS', 'CSL', 'WES', 'MQG', 'WOW', 'FMG']

for sym in symbols:
    ticker = f"{sym}.AX"
    data = yf.download(ticker, start="2024-01-01", end="2026-03-19")
    data = data.reset_index()
    data.columns = [col[0] if isinstance(col, tuple) else col for col in data.columns]
    if 'Date' not in data.columns:
        data.rename(columns={'index': 'Date'}, inplace=True)
    data['Date'] = pd.to_datetime(data['Date']).dt.tz_localize(None)
    data.to_excel(f"{test_dir}/{sym}.xlsx", index=False)

benchmark = yf.download("^AXJO", start="2024-01-01", end="2026-03-19")
benchmark = benchmark.reset_index()
benchmark.columns = [col[0] if isinstance(col, tuple) else col for col in benchmark.columns]
benchmark['Date'] = pd.to_datetime(benchmark['Date']).dt.tz_localize(None)
benchmark.to_excel(f"{test_dir}/XJO.xlsx", index=False)