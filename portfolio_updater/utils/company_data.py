try:
    import norgatedata as nd
except ImportError:
    nd = None

import numpy as np
import datetime

def nd_timeseries(symbol, *args):
    from utils.data_factory import _PROVIDER, get_data
    import datetime

    if len(args) == 3:
        sd, ed, freq = args
    elif len(args) == 2:
        ed, freq = args
        sd = datetime.datetime.now() - datetime.timedelta(days=2*365)
    else:
        ed = args[0] if len(args) > 0 else datetime.datetime.now()
        freq = args[1] if len(args) > 1 else 'D'
        sd = datetime.datetime.now() - datetime.timedelta(days=2*365)

    if _PROVIDER == 'norgate' and nd is None:
        return get_data(symbol, ed, freq)
    
    import norgatedata as nd
    data = nd.price_timeseries(
        symbol,
        stock_price_adjustment_setting = nd.StockPriceAdjustmentType.TOTALRETURN,
        padding_setting = nd.PaddingType.NONE,
        start_date = sd,
        end_date = ed,
        timeseriesformat = 'pandas-dataframe',
        interval = freq
    )
    return data
def nd_div(symbol, ed, freq):
    if nd is None:
        from utils.data_factory import get_dividend
        return get_dividend(symbol)
    
    sd = datetime.datetime.now() - datetime.timedelta(days=2*365)
    data = nd.price_timeseries(
        symbol,
        stock_price_adjustment_setting = nd.StockPriceAdjustmentType.NONE,
        padding_setting = nd.PaddingType.NONE,
        start_date = sd,
        end_date = ed,
        timeseriesformat = 'pandas-dataframe',
        interval = freq
    )
    return data['Dividend']

def roundToTick(price, tick):
    result = np.round(price/tick) * tick
    return result

def orderPriceRounding(price):
    if price is None:
        return 0.0
    if price < 2 and price >= 0.1:
        initRound = roundToTick(price, 0.005)
        return np.round(initRound, 3)
    elif price < 0.1:
        return np.round(price, 3)
    else:
        return np.round(price, 2)
    
def fundamental_data(symbol:str, ed:datetime.date, freq:str):
    if nd is None:
        from utils.data_factory import get_fundamentals
        return get_fundamentals(symbol, ed, freq)

    ticker = symbol[:3] + '.au'
    company_name = nd.security_name(ticker)
    gics_sector = nd.classification_at_level(ticker, 'GICS', 'Name', 1)
    sd = datetime.datetime.now() - datetime.timedelta(days=2*365)
        
    prices = nd_timeseries(ticker, ed, freq)
    
    last_price = prices.iloc[-1]['Close'] if not prices.empty else None
    lp = f"${orderPriceRounding(last_price):.2f}" if last_price is not None else "N/A"

    high = f"${orderPriceRounding(prices['High'].rolling(window=52).max().iloc[-1])}" if not prices.empty else "N/A"
    low = f"${orderPriceRounding(prices['Low'].rolling(window=52).min().iloc[-1])}" if not prices.empty else "N/A"

    def get_fund(t, field):
        val, _ = nd.fundamental(t, field)
        return val

    market_cap = get_fund(ticker, 'mktcap')
    mc = f"${round(market_cap / 1000, 1)}B" if market_cap else "N/A"

    franking_level = get_fund(ticker, 'FrankedPct')
    fl = f"{round(franking_level, 1)}%" if franking_level else "N/A"

    business_summary = nd.business_summary(ticker)
    
    tpe = f"{round(get_fund(ticker, 'pebexclxor'), 1)}x" if get_fund(ticker, 'pebexclxor') else "N/A"
    dy = f"{round(get_fund(ticker, 'divyield_curttm'), 1)}%" if get_fund(ticker, 'divyield_curttm') else "N/A"
    psr = f"{round(get_fund(ticker, 'apr2rev'), 1)}x" if get_fund(ticker, 'apr2rev') else "N/A"
    pfcf = f"{round(get_fund(ticker, 'aprfcfps'), 1)}x" if get_fund(ticker, 'aprfcfps') else "N/A"
    ndt = f"${round(get_fund(ticker, 'netdebt_i'), 1)}M" if get_fund(ticker, 'netdebt_i') else "N/A"
    de = f"{round(get_fund(ticker, 'qtotd2eq'), 1)}%" if get_fund(ticker, 'qtotd2eq') else "N/A"
    cr = f"{round(get_fund(ticker, 'qcurratio'), 1)}%" if get_fund(ticker, 'qcurratio') else "N/A"
    fcf = f"${round(get_fund(ticker, 'a1fcf'), 1)}M" if get_fund(ticker, 'a1fcf') else "N/A"
    npm = f"{round(get_fund(ticker, 'ttmnpmgn'), 1)}%" if get_fund(ticker, 'ttmnpmgn') else "N/A"
    rg = f"{round(get_fund(ticker, 'revgrpct'), 1)}%" if get_fund(ticker, 'revgrpct') else "N/A"
    eg = f"{round(get_fund(ticker, 'epsgrpct'), 1)}%" if get_fund(ticker, 'epsgrpct') else "N/A"
    req = f"{round(get_fund(ticker, 'ttmroepct'), 1)}%" if get_fund(ticker, 'ttmroepct') else "N/A"

    return [company_name, symbol, gics_sector, lp, high, low, mc, fl, business_summary, tpe, dy, psr, pfcf, ndt, de, cr, fcf, npm, rg, eg, req]