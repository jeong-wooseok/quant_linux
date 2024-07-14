import pandas as pd
import requests
import json
import time
from datetime import datetime, timedelta
import numpy as np
from sqlalchemy import create_engine, text
from config import APP_KEY, APP_SECRET, ACCOUNT_NUMBER, URL_BASE, DB_CONFIG
import requests
from bs4 import BeautifulSoup
import pandas as pd

# DB 연결 설정
engine = create_engine(f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")

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
    with engine.connect() as conn:
        ticker_list = pd.read_sql(text("""
        SELECT * FROM kor_ticker
        WHERE 기준일 = (SELECT MAX(기준일) FROM kor_ticker) 
            AND 종목구분 = '보통주';
        """), con=conn)
    
    print(f"티커 데이터 수집 성공: {len(ticker_list)} 종목")
    print("Ticker data columns:", ticker_list.columns)
    return ticker_list

def get_price_data(ticker, start_date, end_date):
    """가격 데이터 수집"""
    with engine.connect() as conn:
        price_data = pd.read_sql(text(f"""
        SELECT 날짜, 시가, 고가, 저가, 종가, 거래량
        FROM kor_price
        WHERE 종목코드 = '{ticker}'
        AND 날짜 BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY 날짜;
        """), con=conn)
    
    price_data['날짜'] = pd.to_datetime(price_data['날짜'])
    return price_data

def get_financial_data(tickers):
    """재무 데이터 수집"""
    with engine.connect() as conn:
        financial_data = pd.read_sql(text(f"""
        SELECT *
        FROM kor_fs
        WHERE 종목코드 IN {tuple(tickers)}
        AND 공시구분 = 'q'
        AND 계정 IN ('당기순이익', '매출총이익', '영업활동으로인한현금흐름', '자산', '자본');
        """), con=conn)
    return financial_data

def get_value_data(tickers):
    """가치 지표 데이터 수집"""
    with engine.connect() as conn:
        value_data = pd.read_sql(text(f"""
        SELECT *
        FROM kor_value
        WHERE 종목코드 IN {tuple(tickers)}
        AND 기준일 = (SELECT MAX(기준일) FROM kor_value);
        """), con=conn)
    return value_data

def get_moving_average(ticker, period):
    """주어진 기간의 이동평균 계산"""
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=period*2)).strftime('%Y-%m-%d')
    
    df = get_price_data(ticker, start_date, end_date)
    df['ma'] = df['종가'].rolling(window=period).mean()
    
    return df['ma'].iloc[-1]

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

def get_sector_data():
    """섹터 데이터 수집"""
    url = "https://kind.krx.co.kr/corpgeneral/corpList.do"
    params = {
        "method": "searchCorpSummary",
        "currentPageSize": "100",
        "comAbbrv": "",
        "orderMode": "3",
        "orderStat": "D",
        "marketType": "stockMkt",
        "searchType": "13",
        "fiscalYearEnd": "all",
        "location": "all",
    }

    response = requests.get(url, params=params)
    soup = BeautifulSoup(response.text, "html.parser")

    table = soup.find("table", {"class": "CI-GRID-BODY"})
    rows = table.find_all("tr")

    data = []
    for row in rows:
        cols = row.find_all("td")
        cols = [col.text.strip() for col in cols]
        if cols:
            sector = cols[4]
            data.append({"sector": sector})

    df = pd.DataFrame(data)
    df = df.drop_duplicates(subset="sector")
    df = df.reset_index(drop=True)

    return df


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

if __name__ == "__main__":
    # 테스트 코드
    print("Fetching ticker data...")
    ticker_data = get_ticker_data()
    print(ticker_data.head())

    print("\nFetching price data for first ticker...")
    first_ticker = ticker_data.iloc[0]['종목코드']  # 첫 번째 티커 선택
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    price_data = get_price_data(first_ticker, start_date, end_date)
    print(price_data.head())

    print("\nCalculating moving average...")
    ma_20 = get_moving_average(first_ticker, 20)
    print(f"20-day moving average for {first_ticker}: {ma_20}")

    print("\nFetching financial data...")
    financial_data = get_financial_data(ticker_data['종목코드'][:10])
    print(financial_data.head())

    print("\nFetching value data...")
    value_data = get_value_data(ticker_data['종목코드'][:10])
    print(value_data.head())

    print("\nFetching account info...")
    account_info = get_account_info()
    print(account_info)

    print("\nFetching current price...")
    current_price = get_current_price(first_ticker)
    print(f"Current price of {first_ticker}: {current_price}")

    print("\nFetching holding stocks...")
    holdings = get_holding_stocks()
    print(holdings)