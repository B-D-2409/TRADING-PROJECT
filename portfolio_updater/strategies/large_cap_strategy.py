import pandas as pd
from base_strategy import BaseStrategy  # This is the abstract base class

from utils.equity import update_equity_curve, get_equity_value
from utils.company_data import fundamental_data
from utils.signals import process_signals
from utils.trades import update_trade_list
from utils.analytics import performance_analytics
from utils.file_io import combine_data


class LargeCapStrategy(BaseStrategy):
    def __init__(self, config, asof_date):
        super().__init__(config, asof_date)
        self.name = config["name"]
        self.folder = f"{self.name}/live_sheets"
        self.live_file = f"{self.name}/live_file/{self.asof_date}-data.xlsx"

    def read_old_data(self):
        def load(name): return pd.read_csv(f"{self.folder}/{self.prev_date}-{name}.csv")
        self.old_data = {
            "cip": load("companies_in_portfolio"),
            "cp": load("company_page_data"),
            "bs": load("buy_sell_alerts"),
            "a": load("analytics"),
            "ec": load("equity_curve"),
            "t": load("trades"),
        }

    def calculate_equity(self):
        self.equity_value = get_equity_value(self.old_data["t"], 0, self.asof_date)

    def update_equity_curve(self):
        self.new_ec = update_equity_curve(self.old_data["ec"], self.equity_value, self.asof_date)

    def generate_signals(self):
        # Read config
        c = self.config
        self.activitydf, self.positions = process_signals(
            strat_name=self.name,
            index_sym=c["universe"],
            frequency=c["freq"],
            number_positions=c["number_positions"],
            buy_lookback=next(cond["lookback_period"] for cond in c["buy_criteria"]["conditions"] if cond["type"] == "price_breakout"),
            sma_period=next(cond["period"] for cond in c["buy_criteria"]["conditions"] if cond["type"] == "external_indicator"),
            sell_lookback=next(c["sell_criteria"]["if_true"]["lookback_period"], 30),
            sell_scale=-0.1,
            index_sma=c["sell_criteria"]["condition_on"]["period"],
            sell_short_lookback=c["sell_criteria"]["if_false"]["lookback_period"],
            equity=self.equity_value,
            prev_date=self.prev_date
        )

    def update_portfolio(self):
        self.new_tradelist = update_trade_list(self.old_data["t"], self.activitydf, self.new_ec, self.asof_date, self.config["number_positions"])

    def calculate_analytics(self):
        self.new_analytics = performance_analytics(self.new_ec, self.new_tradelist)

    def get_company_data(self):
        columns = [
            "Name:", "Code:", "Sector:", "Last Price:", "52-Week High:", "52-Week Low:", "Market Cap:", "Franking Level:", "Business Summary:",
            "P/E Ratio:", "Dividend Yield:", "P/S Ratio:", "P/FCF Ratio:",
            "Net Debt:", "Debt-to-Equity Ratio:", "Current Ratio:", "Free Cash Flow:", "Net Profit Margin:",
            "Revenue Growth (3-Year CAGR):", "EPS Growth (3-Year CAGR):", "ROE:"
        ]
        data = [fundamental_data(code) for code in self.positions["Code:"]]
        self.new_cip = self.new_cp = pd.DataFrame(data, columns=columns)

    def get_trade_alerts(self):
        return self.activitydf

    def save_all(self):
        # Save each sheet
        self.new_cip.to_csv(f"{self.folder}/{self.asof_date}-companies_in_portfolio.csv", index=False)
        self.new_cp.to_csv(f"{self.folder}/{self.asof_date}-company_page_data.csv", index=False)
        self.new_ec.to_csv(f"{self.folder}/{self.asof_date}-equity_curve.csv", index=False)
        self.new_tradelist.to_csv(f"{self.folder}/{self.asof_date}-trades.csv", index=False)
        self.activitydf.to_csv(f"{self.folder}/{self.asof_date}-buy_sell_alerts.csv", index=False)
        self.new_analytics.to_csv(f"{self.folder}/{self.asof_date}-analytics.csv", header=False)

        # Final Excel export
        combine_data(
            self.live_file,
            self.new_cip,
            self.new_cp,
            self.activitydf,
            self.new_analytics,
            self.new_ec,
            self.new_tradelist
        )
