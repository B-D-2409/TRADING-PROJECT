import pandas as pd

def annualised_retun(equitydf):

    # Convert 'Date' column to datetime
    equitydf['Date:'] = pd.to_datetime(equitydf['Date:'], format='%Y-%m-%d')

    # Calculate Total Return
    initial_value = equitydf['Portfolio Equity:'].iloc[0]
    final_value = equitydf['Portfolio Equity:'].iloc[-1]
    total_return = (final_value / initial_value) - 1

    # Calculate Time Period in Years
    start_date = equitydf['Date:'].iloc[0]
    end_date = equitydf['Date:'].iloc[-1]
    years = (end_date - start_date).days / 365.0

    # Calculate Annualized Return
    ann_ret = (1 + total_return) ** (1 / years) - 1

    return ann_ret

def performance_analytics(equitydf, tradelist):

    num_trades = len(tradelist)
    winners = len(tradelist[tradelist['Profit:'] > 0])
    losers = len(tradelist[tradelist['Profit:'] <= 0])
    # Convert the '% Profit:' column to numerical values
    tradelist['dummy'] = tradelist['% Profit:'].str.rstrip('%').astype(float)
    # caculate stats
    avgprofit = tradelist[tradelist['dummy'] > 0]['dummy'].mean()
    avgloss = tradelist[tradelist['dummy'] <= 0]['dummy'].mean()
    # drop dummy col
    tradelist.drop(columns=['dummy'], inplace=True)
    # more stats
    annret = annualised_retun(equitydf)
    maxdd = equitydf['Drawdown %:'].min()

    # Create a DataFrame
    stats = {
        "Annual Return %": [annret * 100],  # Convert to percentage
        "All trades": [num_trades],
        "Winners": [winners],
        "Avg. Profit %": [avgprofit],
        "Losers": [losers],
        "Avg. Loss %": [avgloss],
        "Max. system % drawdown": [maxdd],
    }

    # Convert to a DataFrame with the desired index
    stats_df = pd.DataFrame.from_dict(stats, orient="index", columns=["Value"])
    stats_df.index.name = "Metric"

    return stats_df
