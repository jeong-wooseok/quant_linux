@echo off

REM Conda 환경 생성 및 패키지 설치
call conda env create -f environment.yml

echo 설치가 완료되었습니다. 환경을 활성화하려면 'conda activate stock_trading' 명령을 실행하세요.