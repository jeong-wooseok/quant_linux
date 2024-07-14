import pandas as pd
import numpy as np

def process_data(ticker_data, price_data, financial_data, value_data, sector_data):
    # 데이터 처리 및 결합 로직
    processed_data = pd.merge(ticker_data, price_data, on='종목코드')
    processed_data = pd.merge(processed_data, financial_data, on='종목코드')
    processed_data = pd.merge(processed_data, value_data, on='종목코드')
    processed_data = pd.merge(processed_data, sector_data, on='종목코드')
    
    # 결측치 처리
    processed_data = processed_data.dropna()
    
    # 이상치 처리
    for column in processed_data.select_dtypes(include=[np.number]).columns:
        processed_data[column] = winsorize(processed_data[column])
    
    return processed_data

def winsorize(series, limits=(0.01, 0.99)):
    return series.clip(lower=series.quantile(limits[0]), upper=series.quantile(limits[1]))