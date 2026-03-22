"""
Public API for portfolio_updater.utils

Usage:
    from portfolio_updater.utils import read_excel_sheet, overwrite_excel_sheet
"""

from __future__ import annotations
import importlib

# Everything you want to expose from utils
__all__ = [
    # equity
    "get_equity_value", "update_equity_curve",
    # company_data
    "nd_timeseries", "nd_div", "roundToTick", "orderPriceRounding", "fundamental_data",
    # data_factory
    "get_data", "get_dividend", "get_fundamentals",
    # signals
    "momentum_score", "process_signals",
    # trades
    "update_trade_list",
    # analytics
    "performance_analytics",
    # file_io
    "read_in_data", "save_data", "combine_data", "read_excel_sheet", "overwrite_excel_sheet",
    # config_loader
    "load_config",
    # react_exporter
    "export_strategy_data",
]

# Map public names -> (module, attribute)
_exports = {
    # equity
    "get_equity_value": ("equity", "get_equity_value"),
    "update_equity_curve": ("equity", "update_equity_curve"),

    # company_data
    "nd_timeseries": ("company_data", "nd_timeseries"),
    "nd_div": ("company_data", "nd_div"),
    "roundToTick": ("company_data", "roundToTick"),
    "orderPriceRounding": ("company_data", "orderPriceRounding"),
    "fundamental_data": ("company_data", "fundamental_data"),

    # data_factory
    "get_data": ("data_factory", "get_data"),
    "get_dividend": ("data_factory", "get_dividend"),
    "get_fundamentals": ("data_factory", "get_fundamentals"),

    # signals
    "momentum_score": ("signals", "momentum_score"),
    "process_signals": ("signals", "process_signals"),

    # trades
    "update_trade_list": ("trades", "update_trade_list"),

    # analytics
    "performance_analytics": ("analytics", "performance_analytics"),

    # file_io
    "read_in_data": ("file_io", "read_in_data"),
    "save_data": ("file_io", "save_data"),
    "combine_data": ("file_io", "combine_data"),
    "read_excel_sheet": ("file_io", "read_excel_sheet"),
    "overwrite_excel_sheet": ("file_io", "overwrite_excel_sheet"),

    # config_loader
    "load_config": ("config_loader", "load_config"),

    # react_exporter
    "export_strategy_data": ("react_exporter", "export_strategy_data"),
}

def __getattr__(name: str):
    """Lazy re-export to avoid circular imports and speed import time."""
    try:
        mod_name, attr = _exports[name]
    except KeyError:
        raise AttributeError(f"module 'utils' has no attribute {name!r}") from None
    module = importlib.import_module(f".{mod_name}", __name__)
    return getattr(module, attr)

def __dir__():
    return sorted(set(globals().keys()) | set(__all__))
