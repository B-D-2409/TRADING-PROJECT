import sys
import os
from pathlib import Path
from unittest.mock import MagicMock
import argparse
import logging
from datetime import date

#%%
root_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, root_path)
sys.path.append(os.path.join(root_path, 'utils'))
sys.path.append(os.path.join(root_path, 'strategies'))

try:
    import norgatedata
except ImportError:
    mock_nd = MagicMock()
    mock_nd.StockPriceAdjustmentType.TOTALRETURN = 1
    mock_nd.StockPriceAdjustmentType.NONE = 0
    mock_nd.PaddingType.NONE = 0
    mock_nd.status.return_value = "Not Running"
    sys.modules["norgatedata"] = mock_nd

#%%
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

#%%
from utils.data_factory import _PROVIDER as _DATA_PROVIDER
logger.info(f"Active data provider: {_DATA_PROVIDER.upper()}")

from strategies.base_strategy import BaseStrategy
from strategies.large_cap_strategy import LargeCapStrategy
from strategies.mid_cap_strategy import MidCapStrategy
from strategies.income_strategy import IncomeStrategy
from config import STRATEGY_CONFIG_PATHS

#%%
STRATEGY_REGISTRY = {
    "large_cap": LargeCapStrategy,
    "mid_cap":   MidCapStrategy,
    "income":    IncomeStrategy,
}

#%%
def build_strategy(name: str, asof_date: str | None = None) -> BaseStrategy:
    """Instantiate and return a strategy object by name, loading its config from disk."""
    if name not in STRATEGY_REGISTRY:
        raise ValueError(f"Unknown strategy '{name}'. Valid choices: {list(STRATEGY_REGISTRY.keys())}")

    run_date     = asof_date if asof_date else date.today().isoformat()
    config_path  = STRATEGY_CONFIG_PATHS[name]
    strategy_cls = STRATEGY_REGISTRY[name]

    logger.info(f"[{name}] Building strategy — config: {config_path} | date: {run_date}")

    if name == "large_cap":
        from utils.config_loader import load_config
        config = load_config(config_path)
        return strategy_cls(config=config, asof_date=run_date)

    return strategy_cls()


def run_workflow(strategy: BaseStrategy, workflow: str) -> None:
    """Dispatch the named workflow method on the given strategy and log its execution boundaries."""
    dispatch = {
        "daily":   strategy.daily_workflow,
        "weekly":  strategy.weekly_workflow,
        "monthly": strategy.monthly_workflow,
    }

    if workflow not in dispatch:
        raise ValueError(f"Unknown workflow '{workflow}'. Valid choices: {list(dispatch.keys())}")

    logger.info(f"[{strategy.name}] ── Starting {workflow.upper()} workflow ──")
    dispatch[workflow]()
    logger.info(f"[{strategy.name}] ── {workflow.capitalize()} workflow complete ──")


def build_parser() -> argparse.ArgumentParser:
    """Define and return the CLI argument parser for portfolio_updater."""
    parser = argparse.ArgumentParser(prog="portfolio_updater")
    parser.add_argument(
        "--strategy",
        choices=["large_cap", "mid_cap", "income", "all"],
        required=True,
    )

    workflow_group = parser.add_mutually_exclusive_group(required=True)
    workflow_group.add_argument("--run-daily",   action="store_true", dest="run_daily")
    workflow_group.add_argument("--run-weekly",  action="store_true", dest="run_weekly")
    workflow_group.add_argument("--run-monthly", action="store_true", dest="run_monthly")

    parser.add_argument("--date",    type=str, default=None, metavar="YYYY-MM-DD")
    parser.add_argument("--dry-run", action="store_true", dest="dry_run")

    return parser

#%%
def main() -> None:
    """Parse CLI arguments and execute the requested workflow for each selected strategy."""
    parser = build_parser()
    args   = parser.parse_args()

    if args.run_daily:
        workflow = "daily"
    elif args.run_weekly:
        workflow = "weekly"
    else:
        workflow = "monthly"

    run_date       = args.date or date.today().isoformat()
    strategy_names = list(STRATEGY_REGISTRY.keys()) if args.strategy == "all" else [args.strategy]

    logger.info("=" * 60)
    logger.info("portfolio_updater starting")
    logger.info(f"Workflow  : {workflow.upper()}")
    logger.info(f"Strategies: {strategy_names}")
    logger.info(f"As-of date: {run_date}")
    logger.info("=" * 60)

    if args.dry_run:
        logger.info("DRY RUN — no workflows will be executed")
        for name in strategy_names:
            logger.info(f"  Would run: {workflow} | strategy: {name} | date: {run_date}")
        return

    for name in strategy_names:
        logger.info(f"[{name}] ── Execution starting ──")
        try:
            strategy = build_strategy(name, asof_date=args.date)
            run_workflow(strategy, workflow)
            logger.info(f"[{name}] ── Execution finished successfully ──")
        except Exception as e:
            logger.exception(f"[{name}] Fatal error during {workflow} workflow: {e}")
            raise

    logger.info("portfolio_updater finished")


if __name__ == "__main__":
    main()
