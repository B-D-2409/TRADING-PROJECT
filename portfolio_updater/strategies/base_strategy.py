import logging
from datetime import datetime
from utils.config_loader import load_config
from utils.company_data import nd_timeseries
from utils.file_io import read_excel_sheet, copy_most_recent_file, overwrite_excel_sheet
from utils.trades import update_trade_prices, update_trade_list
from utils.equity import get_equity_value, update_equity_curve
from utils.market import update_market_performance

class BaseStrategy:
    def __init__(self, config_path):
        self.config = load_config(config_path)
        self.name = self.config["name"]
        self.freq = self.config["freq"]
        self.comms = self.config["commissions"]
        self.buy_criteria = self.config["buy_criteria"]
        self.sell_criteria = self.config["sell_criteria"]
        self.index_filter = self.config["index_filter"]
        self.directory = self.config["directory"]

    # ---------- Utility ----------
    def log(self, message):
        logging.info(f"[{self.name}] {message}")

    def market_traded_today(self):
        """Check if market traded by comparing last 2 daily bars"""
        indexdf = nd_timeseries(self.index_filter, datetime.now().date(), 'D')
        indexdf_date = indexdf.index[-1]
        if indexdf_date.date() == datetime.now().date():
            return True
        else:
            return False
    
    def load_positions(self):
        """Read current positions file"""
        return read_excel_sheet(
            directory_path=self.directory,
            sheet="Company Page Data"
        )
    def load_buy_sell_alerts(self):
        """Read Buy/Sell Alerts data"""
        return read_excel_sheet(
            directory_path=self.directory,
            sheet="Buy Sell Alerts"
        )

    def load_trades(self):
        """Read trades data"""
        return read_excel_sheet(
            directory_path=self.directory,
            sheet="Trades"
        )

    def load_equity_curve(self):
        """Read equity curve data"""
        return read_excel_sheet(
            directory_path=self.directory,
            sheet="Equity Curve"
        )

    def save_trades(self, trades_df):
        """Save trades data back to Excel sheet"""
        # Find the most recent file to update
        from pathlib import Path
        dir_path = Path(self.directory)
        files = [f for f in dir_path.iterdir() 
                if f.is_file() and f.suffix.lower() in ['.xlsx', '.xlsm']]
        if not files:
            raise FileNotFoundError(f"No Excel files found in directory: {dir_path}")
        most_recent_file = max(files, key=lambda f: f.stat().st_mtime)
        
        overwrite_excel_sheet(
            path=most_recent_file,
            df=trades_df,
            sheet="Trades",
            index=False
        )

    def save_equity_curve(self, equity_curve_df):
        """Save equity curve data back to Excel sheet"""
        from pathlib import Path
        dir_path = Path(self.directory)
        files = [f for f in dir_path.iterdir() 
                if f.is_file() and f.suffix.lower() in ['.xlsx', '.xlsm']]
        if not files:
            raise FileNotFoundError(f"No Excel files found in directory: {dir_path}")
        most_recent_file = max(files, key=lambda f: f.stat().st_mtime)
        
        overwrite_excel_sheet(
            path=most_recent_file,
            df=equity_curve_df,
            sheet="Equity Curve",
            index=False
        )

    def save_xjo(self, xjo_df):
        """Save XJO data back to Excel sheet"""
        from pathlib import Path
        dir_path = Path(self.directory)
        files = [f for f in dir_path.iterdir() 
                if f.is_file() and f.suffix.lower() in ['.xlsx', '.xlsm']]
        if not files:
            raise FileNotFoundError(f"No Excel files found in directory: {dir_path}")
        most_recent_file = max(files, key=lambda f: f.stat().st_mtime)
        
        overwrite_excel_sheet(
            path=most_recent_file,
            df=xjo_df,
            sheet="XJO",
            index=False
        )
    # ---------- Daily Workflow ----------
    def daily_workflow(self):
        """Execute daily workflow for strategy processing."""
        self.log("Starting daily workflow...")
        
        # Check if market traded today
        if not self.market_traded_today():
            self.log("Market did not trade today. Exiting workflow.")
            return
        
        self.log("Market traded today. Proceeding with workflow...")
        
        # Create copy of most recent data file to update
        try:
            backup_filename = f"{datetime.now().date()}-data-{self.name}"
            copy_most_recent_file(self.directory, backup_filename)
            self.log(f"Successfully created backup: {backup_filename}")
        except FileNotFoundError as e:
            self.log(f"Warning: Could not create backup - {e}")
        except Exception as e:
            self.log(f"Error creating backup: {e}")
            # Continue workflow despite backup failure
        
        self.log("Proceeding with data processing...")

        # load equity curve
        equity_curve_df = self.load_equity_curve()
        cash = equity_curve_df.iloc[-1]['Cash']

        # Load and update trade prices
        trades_df = self.load_trades()
        updated_trades_df, updated_cash = update_trade_prices(trades_df, cash, self.comms, datetime.now().date())
        self.save_trades(updated_trades_df)
        self.log("Trade prices updated and saved.")

        # update equity curve
        current_equity = get_equity_value(updated_trades_df, updated_cash, datetime.now().date())
        updated_equity_curve_df = update_equity_curve(equity_curve_df, current_equity, datetime.now().date(), updated_cash)
        self.save_equity_curve(updated_equity_curve_df)
        self.log("Equity curve updated and saved.")

        # load and update market performance
        xjo_df = read_excel_sheet(
            directory_path=self.directory,
            sheet="XJO"
        )
        updated_xjo_df = update_market_performance(xjo_df, self.index_filter, datetime.now().date(), 'D')
        self.save_xjo(updated_xjo_df)
        self.log("Market performance updated and saved.")

        self.log("Daily workflow complete.")


    # ---------- Weekly Workflow ----------
    def weekly_workflow(self):
        self.log("Starting weekly workflow...")

        # Create copy of most recent data file to update
        try:
            backup_filename = f"{datetime.now().date()}-data-{self.name}"
            copy_most_recent_file(self.directory, backup_filename)
            self.log(f"Successfully created backup: {backup_filename}")
        except FileNotFoundError as e:
            self.log(f"Warning: Could not create backup - {e}")
        except Exception as e:
            self.log(f"Error creating backup: {e}")
            # Continue workflow despite backup failure
        
        self.log("Proceeding with data processing...")

        # update market performance
        xjo_df = read_excel_sheet(
            directory_path=self.directory,
            sheet="XJO"
        )
        updated_xjo_df = update_market_performance(xjo_df, self.index_filter, datetime.now().date(), 'W')
        self.save_xjo(updated_xjo_df)
        self.log("Market performance updated and saved.")

        self.log("Daily workflow complete.")

        # load and update trade prices
        trades_df = self.load_trades()
        updated_trades_df = update_trade_list(trades_df, datetime.now().date(), self.comms)

        # load and update equity curve
        equity_curve_df = self.load_equity_curve()
        cash = equity_curve_df.iloc[-1]['Cash']
        current_equity = get_equity_value(updated_trades_df, cash, datetime.now().date())
        updated_equity_curve_df = update_equity_curve(equity_curve_df, current_equity, datetime.now().date(), cash)
        self.save_equity_curve(updated_equity_curve_df)
        self.log("Equity curve updated and saved.")
        
        ## process buy and sell alerts
        # load positions
        positions_df = self.load_positions()
        positions = positions_df['Code'].to_list()
        

        
        
        
        
        
        
        
        
        
        
        
        
        
        self.load_positions()
        self.update_fundamentals()

        self.load_buy_sell_alerts()
        self.update_prices_for_open_positions()
        self.update_fundamentals()  # second update

        self.load_equity_curve()
        self.calc_recent_performance()

        self.load_trades()
        self.update_open_positions_data()
        self.calc_portfolio_stats()

        self.check_for_sell_orders()
        self.check_for_buy_orders()

        self.log("Weekly workflow complete.")

    def update_fundamentals(self):
        raise NotImplementedError

    def update_prices_for_open_positions(self):
        raise NotImplementedError

    def calc_recent_performance(self):
        raise NotImplementedError

    def update_open_positions_data(self):
        raise NotImplementedError

    def calc_portfolio_stats(self):
        raise NotImplementedError

    def check_for_sell_orders(self):
        """Find positions to sell, update alerts & closed trades"""
        raise NotImplementedError

    def check_for_buy_orders(self):
        """Find positions to buy, update alerts & portfolio"""
        raise NotImplementedError

    # ---------- Monthly Workflow ----------
    def monthly_workflow(self):
        self.log("Starting monthly workflow...")

        self.load_positions()
        self.calc_monthly_performance()
        self.update_monthly_performance_tab()

        self.update_equity_curve()

        self.load_buy_sell_alerts()
        self.update_analytics()

        self.log("Monthly workflow complete.")

    def calc_monthly_performance(self):
        raise NotImplementedError

    def update_monthly_performance_tab(self):
        raise NotImplementedError

    def update_analytics(self):
        raise NotImplementedError
