from tabulate import tabulate
import slack_sdk
import time
from config import SLACK_TOKEN

def print_results(portfolio):
    print("\n포트폴리오 구성:")
    print(tabulate(portfolio, headers="keys", tablefmt="psql"))

def print_backtest_results(backtest_results):
    print("\n백테스트 결과 (Top 10):")
    print(tabulate(backtest_results.head(10).round(4), headers="keys", tablefmt="psql", showindex=True))
    
    # Slack으로 결과 전송
    send_slack_message(backtest_results)

def send_slack_message(backtest_results):
    cl = slack_sdk.WebClient(token=SLACK_TOKEN)
    
    tms = time.strftime('%y-%m-%d')
    message = f"{tms}의 백테스트 결과 (Top 10):\n{tabulate(backtest_results.head(10).round(4), headers='keys', tablefmt='psql', showindex=True)}"
    
    try:
        cl.chat_postMessage(channel='#api_test', text=message)
        print("Slack 메시지 전송 성공")
    except Exception as e:
        print(f"Slack 메시지 전송 실패: {str(e)}")

# 필요한 경우 다른 Slack 관련 함수들을 여기에 추가할 수 있습니다.