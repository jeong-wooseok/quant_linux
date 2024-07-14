import pandas as pd
import numpy as np

def calculate_factors(processed_data):
    factor_data = processed_data.copy()
    
    # 퀄리티 팩터
    factor_data['ROE'] = factor_data['당기순이익'] / factor_data['자본']
    factor_data['GP/A'] = factor_data['매출총이익'] / factor_data['자산']
    
    # 밸류 팩터
    factor_data['PBR'] = factor_data['시가총액'] / factor_data['자본']
    factor_data['PER'] = factor_data['시가총액'] / factor_data['당기순이익']
    
    # 모멘텀 팩터
    factor_data['12M_momentum'] = factor_data['수익률_12개월']
    
    # 팩터 표준화
    factors = ['ROE', 'GP/A', 'PBR', 'PER', '12M_momentum']
    for factor in factors:
        factor_data[f'{factor}_z'] = (factor_data[factor] - factor_data[factor].mean()) / factor_data[factor].std()
    
    # 종합 점수 계산
    factor_data['total_score'] = (
        factor_data['ROE_z'] + 
        factor_data['GP/A_z'] - 
        factor_data['PBR_z'] - 
        factor_data['PER_z'] + 
        factor_data['12M_momentum_z']
    )
    
    return factor_data