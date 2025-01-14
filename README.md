# 주식 트레이딩 시스템

이 프로젝트는 한국 주식 시장에서 멀티팩터 전략을 사용하여 자동으로 트레이딩하는 시스템을 구현합니다.

## 기능

- 주식 데이터 수집 (가격, 재무 정보, 가치 지표 등)
- 멀티팩터 모델을 이용한 주식 선별
- 백테스팅
- 실시간 트레이딩 (당일 매매)
- 결과 리포팅 (Slack 통합)

## 설치 방법

1. 이 저장소를 클론합니다:
git clone https://github.com/yourusername/stock-trading-system.git
Copy
2. 필요한 패키지를 설치합니다:
pip install -r requirements.txt
Copy
3. `config.py` 파일을 생성하고 필요한 설정을 입력합니다:
```python
APP_KEY = "YOUR_APP_KEY"
APP_SECRET = "YOUR_APP_SECRET"
ACCOUNT_NUMBER = "YOUR_ACCOUNT_NUMBER"
URL_BASE = "https://openapi.koreainvestment.com:9443"
INVEST_RATIO = 0.98

## 사용 방법

### 메인 스크립트를 실행합니다:

```linux
python main.py
```

### 시스템은 자동으로 다음 단계를 수행합니다:

- 주식 데이터 수집
- 팩터 계산 및 주식 선별
- 백테스팅
- Top 10 종목 선정
- 실시간 트레이딩 실행


> 트레이딩 결과는 콘솔에 출력되며, 설정된 Slack 채널로도 전송됩니다.

## 파일 구조

- main.py: 메인 실행 스크립트
    - data_collection.py: 데이터 수집 관련 함수
    - data_processing.py: 데이터 처리 관련 함수
    - factor_calculation.py: 팩터 계산 관련 함수
    - portfolio_construction.py: 포트폴리오 구성 관련 함수
    - backtesting.py: 백테스팅 관련 함수
    - utils.py: 유틸리티 함수
- config.py: 설정 파일

## 주의사항
```
이 시스템은 실제 돈을 거래합니다. 반드시 충분한 테스트를 거친 후에 실제 계좌에서 사용하세요.
API 키와 계좌 정보는 절대 공개하지 마세요.
한국투자증권 API의 사용 제한을 준수하세요.
```

## 라이선스
이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 LICENSE 파일을 참조하세요.

## 기여
버그 리포트, 기능 제안, 풀 리퀘스트는 언제나 환영합니다. 큰 변경사항의 경우, 먼저 이슈를 열어 논의해 주세요.
