import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

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


def _to_float(value, default: float = 0.0) -> float:
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


def _build_kpis(
    equity_df:    pd.DataFrame,
    analytics_df: Optional[pd.DataFrame],
) -> dict:
    empty_result = {"equity": 0.0, "cash": 0.0, "totalReturn": 0.0, "maxDrawdown": 0.0}

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

    total_return = 0.0
    max_drawdown = 0.0

    if (
        analytics_df is not None
        and not analytics_df.empty
        and analytics_df.shape[1] >= 2
    ):
        col_keys = analytics_df.iloc[:, 0].astype(str).str.lower().str.strip()
        col_vals = analytics_df.iloc[:, 1]
        metrics  = dict(zip(col_keys, col_vals))
        for key, val in metrics.items():
            if "annual return" in key:
                total_return = _to_float(val)
            if "drawdown" in key and "max" in key:
                max_drawdown = _to_float(val)

    if total_return == 0.0 and len(clean) > 1:
        first_equity = float(clean["_equity"].iloc[0])
        if first_equity > 0:
            total_return = round((equity / first_equity - 1) * 100, 2)

    if max_drawdown == 0.0 and "Drawdown %:" in clean.columns:
        dd_series = pd.to_numeric(clean["Drawdown %:"], errors="coerce")
        if not dd_series.isna().all():
            max_drawdown = round(float(dd_series.min()), 2)

    return {
        "equity":      round(equity, 2),
        "cash":        round(cash, 2),
        "totalReturn": round(total_return, 2),
        "maxDrawdown": round(max_drawdown, 2),
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

    return [
        {
            "date":  _fmt_date_short(row.get("Date:", "")),
            "value": round(float(row["_equity"]), 2),
        }
        for _, row in clean.iterrows()
    ]


def _build_alerts(alerts_df: pd.DataFrame) -> list[dict]:
    if alerts_df.empty or "Code:" not in alerts_df.columns:
        return []

    result = []
    for _, row in alerts_df.iterrows():
        ticker = _to_str(row.get("Code:"))
        action = _to_str(row.get("Action:")).upper()
        if not ticker or not action:
            continue
        stop_type = _to_str(row.get("Stop Type:", ""))
        result.append({
            "ticker": ticker,
            "action": action,
            "date":   _fmt_date(row.get("Date:", "")),
            "reason": stop_type if stop_type else "Momentum Signal",
        })
    return result


def _build_positions(
    trades_df:  pd.DataFrame,
    company_df: Optional[pd.DataFrame],
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
                "name":         _to_str(row.get("Name:")),
                "sector":       _to_str(row.get("Sector:")),
                "currentPrice": _to_float(row.get("Last Price:")),
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

        current_price = company.get("currentPrice") or (
            round(entry_price * (1.0 + pct_chg / 100.0), 4)
            if entry_price and pct_chg
            else 0.0
        )

        result.append({
            "ticker":       ticker,
            "name":         company.get("name", ""),
            "sector":       company.get("sector", ""),
            "shares":       shares,
            "entryPrice":   round(entry_price, 4),
            "currentPrice": round(float(current_price), 4),
            "profitDollar": round(profit_dollar, 2),
            "profitPct":    round(profit_pct, 2),
        })

    return result


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

    return {
        "label":       meta["label"],
        "universe":    meta["universe"],
        "lastUpdated": file_date.strftime("%a %d %b %Y"),
        "kpis":        _build_kpis(equity_df, analytics_df),
        "equityCurve": _build_equity_curve(equity_df),
        "alerts":      _build_alerts(alerts_df),
        "positions":   _build_positions(trades_df, company_df),
    }
