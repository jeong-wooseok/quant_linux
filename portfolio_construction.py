import pandas as pd
import numpy as np
from backtesting import run_backtesting

def construct_portfolio(factor_data, price_data):
    # 종합 점수 기준으로 상위 30개 종목 선택
    top_30 = factor_data.nlargest(30, 'total_score')
    
    # 백테스트 실행
    backtest_results = run_backtesting(top_30, price_data)
    
    return top_30, backtest_results