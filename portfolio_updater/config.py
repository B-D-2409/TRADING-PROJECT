#%%
# config.py
# Central configuration for portfolio_updater.
#
# ALL hardcoded paths found across the codebase are extracted here.
# To move the project to a new machine, only this file needs editing.
#
# Sources audited:
#   - daily.py               → ./test/2025-08-03-data-large-UPDATED.xlsx
#   - utils/signals.py       → 'large_cap/live_sheets/', '../SMAs/watchlists/'
#   - utils/company_data_all.py → 'Y:\AusBiz\...'
#   - utils/divy_and_port_val.py → 'Y:\AusBiz\portfolio_updater\output\...'
#   - strategies/large_cap_strategy.py → '{name}/live_sheets'

import os
from pathlib import Path

#%%
# ── Project Root ──────────────────────────────────────────────────────────────
# Resolves to the directory containing this config.py file, regardless of
# where the script is called from.
PROJECT_ROOT = Path(__file__).resolve().parent

#%%
# ── Output Directories ────────────────────────────────────────────────────────
# Weekly Excel snapshots are written here by each strategy.
OUTPUT_DIR           = PROJECT_ROOT / "output"
LARGE_CAP_OUTPUT_DIR = OUTPUT_DIR / "large_cap"
MID_CAP_OUTPUT_DIR   = OUTPUT_DIR / "mid_cap"
INCOME_OUTPUT_DIR    = OUTPUT_DIR / "income"

# Legacy live-sheets subdirectory (CSV intermediates used by process_signals).
# Previously hardcoded as 'large_cap/live_sheets/' in signals.py line 181.
LARGE_CAP_LIVE_SHEETS = LARGE_CAP_OUTPUT_DIR / "live_sheets"
MID_CAP_LIVE_SHEETS   = MID_CAP_OUTPUT_DIR   / "live_sheets"
INCOME_LIVE_SHEETS    = INCOME_OUTPUT_DIR     / "live_sheets"

#%%
# ── Strategy Config Files ─────────────────────────────────────────────────────
# JSON parameter files for each strategy.
# NOTE: these are currently 0 bytes — see configs/NOTE.txt.
# Populate them before running any strategy workflow.
CONFIGS_DIR           = PROJECT_ROOT / "configs"
LARGE_CAP_CONFIG_PATH = CONFIGS_DIR / "large_cap_config.json"
MID_CAP_CONFIG_PATH   = CONFIGS_DIR / "mid_cap_config.json"
INCOME_CONFIG_PATH    = CONFIGS_DIR / "income_config.json"

#%%
# ── External Watchlist / Universe Files ───────────────────────────────────────
# xjo.csv and xao.csv live in a sibling directory outside this repo.
# Previously hardcoded as '../SMAs/watchlists/' in signals.py lines 192-201.
# Override the WATCHLISTS_DIR environment variable to redirect on a new machine.
WATCHLISTS_DIR = Path(
    os.environ.get("WATCHLISTS_DIR", str(PROJECT_ROOT.parent / "SMAs" / "watchlists"))
)

#%%
# ── Test / Development Data ───────────────────────────────────────────────────
# Directory for ad-hoc Excel files used during development.
# Previously hardcoded as './test/2025-08-03-data-large-UPDATED.xlsx' in daily.py.
TEST_DIR = PROJECT_ROOT / "test"

#%%
# ── Legacy Windows Export Path ────────────────────────────────────────────────
# Previously hardcoded as 'Y:\AusBiz\' in company_data_all.py and
# divy_and_port_val.py.
# Set the AUSBIZ_EXPORT_DIR environment variable or edit the fallback below
# to redirect CSV exports on a new machine.
LEGACY_EXPORT_DIR = Path(
    os.environ.get("AUSBIZ_EXPORT_DIR", str(OUTPUT_DIR / "legacy_exports"))
)

#%%
# ── React Frontend JSON Export ────────────────────────────────────────────────
# Where react_exporter.py writes its output JSON files.
REACT_EXPORT_DIR = OUTPUT_DIR / "react"

#%%
# ── Lookup Dicts (used by main.py and react_exporter.py) ──────────────────────
# Single source of truth for mapping a strategy name to its paths.

STRATEGY_OUTPUT_DIRS = {
    "large_cap": LARGE_CAP_OUTPUT_DIR,
    "mid_cap":   MID_CAP_OUTPUT_DIR,
    "income":    INCOME_OUTPUT_DIR,
}

STRATEGY_LIVE_SHEETS_DIRS = {
    "large_cap": LARGE_CAP_LIVE_SHEETS,
    "mid_cap":   MID_CAP_LIVE_SHEETS,
    "income":    INCOME_LIVE_SHEETS,
}

STRATEGY_CONFIG_PATHS = {
    "large_cap": LARGE_CAP_CONFIG_PATH,
    "mid_cap":   MID_CAP_CONFIG_PATH,
    "income":    INCOME_CONFIG_PATH,
}
