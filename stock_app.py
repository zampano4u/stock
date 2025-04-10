import streamlit as st
import yfinance as yf
import pandas as pd

# 종목 목록 초기화
if 'tickers' not in st.session_state:
    st.session_state.tickers = ['AAPL', 'MSFT']

# 사이드바에서 종목 관리
st.sidebar.title("종목 관리")
new_ticker = st.sidebar.text_input("추가할 티커 입력 (예: AAPL)")
if st.sidebar.button("추가") and new_ticker:
    ticker = new_ticker.upper()
    if ticker not in st.session_state.tickers:
        st.session_state.tickers.append(ticker)

remove_ticker = st.sidebar.selectbox("제거할 티커 선택", [""] + st.session_state.tickers)
if st.sidebar.button("제거") and remove_ticker:
    st.session_state.tickers.remove(remove_ticker)

st.title("📈 미국 주식 현재가 및 최고가 분석")

# 퍼센트 계산 함수
def percent_change(current, reference):
    if not current or not reference or reference == 0:
        return "N/A"
    return f"{round(((current - reference) / reference) * 100, 2)}%"

# yfinance에서 사상 최고가 추정 (10년간 최고가)
def get_all_time_high(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="10y")
        return hist["High"].max() if not hist.empty else None
    except:
        return None

# 각 종목에 대해 정보 출력
for ticker in st.session_state.tickers:
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="1y")

        current_price = info.get("regularMarketPrice")
        high_52w = hist["High"].max() if not hist.empty else None
        low_52w = hist["Low"].min() if not hist.empty else None
        ath = get_all_time_high(ticker)

        st.markdown(f"### 📌 {ticker}")
        st.write(f"- 현재가: **${current_price}**")
        st.write(f"- 연중 최고가: **${high_52w}**")
        st.write(f"- 연중 최저가: **${low_52w}**")
        st.write(f"- (10년 기준) 사상 최고가: **${ath}**")

        st.write(f"📉 사상 최고가 대비 하락률: {percent_change(current_price, ath)}")
        st.write(f"📉 연중 최고가 대비 하락률: {percent_change(current_price, high_52w)}")
        st.write(f"📈 연중 최저가 대비 상승률: {percent_change(current_price, low_52w)}")

        st.markdown("---")
    except Exception as e:
        st.error(f"{ticker} 조회 실패: {e}")
