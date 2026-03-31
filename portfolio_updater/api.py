import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import yfinance as yf
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="AusBiz Portfolio API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).parent

STRATEGY_META = {
    "large_cap": {
        "label":       "Large Cap",
        "universe":    "ASX XJO · Top 200",
        "file_suffix": "large",
        "output_dir":  BASE_DIR / "output" / "large_cap",
    },
    "mid_cap": {
        "label":       "Mid Cap",
        "universe":    "ASX XMD · 201–300",
        "file_suffix": "mid",
        "output_dir":  BASE_DIR / "output" / "mid_cap",
    },
    "income": {
        "label":       "Income",
        "universe":    "ASX XAO · Dividend Focus",
        "file_suffix": "income",
        "output_dir":  BASE_DIR / "output" / "income",
    },
}

SHEET_EQUITY    = "Equity Curve"
SHEET_TRADES    = "Trades"
SHEET_ALERTS    = "Buy Sell Alerts"
SHEET_COMPANY   = "Company Page Data"
SHEET_ANALYTICS = "Analytics"

SKIP_TAGS = {"DRAFT", "UPDATED"}

INDEX_COL_CANDIDATES = ["XJO:", "XAO:", "Index:", "Benchmark:", "Index Value:"]

# Exact Analytics sheet row labels (lowercased). First match wins.
ANALYTICS_KEYS: dict[str, list[str]] = {
    "return3M":           ["last 3 month return %",  "3 month return %",  "last 3 month return"],
    "return6M":           ["last 6 month return %",  "6 month return %",  "last 6 month return"],
    "return12M":          ["last 12 month return %", "12 month return %", "last 12 month return"],
    "annual":             ["annual return %",         "annual return",     "cagr %", "cagr"],
    "ytd":                ["ytd return %",            "ytd return",        "year to date return %", "year to date return"],
    "maxDrawdown":        ["max drawdown %",          "max drawdown",      "maximum drawdown %", "maximum drawdown"],
    "winPct":             ["win %",                   "win rate %",        "% wins",   "win rate"],
    "lossPct":            ["loss %",                  "loss rate %",       "% losses", "loss rate"],
    "wlr":                ["win/loss ratio",          "w/l ratio",         "wlr"],
    "portfolioDivYield":  ["portfolio dividend yield %", "dividend yield %", "div yield %"],
}

# Exact Company Page Data column headers. First match wins.
COMPANY_COLS: dict[str, list[str]] = {
    "pe":         ["P/E Ratio:",           "P/E:",          "PE:",         "Price/Earnings:"],
    "divYield":   ["Dividend Yield:",      "Div Yield:",    "Yield:"],
    "peg":        ["PEG Ratio:",           "PEG:"],
    "ps":         ["P/S Ratio:",           "P/S:",          "Price/Sales:"],
    "roe":        ["ROE:",                 "Return on Equity:"],
    "debtEquity": ["Debt-to-Equity Ratio:", "Debt/Equity:", "D/E:",        "Debt Equity:"],
}


def _find_latest_file(strategy: str) -> Path:
    meta       = STRATEGY_META[strategy]
    output_dir = Path(meta["output_dir"])

    if not output_dir.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Output directory not found: {output_dir}",
        )

    candidates = [
        f for f in output_dir.glob("*.xlsx")
        if not any(tag in f.stem.upper() for tag in SKIP_TAGS)
        and len(f.stem) >= 10
        and f.stem[:10].replace("-", "").isdigit()
    ]

    if not candidates:
        raise HTTPException(
            status_code=404,
            detail=f"No data file found for strategy '{strategy}' in {output_dir}",
        )

    return max(candidates, key=lambda f: f.stem[:10])


def _read_sheet(path: Path, sheet: str) -> pd.DataFrame:
    try:
        return pd.read_excel(path, sheet_name=sheet)
    except Exception:
        raise HTTPException(
            status_code=404,
            detail=f"Required sheet '{sheet}' not found in {path.name}",
        )


def _try_read_sheet(path: Path, sheet: str) -> Optional[pd.DataFrame]:
    try:
        return pd.read_excel(path, sheet_name=sheet)
    except Exception:
        return None


def _to_float(value, default=0.0):
    if value is None:
        return default
    if isinstance(value, float) and pd.isna(value):
        return default
    if isinstance(value, str):
        cleaned = value.replace("%", "").replace("$", "").replace(",", "").strip()
        if cleaned in ("-", "", "N/A", "nan"):
            return default
        try:
            return float(cleaned)
        except ValueError:
            return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def _to_str(value, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, float) and pd.isna(value):
        return default
    result = str(value).strip()
    return default if result in ("nan", "NaT") else result


def _fmt_date(value) -> str:
    if isinstance(value, (datetime, pd.Timestamp)):
        return value.strftime("%d %b %Y")
    raw = _to_str(value)
    for pattern in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(raw, pattern).strftime("%d %b %Y")
        except ValueError:
            continue
    return raw


def _fmt_date_short(value) -> str:
    if isinstance(value, (datetime, pd.Timestamp)):
        return value.strftime("%b '%y")
    raw = _to_str(value)
    for pattern in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(raw, pattern).strftime("%b '%y")
        except ValueError:
            continue
    return raw


def _first_valid(row, *cols):
    for col in cols:
        val = row.get(col)
        if val is not None and not (isinstance(val, float) and pd.isna(val)):
            return val
    return None


def _asx_to_yf(ticker: str) -> str:
    return ticker.upper().replace(".ASX", ".AX")


def _fetch_live_prices(tickers: list[str]) -> dict[str, float]:
    if not tickers:
        return {}
    try:
        yf_map  = {t: _asx_to_yf(t) for t in tickers}
        symbols = list(yf_map.values())
        raw = yf.download(symbols, period="1d", progress=False, auto_adjust=True)
        if raw is None or raw.empty or "Close" not in raw.columns:
            return {}
        close = raw["Close"]
        result = {}
        for orig, sym in yf_map.items():
            try:
                price = float(close.iloc[-1]) if len(symbols) == 1 else float(close[sym].iloc[-1])
                if not pd.isna(price):
                    result[orig] = round(price, 4)
            except (KeyError, IndexError, TypeError):
                continue
        return result
    except Exception:
        return {}


def _parse_analytics(analytics_df: Optional[pd.DataFrame]) -> dict:
    if analytics_df is None or analytics_df.empty or analytics_df.shape[1] < 2:
        return {}
    col_keys = analytics_df.iloc[:, 0].astype(str).str.lower().str.strip()
    col_vals = analytics_df.iloc[:, 1]
    return dict(zip(col_keys, col_vals))


def _lookup(metrics: dict, field: str) -> Optional[float]:
    for label in ANALYTICS_KEYS.get(field, []):
        val = metrics.get(label)
        if val is not None:
            result = _to_float(val, default=None)
            if result is not None:
                return result
    return None


def _r(value, default: float = 0.0, places: int = 2) -> float:
    try:
        f = float(value) if value is not None else default
        if pd.isna(f) or not (-1e15 < f < 1e15):
            return default
        return round(f, places)
    except (TypeError, ValueError):
        return default


def _build_kpis(
    equity_df:    pd.DataFrame,
    analytics_df: Optional[pd.DataFrame],
) -> dict:
    empty_result = {
        "equity": 0.0, "cash": 0.0, "totalReturn": 0.0, "maxDrawdown": 0.0,
        "winPct": 0.0, "lossPct": 0.0, "wlr": 0.0, "portfolioDivYieldPct": 0.0,
    }

    if equity_df.empty or "Portfolio Equity:" not in equity_df.columns:
        return empty_result

    numeric_equity = pd.to_numeric(equity_df["Portfolio Equity:"], errors="coerce")
    valid_mask     = numeric_equity.notna()

    if not valid_mask.any():
        return empty_result

    clean            = equity_df[valid_mask].copy()
    clean["_equity"] = numeric_equity[valid_mask].values

    equity = float(clean["_equity"].iloc[-1])

    cash = 0.0
    if "Cash:" in clean.columns:
        cash_series = pd.to_numeric(clean["Cash:"], errors="coerce")
        if not cash_series.empty and cash_series.notna().any():
            cash = _to_float(cash_series.dropna().iloc[-1])

    metrics      = _parse_analytics(analytics_df)
    total_return = _lookup(metrics, "annual")
    max_drawdown = _lookup(metrics, "maxDrawdown")
    win_pct      = _lookup(metrics, "winPct")
    loss_pct     = _lookup(metrics, "lossPct")
    wlr          = _lookup(metrics, "wlr")
    div_yield    = _lookup(metrics, "portfolioDivYield")

    if total_return is None and len(clean) > 1:
        first_equity = float(clean["_equity"].iloc[0])
        if first_equity > 0:
            total_return = round((equity / first_equity - 1) * 100, 2)

    if max_drawdown is None and "Drawdown %:" in clean.columns:
        dd_series = pd.to_numeric(clean["Drawdown %:"], errors="coerce")
        if not dd_series.isna().all():
            max_drawdown = round(float(dd_series.min()), 2)

    return {
        "equity":               _r(equity),
        "cash":                 _r(cash),
        "totalReturn":          _r(total_return),
        "maxDrawdown":          _r(max_drawdown),
        "winPct":               _r(win_pct),
        "lossPct":              _r(loss_pct),
        "wlr":                  _r(wlr),
        "portfolioDivYieldPct": _r(div_yield),
    }


def _build_returns(analytics_df: Optional[pd.DataFrame]) -> dict:
    metrics = _parse_analytics(analytics_df)
    return {
        "return3M":  _r(_lookup(metrics, "return3M")),
        "return6M":  _r(_lookup(metrics, "return6M")),
        "return12M": _r(_lookup(metrics, "return12M")),
        "ytd":       _r(_lookup(metrics, "ytd")),
        "annual":    _r(_lookup(metrics, "annual")),
    }


def _build_equity_curve(equity_df: pd.DataFrame) -> list[dict]:
    if equity_df.empty or "Portfolio Equity:" not in equity_df.columns:
        return []

    numeric_equity = pd.to_numeric(equity_df["Portfolio Equity:"], errors="coerce")
    valid_mask     = numeric_equity.notna()

    if not valid_mask.any():
        return []

    clean            = equity_df[valid_mask].copy()
    clean["_equity"] = numeric_equity[valid_mask].values

    index_col = next((c for c in INDEX_COL_CANDIDATES if c in clean.columns), None)

    result = []
    for _, row in clean.iterrows():
        point: dict = {
            "date":  _fmt_date_short(row.get("Date:", "")),
            "value": round(float(row["_equity"]), 2),
        }
        if index_col:
            idx_val = pd.to_numeric(row.get(index_col), errors="coerce")
            if not pd.isna(idx_val):
                point["indexValue"] = round(float(idx_val), 2)
        result.append(point)
    return result


def _build_alerts(
    alerts_df:   pd.DataFrame,
    company_df:  Optional[pd.DataFrame],
    live_prices: dict[str, float],
) -> list[dict]:
    if alerts_df.empty or "Code:" not in alerts_df.columns:
        return []

    sector_lookup: dict[str, str] = {}
    if company_df is not None and not company_df.empty and "Code:" in company_df.columns:
        for _, row in company_df.iterrows():
            code = _to_str(row.get("Code:"))
            if code:
                sector_lookup[code] = _to_str(row.get("Sector:", ""))

    result = []
    for _, row in alerts_df.iterrows():
        ticker = _to_str(row.get("Code:"))
        action = _to_str(row.get("Action:")).upper()
        if not ticker or not action:
            continue

        alert_price   = _to_float(_first_valid(row, "Price:", "Alert Price:", "Signal Price:"))
        current_price = live_prices.get(ticker, 0.0)
        diff_pct      = 0.0
        if alert_price and current_price:
            diff_pct = round((current_price / alert_price - 1) * 100, 2)

        stop_type = _to_str(row.get("Stop Type:", ""))
        result.append({
            "ticker":       ticker,
            "action":       action,
            "date":         _fmt_date(row.get("Date:", "")),
            "reason":       stop_type if stop_type else "Momentum Signal",
            "sector":       sector_lookup.get(ticker, ""),
            "alertPrice":   round(alert_price, 4),
            "currentPrice": round(current_price, 4),
            "difference":   diff_pct,
        })
    return result


def _build_positions(
    trades_df:   pd.DataFrame,
    company_df:  Optional[pd.DataFrame],
    live_prices: dict[str, float],
) -> list[dict]:
    if trades_df.empty or "Trade:" not in trades_df.columns:
        return []

    company_lookup: dict[str, dict] = {}
    if company_df is not None and not company_df.empty and "Code:" in company_df.columns:
        for _, row in company_df.iterrows():
            code = _to_str(row.get("Code:"))
            if not code:
                continue
            company_lookup[code] = {
                "name":       _to_str(row.get("Name:")),
                "sector":     _to_str(row.get("Sector:")),
                "sheetPrice": _to_float(row.get("Last Price:")),
                **{
                    field: _to_float(_first_valid(row, *cols))
                    for field, cols in COMPANY_COLS.items()
                },
            }

    trade_col = trades_df["Trade:"].astype(str).str.strip()
    open_rows = trades_df[trade_col == "Open"]

    result = []
    for _, row in open_rows.iterrows():
        ticker = _to_str(row.get("Code:"))
        if not ticker:
            continue

        company       = company_lookup.get(ticker, {})
        entry_price   = _to_float(row.get("Price:"))
        pct_chg       = _to_float(row.get("% chg:"))
        profit_dollar = _to_float(row.get("Profit:"))
        profit_pct    = _to_float(row.get("% Profit:"))
        shares        = int(_to_float(row.get("Shares:", 0)))

        current_price = (
            live_prices.get(ticker)
            or company.get("sheetPrice")
            or (round(entry_price * (1.0 + pct_chg / 100.0), 4) if entry_price and pct_chg else 0.0)
        )

        result.append({
            "ticker":       ticker,
            "name":         company.get("name", ""),
            "sector":       company.get("sector", ""),
            "shares":       shares,
            "entryPrice":   _r(entry_price,   places=4),
            "currentPrice": _r(current_price, places=4),
            "profitDollar": _r(profit_dollar),
            "profitPct":    _r(profit_pct),
            "pe":           _r(company.get("pe")),
            "divYield":     _r(company.get("divYield")),
            "peg":          _r(company.get("peg")),
            "ps":           _r(company.get("ps")),
            "roe":          _r(company.get("roe")),
            "debtEquity":   _r(company.get("debtEquity")),
        })

    return result


VALID_STRATEGIES = {"all", "large_cap", "mid_cap", "income"}
VALID_RUN_TYPES  = {"daily", "weekly", "monthly"}


class EngineRunRequest(BaseModel):
    strategy: str
    run_type: str


@app.post("/api/engine/run")
async def run_engine(payload: EngineRunRequest):
    if payload.strategy not in VALID_STRATEGIES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid strategy '{payload.strategy}'. Valid: {sorted(VALID_STRATEGIES)}",
        )
    if payload.run_type not in VALID_RUN_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid run_type '{payload.run_type}'. Valid: {sorted(VALID_RUN_TYPES)}",
        )

    script_path = BASE_DIR / "main.py"
    run_flag    = f"--run-{payload.run_type}"
    cmd         = [sys.executable, str(script_path), "--strategy", payload.strategy, run_flag]

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=str(BASE_DIR),
        )
        stdout, _ = await process.communicate()
        output = stdout.decode("utf-8", errors="replace") if stdout else ""

        if process.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail={"message": "Engine run failed — check the logs.", "output": output[-3000:]},
            )

        return {
            "status":   "success",
            "strategy": payload.strategy,
            "run_type": payload.run_type,
            "message":  f"Engine completed successfully · {payload.strategy} / {payload.run_type}",
            "output":   output[-3000:],
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"message": str(exc), "output": ""},
        )


@app.get("/api/portfolio/{strategy}")
def get_portfolio(strategy: str):
    if strategy not in STRATEGY_META:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown strategy '{strategy}'. Valid: {list(STRATEGY_META.keys())}",
        )

    meta      = STRATEGY_META[strategy]
    file_path = _find_latest_file(strategy)
    file_date = datetime.strptime(file_path.stem[:10], "%Y-%m-%d")

    equity_df    = _read_sheet(file_path, SHEET_EQUITY)
    trades_df    = _read_sheet(file_path, SHEET_TRADES)
    alerts_df    = _read_sheet(file_path, SHEET_ALERTS)
    analytics_df = _try_read_sheet(file_path, SHEET_ANALYTICS)
    company_df   = _try_read_sheet(file_path, SHEET_COMPANY)

    alert_tickers    = [_to_str(r.get("Code:")) for _, r in alerts_df.iterrows() if _to_str(r.get("Code:"))]
    position_tickers = [
        _to_str(r.get("Code:"))
        for _, r in trades_df[trades_df.get("Trade:", pd.Series(dtype=str)).astype(str).str.strip() == "Open"].iterrows()
        if _to_str(r.get("Code:"))
    ] if not trades_df.empty and "Trade:" in trades_df.columns else []

    live_prices = _fetch_live_prices(list(set(alert_tickers + position_tickers)))

    return {
        "label":       meta["label"],
        "universe":    meta["universe"],
        "lastUpdated": file_date.strftime("%a %d %b %Y"),
        "kpis":        _build_kpis(equity_df, analytics_df),
        "returns":     _build_returns(analytics_df),
        "equityCurve": _build_equity_curve(equity_df),
        "alerts":      _build_alerts(alerts_df, company_df, live_prices),
        "positions":   _build_positions(trades_df, company_df, live_prices),
    }
