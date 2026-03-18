from strategies.base_strategy import BaseStrategy
from config_loader import load_config

class MidCapStrategy(BaseStrategy):
    def __init__(self):
        config = load_config("config/mid_cap.json")
        super().__init__(config)

    def market_traded_today(self):
        # Implement actual logic using your data source
        pass

    def update_last_price_for_positions(self):
        pass

    def update_distance_from_alert_price(self):
        pass

    def fill_sale_prices(self):
        pass

    def subtract_commissions_from_sales(self):
        pass

    def update_cash_balance_from_sales(self):
        pass

    def fill_purchase_prices(self):
        pass

    def update_cash_balance_from_purchases(self):
        pass

    def fill_buy_prices_for_recent_buys(self):
        pass

    def update_equity_curve(self):
        pass

    def update_fundamentals(self):
        pass

    def update_prices_for_open_positions(self):
        pass

    def calc_recent_performance(self):
        pass

    def update_open_positions_data(self):
        pass

    def calc_portfolio_stats(self):
        pass

    def check_for_sell_orders(self):
        pass

    def check_for_buy_orders(self):
        pass

    def calc_monthly_performance(self):
        pass

    def update_monthly_performance_tab(self):
        pass

    def update_analytics(self):
        pass
