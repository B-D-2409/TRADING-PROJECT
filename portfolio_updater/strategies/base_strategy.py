import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from utils.config_loader import load_config
from utils.company_data import nd_timeseries
from utils.file_io import read_excel_sheet, copy_most_recent_file, overwrite_excel_sheet
from utils.trades import update_trade_prices
from utils.equity import get_equity_value, update_equity_curve
from utils.market import update_market_performance
from utils.analytics import performance_analytics
from utils.data_factory import get_fundamentals, get_data

#%%
_COMPANY_PAGE_COLUMNS = [
    "Name:", "Code:", "Sector:", "Last Price:", "52-Week High:", "52-Week Low:",
    "Market Cap:", "Franking Level:", "Business Summary:",
    "P/E Ratio:", "Dividend Yield:", "P/S Ratio:", "P/FCF Ratio:",
    "Net Debt:", "Debt-to-Equity Ratio:", "Current Ratio:", "Free Cash Flow:",
    "Net Profit Margin:", "Revenue Growth (3-Year CAGR):", "EPS Growth (3-Year CAGR):", "ROE:",
]

#%%
class BaseStrategy:
    def __init__(self, config_source):
        if isinstance(config_source, dict):
            self.config = config_source
        else:
            self.config = load_config(config_source)

        self.name           = self.config.get("strategy_name", self.config.get("name"))
        self.freq           = self.config.get("rebalance_frequency", self.config.get("freq", "daily"))
        self.comms          = self.config.get("commissions", 0)
        self.buy_criteria   = self.config.get("buy_criteria")
        self.sell_criteria  = self.config.get("sell_criteria")
        self.index_filter   = self.config.get("index_filter", self.config.get("benchmark", "XJO"))
        self.directory      = self.config.get("folder", self.config.get("directory"))
        self.max_positions  = self.config.get("number_positions", 10)
        self.index_sma_period = self.config.get("index_sma_period", 40)

    # ── Internal utilities ────────────────────────────────────────────────────

    def log(self, message):
        logging.info(f"[{self.name}] {message}")

    def _asof_as_date(self):
        """Normalise self.asof_date (str or date) to a datetime.date object."""
        asof = getattr(self, 'asof_date', datetime.now().date())
        if isinstance(asof, str):
            return datetime.strptime(asof, "%Y-%m-%d").date()
        return asof

    def _next_monday(self):
        """Return the date of the next Monday relative to the as-of date."""
        asof = self._asof_as_date()
        days = (7 - asof.weekday()) % 7
        if days == 0:
            days = 7
        return asof + timedelta(days=days)

    def _index_above_ma(self):
        """Return True if the benchmark index close is above its configured SMA."""
        asof = self._asof_as_date()
        index_df = get_data(self.index_filter, ed=asof, freq='W')
        index_df['MA'] = index_df['Close'].rolling(window=self.index_sma_period).mean()
        return bool(index_df['Close'].iloc[-1] > index_df['MA'].iloc[-1])

    def _save_sheet(self, df: pd.DataFrame, sheet: str, index: bool = False) -> None:
        """Overwrite a named sheet in the most-recently modified Excel workbook."""
        from pathlib import Path
        dir_path = Path(self.directory)
        files = [
            f for f in dir_path.iterdir()
            if f.is_file() and f.suffix.lower() in ('.xlsx', '.xlsm')
        ]
        if not files:
            raise FileNotFoundError(f"No Excel files found in: {dir_path}")
        overwrite_excel_sheet(
            path=max(files, key=lambda f: f.stat().st_mtime),
            df=df,
            sheet=sheet,
            index=index,
        )

    def market_traded_today(self):
        target_date = self._asof_as_date()

        print(f"\n--- DEBUG ИНФО ---")
        print(f"1. Търсим дата: {target_date}")
        print(f"2. Търсим файл/индекс: {self.index_filter}")

        indexdf = nd_timeseries(self.index_filter, target_date, 'D')

        if indexdf is None or indexdf.empty:
            print("3. ГРЕШКА: nd_timeseries не върна никакви данни! Файлът е празен или не е намерен.")
            print("------------------\n")
            return False

        indexdf_date = indexdf.index[-1]
        print(f"4. Последната намерена дата в Ексела е: {indexdf_date}")

        if indexdf_date.date() == target_date:
            print("5. РЕЗУЛТАТ: Датите съвпадат! Пускам процеса.")
            print("------------------\n")
            return True
        else:
            print(f"5. РЕЗУЛТАТ: Разминаване! {indexdf_date.date()} не е равно на {target_date}")
            print("------------------\n")
            return False

    # ── Load helpers ──────────────────────────────────────────────────────────

    def load_trades(self):
        """Read the Trades sheet from the most recent workbook."""
        return read_excel_sheet(directory_path=self.directory, sheet="Trades")

    def load_equity_curve(self):
        """Read the Equity Curve sheet from the most recent workbook."""
        return read_excel_sheet(directory_path=self.directory, sheet="Equity Curve")

    def load_positions(self):
        """Read the Company Page Data sheet from the most recent workbook."""
        return read_excel_sheet(directory_path=self.directory, sheet="Company Page Data")

    def load_buy_sell_alerts(self):
        """Read the Buy Sell Alerts sheet from the most recent workbook."""
        return read_excel_sheet(directory_path=self.directory, sheet="Buy Sell Alerts")

    def load_analytics(self):
        """Read the Analytics sheet from the most recent workbook."""
        return read_excel_sheet(directory_path=self.directory, sheet="Analytics")

    def load_monthly_performance(self):
        """Read the Monthly Performance sheet from the most recent workbook."""
        return read_excel_sheet(directory_path=self.directory, sheet="Monthly Performance")

    # ── Save helpers ──────────────────────────────────────────────────────────

    def save_trades(self, df):
        self._save_sheet(df, "Trades")

    def save_equity_curve(self, df):
        self._save_sheet(df, "Equity Curve")

    def save_xjo(self, df):
        self._save_sheet(df, "XJO")

    def save_alerts(self, df):
        self._save_sheet(df, "Buy Sell Alerts")

    def save_company_page(self, df):
        self._save_sheet(df, "Company Page Data")

    def save_analytics(self, df):
        self._save_sheet(df, "Analytics", index=True)

    def save_monthly_performance(self, df):
        self._save_sheet(df, "Monthly Performance")

    # ── Daily Workflow ────────────────────────────────────────────────────────

    def daily_workflow(self):
        """
        Fill pending trade entry and exit prices using today's open price,
        update the cash balance, and append a new row to the equity curve.
        Skips execution on non-trading days.
        """
        self.log("Starting daily workflow...")

        if not self.market_traded_today():
            self.log("Market did not trade today. Exiting.")
            return

        equity_curve_df = self.load_equity_curve()
        trades_df       = self.load_trades()

        current_cash = float(equity_curve_df.iloc[-1]['Cash'])
        trades_df    = trades_df.replace({np.nan: '-', None: '-'})

        target_dt = self._asof_as_date()

        updated_trades_df, new_cash = update_trade_prices(
            trades_df, current_cash, self.comms, target_dt
        )

        portfolio_val  = get_equity_value(updated_trades_df, new_cash, target_dt)
        new_equity_df  = update_equity_curve(equity_curve_df, portfolio_val, target_dt, new_cash)

        self.save_trades(updated_trades_df)
        self.save_equity_curve(new_equity_df)

        self.log(f"Daily workflow complete. Portfolio value: {portfolio_val:.2f}, Cash: {new_cash:.2f}")

    # ── Weekly Workflow ───────────────────────────────────────────────────────

    def weekly_workflow(self):
        """
        End-of-week rebalance workflow:
          1. Create a dated backup of the live workbook.
          2. Fetch the latest benchmark bar and update the XJO equity curve.
          3. Load trades; normalise all NaN/None sentinels to '-'.
          4. Evaluate the index-filter condition (Close vs SMA).
          5. Identify stop-triggered exits via check_for_sell_orders (abstract).
          6. Identify new entries via check_for_buy_orders (abstract).
          7. Refresh current close prices and P&L metrics for all Open positions.
          8. Append a new row to the portfolio equity curve.
          9. Prepend any new sell/buy alerts to the Buy Sell Alerts sheet.
         10. Rebuild the Company Page Data sheet for the current holdings.
        """
        self.log("Starting weekly workflow...")

        backup_name = f"{self._asof_as_date()}-data-{self.name}"
        try:
            copy_most_recent_file(self.directory, backup_name)
            self.log(f"Backup created: {backup_name}")
        except Exception as e:
            self.log(f"Backup failed (non-fatal): {e}")

        xjo_df = read_excel_sheet(directory_path=self.directory, sheet="XJO")
        updated_xjo_df = update_market_performance(
            xjo_df, self.index_filter, self._asof_as_date(), 'W'
        )
        self.save_xjo(updated_xjo_df)
        self.log("Market benchmark updated.")

        equity_df  = self.load_equity_curve()
        trades_df  = self.load_trades()
        trades_df  = trades_df.replace({np.nan: '-', None: '-'})

        index_above_ma  = self._index_above_ma()
        next_monday     = self._next_monday()
        next_monday_str = next_monday.strftime('%d/%m/%Y')

        trades_df, sell_alerts_df = self.check_for_sell_orders(
            trades_df, equity_df, index_above_ma, next_monday_str
        )
        self.log(f"Sell check complete — {len(sell_alerts_df)} position(s) flagged.")

        trades_df, buy_alerts_df = self.check_for_buy_orders(
            trades_df, equity_df, index_above_ma, next_monday_str
        )
        self.log(f"Buy check complete — {len(buy_alerts_df)} new position(s) queued.")

        trades_df = self._refresh_open_position_metrics(trades_df)
        self.save_trades(trades_df)
        self.log("Trade metrics refreshed and saved.")

        cash           = float(equity_df.iloc[-1]['Cash'])
        portfolio_value = get_equity_value(trades_df, cash, self._asof_as_date())
        updated_equity_df = update_equity_curve(
            equity_df, portfolio_value, self._asof_as_date(), cash
        )
        self.save_equity_curve(updated_equity_df)
        self.log(f"Equity curve updated. Portfolio value: {portfolio_value:.2f}")

        if not sell_alerts_df.empty or not buy_alerts_df.empty:
            existing_alerts_df  = self.load_buy_sell_alerts()
            new_alerts_df       = pd.concat([sell_alerts_df, buy_alerts_df], ignore_index=True)
            updated_alerts_df   = pd.concat([new_alerts_df, existing_alerts_df], ignore_index=True)
            self.save_alerts(updated_alerts_df)
            self.log("Buy/sell alerts prepended and saved.")

        open_codes = trades_df.loc[trades_df['Trade:'] == 'Open', 'Code:'].tolist()
        if open_codes:
            company_data = [get_fundamentals(code) for code in open_codes]
            company_df   = pd.DataFrame(company_data, columns=_COMPANY_PAGE_COLUMNS)
            self.save_company_page(company_df)
            self.log(f"Company page refreshed for {len(open_codes)} holding(s).")

        self.log("Weekly workflow complete.")

    def _refresh_open_position_metrics(self, trades_df: pd.DataFrame) -> pd.DataFrame:
        """
        For every row where Trade: == 'Open', fetch the latest weekly close price
        and recalculate Ex. Price:, Ex. Date:, % chg:, % Profit:, and Profit:.
        Rows with non-numeric entry prices are skipped safely.
        """
        asof        = self._asof_as_date()
        asof_str    = asof.strftime('%d/%m/%Y')
        open_mask   = trades_df['Trade:'] == 'Open'

        for idx, row in trades_df[open_mask].iterrows():
            ticker = str(row['Code:']).split('.')[0] + '.au'
            try:
                price_data = nd_timeseries(ticker, asof, 'W')
                if price_data is None or price_data.empty:
                    continue
                current_price = float(price_data.iloc[-1]['Close'])
                entry_price   = pd.to_numeric(row['Price:'], errors='coerce')
                if pd.isna(entry_price):
                    continue
                shares      = float(row['Shares:'])
                pct_chg     = current_price / entry_price - 1
                pct_profit  = pct_chg - self.comms * 2
                profit      = entry_price * shares * pct_profit

                trades_df.at[idx, 'Ex. Price:']  = round(current_price, 3)
                trades_df.at[idx, 'Ex. Date:']   = asof_str
                trades_df.at[idx, '% chg:']      = f"{round(pct_chg * 100, 2)}%"
                trades_df.at[idx, '% Profit:']   = f"{round(pct_profit * 100, 2)}%"
                trades_df.at[idx, 'Profit:']     = round(profit, 2)
            except Exception:
                continue

        return trades_df

    def check_for_sell_orders(
        self,
        trades_df: pd.DataFrame,
        equity_df: pd.DataFrame,
        index_above_ma: bool,
        next_monday_str: str,
    ) -> tuple:
        """
        Subclass must implement. Evaluate both stop types for each Open position:
          - Regular trend stop: close <= N-week low.
          - Index stop (only when index_above_ma is False): close <= Week High * (1 - threshold).
        For each triggered position set:
          Trade: → 'Sell'
          Ex. Date: → next_monday_str
          Ex. Price:, % chg:, Profit:, % Profit: → '-'
        Returns (updated_trades_df, sell_alerts_df).
        sell_alerts_df must contain at minimum a 'Code:' column and an 'Action:' column.
        """
        raise NotImplementedError

    def check_for_buy_orders(
        self,
        trades_df: pd.DataFrame,
        equity_df: pd.DataFrame,
        index_above_ma: bool,
        next_monday_str: str,
    ) -> tuple:
        """
        Subclass must implement. If index_above_ma is True and len(open positions) < max_positions,
        identify qualifying new entries from the watchlist.
        For each new entry append a row:
          Trade: → 'Buy'
          Date:  → next_monday_str
          Price:, Ex. Price:, % chg:, Profit:, % Profit: → '-'
          Shares: → floor(equity_per_slot / current_close)
        Returns (updated_trades_df, buy_alerts_df).
        buy_alerts_df must contain at minimum a 'Code:' column and an 'Action:' column.
        """
        raise NotImplementedError

    # ── Monthly Workflow ──────────────────────────────────────────────────────

    def monthly_workflow(self):
        """
        End-of-month analytics workflow:
          1. Load trades and equity curve; calculate current portfolio value.
          2. Compute full analytics: cumulative return, annual return, trade stats,
             max drawdown, dividend yield, and 3/6/12-month rolling returns.
          3. Append last month's performance row to the Monthly Performance tab.
          4. Overwrite the Analytics tab with the updated metrics.
        """
        self.log("Starting monthly workflow...")

        trades_df  = self.load_trades()
        equity_df  = self.load_equity_curve()

        cash            = float(equity_df.iloc[-1]['Cash'])
        portfolio_value = get_equity_value(trades_df, cash, self._asof_as_date())
        self.log(f"Portfolio value: {portfolio_value:.2f}")

        analytics_df = self._calc_analytics(equity_df, trades_df)

        monthly_df         = self.load_monthly_performance()
        updated_monthly_df = self.update_monthly_performance_tab(monthly_df, equity_df, analytics_df)
        self.save_monthly_performance(updated_monthly_df)
        self.log("Monthly performance tab updated.")

        self.update_analytics(analytics_df)
        self.log("Analytics tab updated.")

        self.log("Monthly workflow complete.")

    def _calc_period_return(self, equity_df: pd.DataFrame, months: int):
        """
        Calculate the simple percentage return over the last N calendar months
        from the equity curve. Returns None if there is insufficient history.
        """
        df = equity_df.copy()
        df['Date:'] = pd.to_datetime(df['Date:'], errors='coerce')
        cutoff      = df['Date:'].iloc[-1] - pd.DateOffset(months=months)
        window      = df.loc[df['Date:'] >= cutoff, 'Portfolio Equity:']
        if window.empty:
            return None
        start_val = float(window.iloc[0])
        end_val   = float(df['Portfolio Equity:'].iloc[-1])
        if start_val == 0:
            return None
        return (end_val / start_val) - 1

    def _calc_portfolio_div_yield(self, trades_df: pd.DataFrame) -> float:
        """
        Calculate the average dividend yield across all Open positions by joining
        against the Company Page Data sheet. Returns 0.0 if data is unavailable.
        """
        open_codes = trades_df.loc[trades_df['Trade:'] == 'Open', 'Code:'].tolist()
        if not open_codes:
            return 0.0
        try:
            positions_df = self.load_positions()
            open_pos     = positions_df[positions_df['Code:'].isin(open_codes)]
            yields       = pd.to_numeric(
                open_pos['Dividend Yield:'].astype(str).str.rstrip('%'),
                errors='coerce',
            ).dropna()
            return float(yields.mean() / 100) if not yields.empty else 0.0
        except Exception:
            return 0.0

    def _calc_analytics(self, equity_df: pd.DataFrame, trades_df: pd.DataFrame) -> pd.DataFrame:
        """
        Build the complete analytics DataFrame. Closed trades are isolated by
        requiring a numeric Profit: value. Metrics computed:
          - Annual Return %, All trades, Winners, Avg. Profit %, Losers, Avg. Loss %,
            Max. system % drawdown (from performance_analytics)
          - Cumulative Return %
          - 3M / 6M / 12M Return %
          - Portfolio Dividend Yield %
        """
        numeric_profit = pd.to_numeric(trades_df['Profit:'], errors='coerce')
        closed_trades  = trades_df[numeric_profit.notna()].copy()
        closed_trades['Profit:'] = pd.to_numeric(closed_trades['Profit:'])

        analytics_df = performance_analytics(equity_df, closed_trades)

        cum_ret = (
            float(equity_df['Portfolio Equity:'].iloc[-1])
            / float(equity_df['Portfolio Equity:'].iloc[0])
        ) - 1
        analytics_df.loc['Cumulative Return %'] = round(cum_ret * 100, 2)

        for months in (3, 6, 12):
            ret   = self._calc_period_return(equity_df, months)
            label = f'{months}M Return %'
            analytics_df.loc[label] = round(ret * 100, 2) if ret is not None else '-'

        div_yield = self._calc_portfolio_div_yield(trades_df)
        analytics_df.loc['Portfolio Dividend Yield %'] = round(div_yield * 100, 2)

        return analytics_df

    def update_monthly_performance_tab(
        self,
        monthly_df: pd.DataFrame,
        equity_df: pd.DataFrame,
        analytics_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Append the current period's performance row to the Monthly Performance tab.
        Columns written: Date, 3M Return %, 6M Return %, 12M Return %, Cumulative Return %.
        Subclasses may override this method for a custom tab layout.
        """
        three_m  = self._calc_period_return(equity_df, 3)
        six_m    = self._calc_period_return(equity_df, 6)
        twelve_m = self._calc_period_return(equity_df, 12)

        cum_val  = analytics_df.loc['Cumulative Return %', 'Value'] \
            if 'Cumulative Return %' in analytics_df.index else '-'

        new_row = {
            'Date':                 self._asof_as_date().strftime('%d/%m/%Y'),
            'Cumulative Return %':  cum_val,
            '3M Return %':          round(three_m  * 100, 2) if three_m  is not None else '-',
            '6M Return %':          round(six_m    * 100, 2) if six_m    is not None else '-',
            '12M Return %':         round(twelve_m * 100, 2) if twelve_m is not None else '-',
        }

        return pd.concat([monthly_df, pd.DataFrame([new_row])], ignore_index=True)

    def update_analytics(self, analytics_df: pd.DataFrame) -> None:
        """
        Persist the analytics DataFrame to the Analytics sheet.
        Subclasses may override to apply custom formatting before saving.
        """
        self.save_analytics(analytics_df)
