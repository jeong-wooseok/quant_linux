import pandas as pd
import numpy as np

def run_backtesting(portfolio, price_data, lookback_period=252):
    portfolio_prices = price_data[price_data['종목코드'].isin(portfolio['종목코드'])]
    
    returns = portfolio_prices.groupby('종목코드').apply(lambda x: x['수익률'].iloc[-lookback_period:])
    
    cumulative_returns = (1 + returns).prod() - 1
    daily_returns = returns.mean()
    volatility = returns.std() * np.sqrt(252)
    sharpe_ratio = (daily_returns * 252) / volatility
    
    results = pd.DataFrame({
        '누적수익률': cumulative_returns,
        '평균일일수익률': daily_returns,
        '변동성': volatility,
        '샤프비율': sharpe_ratio
    }).sort_values('샤프비율', ascending=False)
    
    return results

def select_top_performers(backtest_results, n=10):
    return backtest_results.head(n)