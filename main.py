import pandas as pd
import requests
import json
import time
from datetime import datetime, timedelta
import numpy as np
from config import APP_KEY, APP_SECRET, ACCOUNT_NUMBER, URL_BASE
import data_collection

class TokenManager:
    def __init__(self):
        self.access_token = None
        self.expires_at = 0

    def get_access_token(self):
        if self.access_token is None or time.time() > self.expires_at:
            self.refresh_token()
        return self.access_token

    def refresh_token(self):
        url = f"{URL_BASE}/oauth2/tokenP"
        data = {
            "grant_type": "client_credentials",
            "appkey": APP_KEY,
            "appsecret": APP_SECRET
        }
        response = requests.post(url, json=data)
        token_data = response.json()
        self.access_token = token_data["access_token"]
        self.expires_at = time.time() + token_data["expires_in"] - 60  # 60초 여유

token_manager = TokenManager()

def hashkey(datas):
    """해시키 발급"""
    url = f"{URL_BASE}/uapi/hashkey"
    headers = {
        "content-Type": "application/json",
        "appKey": APP_KEY,
        "appSecret": APP_SECRET,
    }
    res = requests.post(url, headers=headers, data=json.dumps(datas))
    return res.json()["HASH"]

def get_ticker_data():
    """티커 데이터 수집"""
    url = f"{URL_BASE}/uapi/domestic-stock/v1/quotations/inquire-price"
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {token_manager.get_access_token()}",
        "appKey": APP_KEY,
        "appSecret": APP_SECRET,
        "tr_id": "FHKST01010100"
    }
    
    tickers = []
    market_codes = {"KOSPI": "J", "KOSDAQ": "Q"}
    
    for market_name, market_code in market_codes.items():
        params = {
            "FID_COND_MRKT_DIV_CODE": market_code,
            "FID_INPUT_ISCD": "0"
        }
        res = requests.get(url, headers=headers, params=params)
        
        if res.status_code != 200:
            print(f"API 호출 실패 ({market_name}): 상태 코드 {res.status_code}")
            print(f"응답 내용: {res.text}")
            continue
        
        res_data = res.json()
        if "output" not in res_data:
            print(f"예상치 못한 API 응답 형식 ({market_name}): {res_data}")
            continue
        
        tickers.extend(res_data["output"])
        print(f"{market_name} 티커 데이터 수집 성공: {len(res_data['output'])} 종목")
        time.sleep(1)  # API 호출 제한 준수

    df = pd.DataFrame(tickers)
    print("Ticker data columns:", df.columns)
    return df

def get_price_data(ticker, start_date, end_date):
    """가격 데이터 수집"""
    url = f"{URL_BASE}/uapi/domestic-stock/v1/quotations/inquire-daily-price"
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {token_manager.get_access_token()}",
        "appKey": APP_KEY,
        "appSecret": APP_SECRET,
        "tr_id": "FHKST01010400"
    }
    
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": ticker,
        "FID_INPUT_DATE_1": start_date,
        "FID_INPUT_DATE_2": end_date,
        "FID_PERIOD_DIV_CODE": "D"
    }
    res = requests.get(url, headers=headers, params=params)
    
    if res.status_code != 200:
        print(f"API 호출 실패 (티커: {ticker}): 상태 코드 {res.status_code}")
        print(f"응답 내용: {res.text}")
        return pd.DataFrame()
    
    res_data = res.json()
    if "output" not in res_data:
        print(f"예상치 못한 API 응답 형식 (티커: {ticker}): {res_data}")
        return pd.DataFrame()
    
    price_data = res_data["output"]
    return pd.DataFrame(price_data)

def get_moving_average(ticker, period):
    """주어진 기간의 이동평균 계산"""
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=period*2)).strftime('%Y%m%d')
    
    df = get_price_data(ticker, start_date, end_date)
    df['stck_clpr'] = df['stck_clpr'].astype(float)
    df['ma'] = df['stck_clpr'].rolling(window=period).mean()
    
    return df['ma'].iloc[-1]

def get_financial_data(tickers):
    """재무 데이터 수집"""
    url = f"{URL_BASE}/uapi/domestic-stock/v1/quotations/inquire-financial-comp"
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {token_manager.get_access_token()}",
        "appKey": APP_KEY,
        "appSecret": APP_SECRET,
        "tr_id": "FHKST03010100"
    }
    
    all_financial_data = []
    for ticker in tickers:
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": ticker
        }
        res = requests.get(url, headers=headers, params=params)
        financial_data = res.json()["output"]
        all_financial_data.extend(financial_data)
        time.sleep(1)  # API 호출 제한 준수

    return pd.DataFrame(all_financial_data)

def get_value_data(tickers):
    """가치 지표 데이터 수집"""
    url = f"{URL_BASE}/uapi/domestic-stock/v1/quotations/inquire-price"
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {token_manager.get_access_token()}",
        "appKey": APP_KEY,
        "appSecret": APP_SECRET,
        "tr_id": "FHKST01010100"
    }
    
    all_value_data = []
    for ticker in tickers:
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": ticker
        }
        res = requests.get(url, headers=headers, params=params)
        value_data = res.json()["output"]
        all_value_data.extend(value_data)
        time.sleep(1)  # API 호출 제한 준수

    return pd.DataFrame(all_value_data)

def get_sector_data():
    """섹터 데이터 수집"""
    # 이 함수는 별도의 데이터 소스를 사용하여 구현해야 합니다.
    # 예를 들어, KRX에서 제공하는 데이터를 사용할 수 있습니다.
    pass

def get_account_info():
    """계좌 정보 조회"""
    url = f"{URL_BASE}/uapi/domestic-stock/v1/trading/inquire-balance"
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {token_manager.get_access_token()}",
        "appKey": APP_KEY,
        "appSecret": APP_SECRET,
        "tr_id": "TTTC8434R"
    }
    params = {
        "CANO": ACCOUNT_NUMBER,
        "ACNT_PRDT_CD": "01",
        "AFHR_FLPR_YN": "N",
        "OFL_YN": "",
        "INQR_DVSN": "02",
        "UNPR_DVSN": "01",
        "FUND_STTL_ICLD_YN": "N",
        "FNCG_AMT_AUTO_RDPT_YN": "N",
        "PRCS_DVSN": "00",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": ""
    }
    response = requests.get(url, headers=headers, params=params)
    return response.json()['output2'][0]

def get_current_price(ticker):
    """현재가 조회"""
    url = f"{URL_BASE}/uapi/domestic-stock/v1/quotations/inquire-price"
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {token_manager.get_access_token()}",
        "appKey": APP_KEY,
        "appSecret": APP_SECRET,
        "tr_id": "FHKST01010100"
    }
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": ticker
    }
    response = requests.get(url, headers=headers, params=params)
    return int(response.json()['output']['stck_prpr'])

def place_order(ticker, quantity, order_type):
    """주문 실행"""
    url = f"{URL_BASE}/uapi/domestic-stock/v1/trading/order-cash"
    data = {
        "CANO": ACCOUNT_NUMBER,
        "ACNT_PRDT_CD": "01",
        "PDNO": ticker,
        "ORD_DVSN": "01",
        "ORD_QTY": str(quantity),
        "ORD_UNPR": "0",
    }
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {token_manager.get_access_token()}",
        "appKey": APP_KEY,
        "appSecret": APP_SECRET,
        "tr_id": "TTTC0802U" if order_type == "매수" else "TTTC0801U",
        "custtype": "P",
        "hashkey": hashkey(data)
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    return response.json()

def get_holding_stocks():
    """보유 주식 정보 조회"""
    url = f"{URL_BASE}/uapi/domestic-stock/v1/trading/inquire-balance"
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {token_manager.get_access_token()}",
        "appKey": APP_KEY,
        "appSecret": APP_SECRET,
        "tr_id": "TTTC8434R"
    }
    params = {
        "CANO": ACCOUNT_NUMBER,
        "ACNT_PRDT_CD": "01",
        "AFHR_FLPR_YN": "N",
        "OFL_YN": "",
        "INQR_DVSN": "02",
        "UNPR_DVSN": "01",
        "FUND_STTL_ICLD_YN": "N",
        "FNCG_AMT_AUTO_RDPT_YN": "N",
        "PRCS_DVSN": "00",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": ""
    }
    response = requests.get(url, headers=headers, params=params)
    return pd.DataFrame(response.json()['output1'])

def main():
    # 데이터 수집
    ticker_data = data_collection.get_ticker_data()
    
    # ticker_data의 열 이름 출력
    print("Ticker data columns:", ticker_data.columns)
    
    if ticker_data.empty:
        print("Error: 티커 데이터가 비어 있습니다.")
        return
    
    # 종목코드가 포함된 열 찾기
    code_column = next((col for col in ticker_data.columns if '코드' in col or 'code' in col.lower()), None)
    
    if code_column is None:
        print("Error: 종목코드를 포함하는 열을 찾을 수 없습니다.")
        print("사용 가능한 열:", ticker_data.columns)
        return
    
    # 모든 티커에 대해 가격 데이터 수집
    start_date = "20230101"  # 시작 날짜 설정
    end_date = datetime.datetime.now().strftime("%Y%m%d")  # 오늘 날짜
    
    all_price_data = []
    for ticker in ticker_data[code_column][:10]:  # 처음 10개 종목만 테스트 (시간 단축을 위해)
        price_data = data_collection.get_price_data(ticker, start_date, end_date)
        all_price_data.append(price_data)
    
    price_data = pd.concat(all_price_data, ignore_index=True)
    
    financial_data = data_collection.get_financial_data(ticker_data[code_column][:10])
    value_data = data_collection.get_value_data(ticker_data[code_column][:10])
    sector_data = data_collection.get_sector_data()

   # 데이터 처리
    processed_data = data_processing.process_data(ticker_data, price_data, financial_data, value_data, sector_data)

    # 팩터 계산
    factor_data = factor_calculation.calculate_factors(processed_data)

    # 포트폴리오 구성 및 백테스트
    portfolio, backtest_results = portfolio_construction.construct_portfolio(factor_data, price_data)
    top_10 = backtesting.select_top_performers(backtest_results, n=10)

    # 실적이 좋지 않은 주식 매도
    check_and_sell_underperforming_stocks()

    # Top 10 주식 매수 (보수적 접근)
    execute_trades(top_10, price_data)

    # 결과 출력
    utils.print_results(portfolio)
    utils.print_backtest_results(backtest_results)

if __name__ == "__main__":
    main()
