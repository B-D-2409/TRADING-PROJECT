#%%
import importlib
import logging
import os
import datetime
import numpy as np
import pandas as pd

#%%
logger = logging.getLogger(__name__)

#%%
_nd = None
_PROVIDER = 'local'

try:
    _nd = importlib.import_module('norgatedata')
    if type(_nd).__name__ == 'MagicMock':
        raise RuntimeError("norgatedata is mocked — local dev mode")
    _nd.status()
    _PROVIDER = 'norgate'
except Exception:
    _nd = None
    _PROVIDER = 'local'

logger.info(f"data_factory initialised — provider: {_PROVIDER.upper()}")

#%%
_TEST_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), '..', 'test')
)

#%%
_OHLCV_COLUMNS       = ['Open', 'High', 'Low', 'Close', 'Volume']
_PLACEHOLDER_COLUMNS = ['Turnover', 'Dividend', 'Sector', 'Security Name']

#%%
def _clean_symbol(symbol: str) -> str:
    """Strip provider suffixes and normalise symbol to a bare uppercase ticker."""
    return symbol.replace('.au', '').replace('DA', '').upper()

def _inject_missing_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure all required OHLCV and placeholder columns exist, filling gaps with defaults."""
    for col in _OHLCV_COLUMNS:
        if col not in df.columns:
            df[col] = 0.0
    for col in _PLACEHOLDER_COLUMNS:
        if col not in df.columns:
            df[col] = 'N/A'
    return df

def _round_price(price: float) -> float:
    """Round a price to the correct tick size for its magnitude."""
    if 0.1 <= price < 2.0:
        return float(np.round(np.round(price / 0.005) * 0.005, 3))
    if price < 0.1:
        return float(np.round(price, 3))
    return float(np.round(price, 2))

#%%
def _norgate_timeseries(symbol: str, ed, freq: str) -> pd.DataFrame:
    """Fetch an OHLCV timeseries from Norgate Data for the given symbol and frequency."""
    sd = datetime.datetime.now() - datetime.timedelta(days=2 * 365)
    return _nd.price_timeseries(
        symbol,
        stock_price_adjustment_setting=_nd.StockPriceAdjustmentType.TOTALRETURN,
        padding_setting=_nd.PaddingType.NONE,
        start_date=sd,
        end_date=ed,
        timeseriesformat='pandas-dataframe',
        interval=freq,
    )

#%%
def _local_timeseries(symbol: str) -> pd.DataFrame:
    """Load an OHLCV timeseries from a local Excel file in the test directory."""
    path = os.path.join(_TEST_DIR, f"{_clean_symbol(symbol)}.xlsx")
    if not os.path.exists(path):
        logger.warning(f"Local file not found for '{symbol}' — returning empty DataFrame")
        cols = _OHLCV_COLUMNS + _PLACEHOLDER_COLUMNS
        df = pd.DataFrame(columns=cols)
        df.index.name = 'Date'
        return df
    df = pd.read_excel(path, index_col=0, parse_dates=True)
    df.index.name = 'Date'
    return _inject_missing_columns(df)

#%%
def get_data(symbol: str, ed=None, freq: str = 'W') -> pd.DataFrame:
    """Return a standardised OHLCV DataFrame for the given symbol, or None on failure."""
    if ed is None:
        ed = datetime.datetime.now()
    logger.info(f"Fetching timeseries — symbol: {symbol!r}, freq: {freq}, provider: {_PROVIDER.upper()}")
    try:
        df = _norgate_timeseries(symbol, ed, freq) if _PROVIDER == 'norgate' else _local_timeseries(symbol)
        if df is None or df.empty:
            logger.warning(f"Empty data returned for '{symbol}'")
            return df
        logger.info(f"Timeseries fetched for '{symbol}' — {len(df)} rows")
        return df
    except Exception as e:
        logger.error(f"Failed to fetch timeseries for '{symbol}': {e}")
        return None

#%%
def get_dividend(symbol: str, ed=None, freq: str = 'W') -> pd.Series:
    """Return a Series of dividend values for the given symbol, or a zero Series on failure."""
    if ed is None:
        ed = datetime.datetime.now()
    logger.info(f"Fetching dividend series — symbol: {symbol!r}, provider: {_PROVIDER.upper()}")
    try:
        if _PROVIDER == 'norgate':
            sd  = datetime.datetime.now() - datetime.timedelta(days=2 * 365)
            raw = _nd.price_timeseries(
                symbol,
                stock_price_adjustment_setting=_nd.StockPriceAdjustmentType.NONE,
                padding_setting=_nd.PaddingType.NONE,
                start_date=sd,
                end_date=ed,
                timeseriesformat='pandas-dataframe',
                interval=freq,
            )
            return raw['Dividend']
        df = _local_timeseries(symbol)
        if 'Dividend' not in df.columns:
            return pd.Series(0.0, index=df.index, name='Dividend')
        return df['Dividend']
    except Exception as e:
        logger.error(f"Failed to fetch dividend series for '{symbol}': {e}")
        return pd.Series(dtype=float, name='Dividend')

#%%
def _resolve_norgate_ticker(symbol: str, ed, freq: str):
    """Try the base and DA-suffixed Norgate ticker variants and return the first that resolves."""
    for suffix in (symbol[:3] + '.au', symbol[:3] + 'DA.au'):
        try:
            name   = _nd.security_name(suffix)
            sector = _nd.classification_at_level(suffix, 'GICS', 'Name', 1)
            prices = _norgate_timeseries(suffix, ed, freq)
            return suffix, name, sector, prices
        except Exception:
            continue
    return None, None, None, None

def _norgate_fundamentals(symbol: str, ed, freq: str) -> list:
    """Fetch and format a 21-element list of fundamental data fields from Norgate."""
    ticker, name, sector, prices = _resolve_norgate_ticker(symbol, ed, freq)
    if ticker is None:
        return _local_fundamentals(symbol)

    last_price = prices.iloc[-1]['Close']
    lp   = f"${_round_price(last_price):.2f}" if last_price is not None else 'N/A'
    high = f"${_round_price(prices['High'].rolling(window=52).max().iloc[-1])}"
    low  = f"${_round_price(prices['Low'].rolling(window=52).min().iloc[-1])}"

    def _fmt(key, fmt):
        """Format a single fundamental value using the supplied formatter, returning 'N/A' if absent."""
        val, _ = _nd.fundamental(ticker, key)
        return fmt(val) if val is not None else 'N/A'

    return [
        name, symbol, sector, lp, high, low,
        _fmt('mktcap',          lambda v: f"${round(v / 1000, 1)}B"),
        _fmt('FrankedPct',      lambda v: f"{round(v, 1)}%"),
        _nd.business_summary(ticker),
        _fmt('pebexclxor',      lambda v: f"{round(v, 1)}x"),
        _fmt('divyield_curttm', lambda v: f"{round(v, 1)}%"),
        _fmt('apr2rev',         lambda v: f"{round(v, 1)}x"),
        _fmt('aprfcfps',        lambda v: f"{round(v, 1)}x"),
        _fmt('netdebt_i',       lambda v: f"${round(v, 1)}M"),
        _fmt('qtotd2eq',        lambda v: f"{round(v, 1)}%"),
        _fmt('qcurratio',       lambda v: f"{round(v, 1)}%"),
        _fmt('a1fcf',           lambda v: f"${round(v, 1)}M"),
        _fmt('ttmnpmgn',        lambda v: f"{round(v, 1)}%"),
        _fmt('revgrpct',        lambda v: f"{round(v, 1)}%"),
        _fmt('epsgrpct',        lambda v: f"{round(v, 1)}%"),
        _fmt('ttmroepct',       lambda v: f"{round(v, 1)}%"),
    ]

def _local_fundamentals(symbol: str) -> list:
    """Return a 21-element fallback list of 'N/A' values for local/offline mode."""
    na = 'N/A'
    return [na, symbol, na, na, na, na, na, na, na, na, na, na, na, na, na, na, na, na, na, na, na]

#%%
def get_fundamentals(symbol: str, ed=None, freq: str = 'W') -> list:
    """Return a 21-element list of formatted fundamental data fields, or a '-' fallback list on error."""
    if ed is None:
        ed = datetime.datetime.now()
    logger.info(f"Fetching fundamentals — symbol: {symbol!r}, provider: {_PROVIDER.upper()}")
    try:
        result = _norgate_fundamentals(symbol, ed, freq) if _PROVIDER == 'norgate' else _local_fundamentals(symbol)
        logger.info(f"Fundamentals fetched for '{symbol}'")
        return result
    except Exception as e:
        logger.error(f"Failed to fetch fundamentals for '{symbol}': {e}")
        return ['-'] * 21
