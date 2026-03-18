#%%
# main.py
# Entry point for the portfolio_updater automation system.
#
# Exposes daily, weekly, and monthly workflow commands via argparse.
# This file is the single place that wires together config, strategy classes,
# and workflow execution — no business logic lives here.
#
# Usage examples:
#   python main.py --strategy large_cap --run-daily
#   python main.py --strategy mid_cap   --run-weekly
#   python main.py --strategy income    --run-monthly
#   python main.py --strategy all       --run-weekly
#   python main.py --strategy large_cap --run-daily  --dry-run
#   python main.py --strategy large_cap --run-weekly --date 2025-08-03

import argparse
import logging
import sys
from datetime import date
from pathlib import Path

# Add project root to sys.path so all imports resolve from any working directory
sys.path.insert(0, str(Path(__file__).resolve().parent))

#%%
# ── Logging setup ─────────────────────────────────────────────────────────────
# Match the logging format already used in daily.py and base_strategy.py
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

#%%
# ── Strategy registry ─────────────────────────────────────────────────────────
# Import all concrete strategy classes here.
# Adding a new strategy: add its class and config path to these two dicts.
from strategies.base_strategy    import BaseStrategy
from strategies.large_cap_strategy import LargeCapStrategy
from strategies.mid_cap_strategy   import MidCapStrategy
from strategies.income_strategy    import IncomeStrategy
from config import STRATEGY_CONFIG_PATHS

STRATEGY_REGISTRY = {
    "large_cap": LargeCapStrategy,
    "mid_cap":   MidCapStrategy,
    "income":    IncomeStrategy,
}

#%%
# ── Strategy factory ──────────────────────────────────────────────────────────

def build_strategy(name: str, asof_date: str | None = None) -> BaseStrategy:
    """
    Instantiate a strategy by name, loading its config from disk.

    NOTE: LargeCapStrategy has a different __init__ signature to BaseStrategy
    (it expects a pre-loaded config dict + asof_date rather than a config path).
    This divergence is a known structural issue tracked separately — do not
    modify either class here to paper over it.

    Args:
        name:       Strategy name — one of 'large_cap', 'mid_cap', 'income'.
        asof_date:  ISO date string (YYYY-MM-DD). Defaults to today.

    Returns:
        An instantiated strategy object ready to call workflow methods on.
    """
    if name not in STRATEGY_REGISTRY:
        raise ValueError(
            f"Unknown strategy '{name}'. Valid: {list(STRATEGY_REGISTRY.keys())}"
        )

    # Default the as-of date to today if not supplied
    run_date = asof_date if asof_date else date.today().isoformat()
    config_path = STRATEGY_CONFIG_PATHS[name]
    strategy_cls = STRATEGY_REGISTRY[name]

    logger.info(f"[{name}] Building strategy (config: {config_path}, date: {run_date})")

    # LargeCapStrategy: expects (config_dict, asof_date) — handle separately
    if name == "large_cap":
        from utils.config_loader import load_config
        config = load_config(config_path)
        return strategy_cls(config=config, asof_date=run_date)

    # MidCapStrategy / IncomeStrategy: BaseStrategy-compatible path (config_path str)
    # These currently have stub workflows; they will execute without error.
    return strategy_cls()

#%%
# ── Workflow dispatcher ────────────────────────────────────────────────────────

def run_workflow(strategy: BaseStrategy, workflow: str) -> None:
    """
    Call the correct workflow method on a strategy instance.

    Args:
        strategy: An instantiated BaseStrategy subclass.
        workflow: One of 'daily', 'weekly', 'monthly'.
    """
    dispatch = {
        "daily":   strategy.daily_workflow,
        "weekly":  strategy.weekly_workflow,
        "monthly": strategy.monthly_workflow,
    }

    if workflow not in dispatch:
        raise ValueError(f"Unknown workflow '{workflow}'. Use: daily, weekly, monthly.")

    logger.info(f"[{strategy.name}] Starting {workflow} workflow...")
    dispatch[workflow]()
    logger.info(f"[{strategy.name}] {workflow.capitalize()} workflow complete.")

#%%
# ── CLI argument parser ───────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    """Define and return the CLI argument parser."""

    parser = argparse.ArgumentParser(
        prog="portfolio_updater",
        description=(
            "ASX portfolio management automation.\n\n"
            "Runs daily, weekly, or monthly update workflows for each strategy.\n\n"
            "Examples:\n"
            "  python main.py --strategy large_cap --run-weekly\n"
            "  python main.py --strategy all       --run-daily\n"
            "  python main.py --strategy income    --run-weekly --date 2025-08-03\n"
            "  python main.py --strategy mid_cap   --run-weekly --dry-run"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # ── Which strategy to run ─────────────────────────────────────────────────
    parser.add_argument(
        "--strategy",
        choices=["large_cap", "mid_cap", "income", "all"],
        required=True,
        help=(
            "Which strategy to update. "
            "Use 'all' to run all three strategies sequentially."
        ),
    )

    # ── Which workflow to trigger (mutually exclusive) ────────────────────────
    workflow_group = parser.add_mutually_exclusive_group(required=True)

    workflow_group.add_argument(
        "--run-daily",
        action="store_true",
        dest="run_daily",
        help=(
            "Run the daily workflow. "
            "Updates prices, equity curve, and XJO data on market days."
        ),
    )
    workflow_group.add_argument(
        "--run-weekly",
        action="store_true",
        dest="run_weekly",
        help=(
            "Run the weekly workflow. "
            "Generates buy/sell signals, updates trade list and equity curve."
        ),
    )
    workflow_group.add_argument(
        "--run-monthly",
        action="store_true",
        dest="run_monthly",
        help=(
            "Run the monthly workflow. "
            "Updates performance analytics and the monthly performance tab."
        ),
    )

    # ── Optional: override as-of date ─────────────────────────────────────────
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        metavar="YYYY-MM-DD",
        help=(
            "As-of date for the workflow run (default: today). "
            "Useful for reprocessing a prior week without changing system date."
        ),
    )

    # ── Optional: dry-run mode ────────────────────────────────────────────────
    parser.add_argument(
        "--dry-run",
        action="store_true",
        dest="dry_run",
        help=(
            "Print what would be executed without running any workflow. "
            "Safe to use at any time."
        ),
    )

    return parser

#%%
# ── Main entrypoint ───────────────────────────────────────────────────────────

def main() -> None:

    parser = build_parser()
    args = parser.parse_args()

    # Resolve which workflow to run from the mutually exclusive group
    if args.run_daily:
        workflow = "daily"
    elif args.run_weekly:
        workflow = "weekly"
    else:
        workflow = "monthly"

    # Resolve which strategies to run
    if args.strategy == "all":
        strategy_names = list(STRATEGY_REGISTRY.keys())
    else:
        strategy_names = [args.strategy]

    # Dry-run: print the execution plan and exit without touching anything
    if args.dry_run:
        logger.info("DRY RUN — no workflows will be executed.")
        for name in strategy_names:
            logger.info(
                f"  Would run: {workflow} workflow | strategy: '{name}' "
                f"| date: {args.date or date.today().isoformat()}"
            )
        return

    # Execute each requested strategy in order
    for name in strategy_names:
        try:
            strategy = build_strategy(name, asof_date=args.date)
            run_workflow(strategy, workflow)

        except (FileNotFoundError, ValueError) as e:
            # Config file missing or empty — expected until configs are populated
            logger.error(f"[{name}] Setup error: {e}")
            logger.error(
                f"[{name}] Skipping. "
                f"Populate configs/{name}_config.json to enable this strategy."
            )

        except NotImplementedError:
            # Workflow method is a stub in MidCapStrategy / IncomeStrategy
            logger.warning(
                f"[{name}] The '{workflow}' workflow is not yet implemented "
                "for this strategy. Skipping."
            )

        except Exception as e:
            # Unexpected error — log and re-raise to surface the full traceback
            logger.exception(f"[{name}] Unexpected error during {workflow} workflow: {e}")
            raise


if __name__ == "__main__":
    main()
