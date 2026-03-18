#%%
# utils/react_exporter.py
# Reads the final output Excel files and converts the key sheets into a
# structured JSON file suitable for consumption by a React.js frontend.
#
# The output JSON shape per strategy:
#   {
#     "strategy":       "large_cap",
#     "generated_at":   "2025-08-03T14:30:00",
#     "source_file":    "2025-08-03-data-large.xlsx",
#     "summary":        { current_equity, starting_equity, total_return_pct,
#                         max_drawdown_pct, current_cash },
#     "open_positions": [ { row per currently open trade } ],
#     "trades":         [ { row per closed or open trade } ],
#     "equity_curve":   [ { row per weekly snapshot } ],
#     "buy_sell_alerts":[ { row per current signal } ]
#   }
#
# Standalone usage:
#   python utils/react_exporter.py --strategy large_cap
#   python utils/react_exporter.py --strategy all --output-dir ./output/react
#
# Programmatic usage:
#   from utils.react_exporter import export_strategy_data
#   path = export_strategy_data("large_cap")

import argparse
import json
import logging
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

#%%
# ── JSON serialisation helpers ────────────────────────────────────────────────

def _serialise_value(val: Any) -> Any:
    """
    Convert a single pandas/numpy value into a JSON-safe Python native type.

    Handles:
      - NaN / NaT / None  → None
      - datetime / Timestamp → ISO 8601 string
      - date              → ISO 8601 string  (e.g. "2025-08-03")
      - numpy int/float   → int/float  (via .item())
      - everything else   → unchanged
    """
    # Check for null/NaN first — pd.isna handles NaT, float NaN, and None
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        # pd.isna raises on some objects (e.g. lists) — treat as non-null
        pass

    # Convert datetime and Timestamp to ISO string
    if isinstance(val, (datetime, pd.Timestamp)):
        return val.isoformat()

    # Convert date (but not datetime, already handled above) to ISO string
    if isinstance(val, date):
        return val.isoformat()

    # Convert numpy scalars (int64, float64, etc.) to native Python types
    if hasattr(val, "item"):
        return val.item()

    return val


def _dataframe_to_records(df: pd.DataFrame) -> list[dict]:
    """
    Convert a DataFrame to a list of row dicts with JSON-safe values.

    Each row becomes one dict; column names become the dict keys.
    """
    records = []
    for _, row in df.iterrows():
        records.append({col: _serialise_value(row[col]) for col in df.columns})
    return records

#%%
# ── Excel sheet readers ───────────────────────────────────────────────────────

def _read_sheet(excel_path: Path, sheet_name: str) -> pd.DataFrame:
    """
    Read a single named sheet from an Excel workbook.

    Args:
        excel_path: Path to the .xlsx file.
        sheet_name: Name of the sheet to read.

    Returns:
        DataFrame containing the sheet contents.
    """
    logger.info(f"Reading '{sheet_name}' from {excel_path.name}")
    return pd.read_excel(excel_path, sheet_name=sheet_name, engine="openpyxl")

#%%
# ── Most-recent file resolver ─────────────────────────────────────────────────

def _find_most_recent_excel(directory: Path) -> Path:
    """
    Return the most recently modified .xlsx file in a directory.

    Uses modification time (mtime) to match the behaviour of
    file_io.read_excel_sheet() so both functions always target the same file.

    Raises:
        FileNotFoundError: If no .xlsx files are found in the directory.
    """
    files = [
        f for f in directory.iterdir()
        if f.is_file() and f.suffix.lower() == ".xlsx"
    ]

    if not files:
        raise FileNotFoundError(f"No .xlsx files found in: {directory}")

    # Sort by last-modified timestamp and return the newest
    most_recent = max(files, key=lambda f: f.stat().st_mtime)
    logger.info(f"Most recent file: {most_recent.name}")
    return most_recent

#%%
# ── Equity curve summary ──────────────────────────────────────────────────────

def _build_summary(equity_df: pd.DataFrame) -> dict:
    """
    Build a compact summary dict from the equity curve DataFrame.

    Searches for columns by substring match so the function tolerates minor
    naming variations (e.g. 'Portfolio Equity:' vs 'Portfolio Equity').

    Returns:
        Dict with keys: current_equity, starting_equity, total_return_pct,
                        max_drawdown_pct, current_cash.
    """
    if equity_df.empty:
        return {}

    cols = equity_df.columns.tolist()

    # Locate each column by substring — tolerates the trailing-colon convention
    def find_col(keyword: str) -> str | None:
        return next((c for c in cols if keyword.lower() in c.lower()), None)

    equity_col   = find_col("equity")
    drawdown_col = next(
        (c for c in cols if "drawdown" in c.lower() and "%" in c), None
    )
    cash_col = find_col("cash")

    summary = {}

    # Current and starting equity values
    if equity_col:
        start = equity_df[equity_col].iloc[0]
        end   = equity_df[equity_col].iloc[-1]
        summary["current_equity"]  = _serialise_value(end)
        summary["starting_equity"] = _serialise_value(start)

        # Total return % from first row to last row
        if start and start != 0:
            summary["total_return_pct"] = round(((end / start) - 1) * 100, 2)

    # Maximum drawdown (the most negative value in the drawdown % column)
    if drawdown_col:
        summary["max_drawdown_pct"] = _serialise_value(
            equity_df[drawdown_col].min()
        )

    # Current cash balance from the last equity curve row
    if cash_col:
        summary["current_cash"] = _serialise_value(
            equity_df[cash_col].iloc[-1]
        )

    return summary

#%%
# ── Open positions filter ─────────────────────────────────────────────────────

def _extract_open_positions(trades_df: pd.DataFrame) -> list[dict]:
    """
    Filter the trades DataFrame to only currently open positions.

    A row is considered open if its 'Trade:' column contains the word 'Open'
    (matches both 'Open Long' and any future variants).

    Returns:
        List of row dicts for open positions only.
    """
    if trades_df.empty or "Trade:" not in trades_df.columns:
        return []

    # Filter to rows where the Trade: status indicates an open position
    open_mask = trades_df["Trade:"].str.contains("Open", na=False)
    return _dataframe_to_records(trades_df[open_mask])

#%%
# ── Main export function ───────────────────────────────────────────────────────

def export_strategy_data(
    strategy_name: str,
    output_dir: Path | None = None,
    source_dir: Path | None = None,
) -> Path:
    """
    Read the most recent Excel output for a strategy and write a JSON file
    ready for a React.js frontend.

    Args:
        strategy_name: One of 'large_cap', 'mid_cap', 'income'.
        output_dir:    Where to write the JSON (default: output/react/).
        source_dir:    Directory containing the Excel files
                       (default: output/{strategy_name}/).

    Returns:
        Path to the written JSON file.
    """
    #%%
    # Resolve directories from config.py if not explicitly overridden
    from config import STRATEGY_OUTPUT_DIRS, REACT_EXPORT_DIR

    if source_dir is None:
        source_dir = STRATEGY_OUTPUT_DIRS.get(strategy_name)
        if source_dir is None:
            raise ValueError(
                f"Unknown strategy: '{strategy_name}'. "
                f"Valid: {list(STRATEGY_OUTPUT_DIRS.keys())}"
            )

    if output_dir is None:
        output_dir = REACT_EXPORT_DIR

    # Create the output directory if it doesn't already exist
    output_dir.mkdir(parents=True, exist_ok=True)

    #%%
    # Find the most recent Excel file in the strategy output directory
    excel_path = _find_most_recent_excel(source_dir)

    # Read the core sheets — Trades and Equity Curve are always expected
    trades_df       = _read_sheet(excel_path, "Trades")
    equity_curve_df = _read_sheet(excel_path, "Equity Curve")

    # Buy/Sell Alerts sheet may not exist in older output files — handle gracefully
    try:
        alerts_df = _read_sheet(excel_path, "Buy Sell Alerts")
    except Exception:
        logger.warning(
            f"'Buy Sell Alerts' sheet not found in {excel_path.name}. "
            "Setting to empty."
        )
        alerts_df = pd.DataFrame()

    #%%
    # Build the structured payload for the React frontend
    payload = {
        # Metadata
        "strategy":       strategy_name,
        "generated_at":   datetime.now().isoformat(),
        "source_file":    excel_path.name,

        # High-level performance numbers shown in a dashboard header/card
        "summary":        _build_summary(equity_curve_df),

        # Currently open positions (subset of trades — useful for a live table)
        "open_positions": _extract_open_positions(trades_df),

        # Full trade history (closed + open)
        "trades":         _dataframe_to_records(trades_df),

        # Weekly equity snapshots for the equity curve chart
        "equity_curve":   _dataframe_to_records(equity_curve_df),

        # Current week's buy/sell signals
        "buy_sell_alerts": _dataframe_to_records(alerts_df),
    }

    #%%
    # Write the JSON payload to disk
    output_path = output_dir / f"{strategy_name}_data.json"

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    logger.info(f"JSON export written → {output_path}")
    return output_path

#%%
# ── CLI interface (standalone usage) ──────────────────────────────────────────
# Run this file directly to export one or all strategies to JSON.
# Example: python utils/react_exporter.py --strategy all

if __name__ == "__main__":

    # Add project root to sys.path so 'from config import ...' resolves
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="Export portfolio data to JSON for the React frontend."
    )
    parser.add_argument(
        "--strategy",
        choices=["large_cap", "mid_cap", "income", "all"],
        required=True,
        help="Which strategy's data to export.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        metavar="PATH",
        help="Override the default output directory (output/react/).",
    )
    args = parser.parse_args()

    # Expand 'all' into individual strategy names
    strategies = (
        ["large_cap", "mid_cap", "income"]
        if args.strategy == "all"
        else [args.strategy]
    )

    # Loop through each requested strategy and export
    for name in strategies:
        try:
            out = export_strategy_data(name, output_dir=args.output_dir)
            print(f"[{name}] Exported → {out}")
        except FileNotFoundError as e:
            print(f"[{name}] No output file found: {e}")
        except Exception as e:
            print(f"[{name}] Export failed: {e}")
            raise
