#%%
import math
import pandas as pd
from strategies.base_strategy import BaseStrategy
from utils.data_factory import get_data

#%%
class LargeCapStrategy(BaseStrategy):
    """
    Large Cap Strategy — ASX XJO universe (top 200 stocks by market cap).

    Max positions : 15
    Sell (always) : current close ≤ 30-week rolling low             [Trend Stop]
    Sell (index below SMA only):
                    current close ≤ 30-week rolling low             [Trend Stop]
                 OR current close ≤ 0.9 × 2-week high              [Momentum Stop]
    Buy  (index above SMA, open slots exist):
                    candidates supplied by external momentum scanner;
                    sized at equal weight: portfolio_equity ÷ 15.

    Symbol conversion: Trades sheet codes end in '.ASX'; stripped to base + '.au'
    before calling get_data (e.g. 'BHP.ASX' → 'BHP.au').
    """

    MAX_POSITIONS       = 15
    SELL_LOW_WEEKS      = 30
    SELL_HIGH_WEEKS     = 2
    SELL_HIGH_THRESHOLD = 0.9

    def __init__(self, config: dict, asof_date: str):
        super().__init__(config)
        self.asof_date = asof_date

    #%%
    def check_for_sell_orders(
        self,
        trades_df: pd.DataFrame,
        _: pd.DataFrame,
        index_above_ma: bool,
        next_monday_str: str,
    ) -> tuple:
        """
        Evaluate stop conditions for every currently Open position.

        Trend Stop    : close ≤ 30-week rolling low (fires regardless of index state).
        Momentum Stop : close ≤ 0.9 × 2-week high  (fires only when index is below SMA).

        Triggered rows are updated in-place:
          Trade: → 'Sell'  |  Ex. Date: → next_monday_str
          Ex. Price: / % chg: / Profit: / % Profit: → '-'
        The actual exit price is filled by daily_workflow on next Monday's open.

        Returns (updated_trades_df, sell_alerts_df).
        """
        asof     = self._asof_as_date()
        min_bars = self.SELL_LOW_WEEKS + 1
        sell_rows = []

        for idx, row in trades_df[trades_df['Trade:'] == 'Open'].iterrows():
            code   = str(row['Code:'])
            ticker = code.split('.')[0] + '.au'

            try:
                price_df = get_data(ticker, ed=asof, freq='W')
                if price_df is None or len(price_df) < min_bars:
                    continue

                current_close = float(price_df['Close'].iloc[-1])
                n_week_low    = float(
                    price_df['Low'].iloc[-(self.SELL_LOW_WEEKS + 1):-1].min()
                )
                two_week_high = float(
                    price_df['High'].iloc[-self.SELL_HIGH_WEEKS:].max()
                )

                trend_stop_hit    = current_close <= n_week_low
                momentum_stop_hit = (not index_above_ma) and (
                    current_close <= self.SELL_HIGH_THRESHOLD * two_week_high
                )

                if not (trend_stop_hit or momentum_stop_hit):
                    continue

                stop_type = 'Trend Stop' if trend_stop_hit else 'Momentum Stop'

                trades_df.at[idx, 'Trade:']     = 'Sell'
                trades_df.at[idx, 'Ex. Date:']  = next_monday_str
                trades_df.at[idx, 'Ex. Price:'] = '-'
                trades_df.at[idx, '% chg:']     = '-'
                trades_df.at[idx, 'Profit:']    = '-'
                trades_df.at[idx, '% Profit:']  = '-'

                sell_rows.append({
                    'Code:':      code,
                    'Action:':    'SELL',
                    'Stop Type:': stop_type,
                    'Date:':      next_monday_str,
                })

            except Exception:
                continue

        sell_alerts_df = (
            pd.DataFrame(sell_rows)
            if sell_rows
            else pd.DataFrame(columns=['Code:', 'Action:', 'Stop Type:', 'Date:'])
        )
        return trades_df, sell_alerts_df

    #%%
    def check_for_buy_orders(
        self,
        trades_df: pd.DataFrame,
        equity_df: pd.DataFrame,
        index_above_ma: bool,
        next_monday_str: str,
    ) -> tuple:
        """
        Insert new Buy rows when the index filter is clear and the portfolio has capacity.

        Position size = floor(portfolio_equity / MAX_POSITIONS / current_weekly_close).
        Occupied slots = count of rows where Trade: is 'Open' or 'Buy'.

        new_buys_df is the integration point for the external momentum scanner.
        Replace the pd.DataFrame() placeholder with the ranked candidate list
        (must contain at minimum a 'Code:' column) to activate live buy signals.

        Returns (updated_trades_df, buy_alerts_df).
        """
        empty_alerts = pd.DataFrame(columns=['Code:', 'Action:', 'Date:'])

        if not index_above_ma:
            return trades_df, empty_alerts

        occupied        = int(trades_df['Trade:'].isin(['Open', 'Buy']).sum())
        available_slots = self.MAX_POSITIONS - occupied
        if available_slots <= 0:
            return trades_df, empty_alerts

        current_equity        = float(equity_df['Portfolio Equity:'].iloc[-1])
        position_size_dollars = current_equity / self.MAX_POSITIONS

        new_buys_df = pd.DataFrame()

        if new_buys_df.empty:
            return trades_df, empty_alerts

        asof       = self._asof_as_date()
        buy_rows   = []
        alert_rows = []

        for _, candidate in new_buys_df.head(available_slots).iterrows():
            code   = str(candidate['Code:'])
            ticker = code.split('.')[0] + '.au'

            try:
                price_df      = get_data(ticker, ed=asof, freq='W')
                current_close = float(price_df['Close'].iloc[-1])
                shares        = math.floor(position_size_dollars / current_close)
                if shares == 0:
                    continue

                buy_rows.append({
                    'Code:':      code,
                    'Trade:':     'Buy',
                    'Date:':      next_monday_str,
                    'Price:':     '-',
                    'Ex. Date:':  next_monday_str,
                    'Ex. Price:': '-',
                    '% chg:':     '-',
                    'Profit:':    '-',
                    '% Profit:':  '-',
                    'Shares:':    float(shares),
                })
                alert_rows.append({
                    'Code:':   code,
                    'Action:': 'BUY',
                    'Date:':   next_monday_str,
                })

            except Exception:
                continue

        if buy_rows:
            trades_df = pd.concat(
                [trades_df, pd.DataFrame(buy_rows)], ignore_index=True
            )

        buy_alerts_df = pd.DataFrame(alert_rows) if alert_rows else empty_alerts
        return trades_df, buy_alerts_df
