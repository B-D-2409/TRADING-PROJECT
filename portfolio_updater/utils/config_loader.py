#%%
# utils/config_loader.py
# Loads a JSON strategy config file from disk and returns it as a dict.
#
# Imported by:
#   - strategies/base_strategy.py     (from utils.config_loader import load_config)
#   - strategies/mid_cap_strategy.py  (from config_loader import load_config)
#   - strategies/income_strategy.py   (from config_loader import load_config)

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

#%%
# ── Config loader ─────────────────────────────────────────────────────────────

def load_config(config_path: str | Path) -> dict:
    """
    Load a JSON config file and return its contents as a dict.

    Args:
        config_path: Path to the .json config file (str or Path).

    Returns:
        Parsed config dict.

    Raises:
        FileNotFoundError: If the file does not exist at the given path.
        ValueError: If the file is empty (configs not yet populated).
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    p = Path(config_path)

    # Check the file exists before attempting to open it
    if not p.exists():
        raise FileNotFoundError(
            f"Config file not found: {p}\n"
            "Ensure the path is correct and the file exists."
        )

    # Guard against empty config files (see configs/NOTE.txt)
    if p.stat().st_size == 0:
        raise ValueError(
            f"Config file is empty: {p}\n"
            "Populate this file with trading rules and universe settings "
            "before running the strategy. See the *.txt rules files for reference."
        )

    # Read and parse the JSON
    with p.open("r", encoding="utf-8") as f:
        config = json.load(f)

    logger.info(f"Loaded config '{p.name}': {list(config.keys())}")
    return config
