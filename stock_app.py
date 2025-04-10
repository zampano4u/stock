import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# 비밀번호 설정
PASSWORD = "jelso0428"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# 로그인 UI
if not st.session_state.authenticated:
    st.title("🔐 로그인 필요")
    password_input = st.text_input("비밀번호를 입력하세요", type="password")
    if st.button("로그인"):
        if password_input == PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("비밀번호가 틀렸습니다.")
    st.stop()

# 종목 목록 관리
if 'tickers' not in st.session_state:
    st.session_state.tickers = ['AAPL', 'MSFT']

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

# 유틸 함수
def percent_change(current, reference):
    if not current or not reference or reference == 0:
        return "N/A"
    return f"{round(((current - reference) / reference) * 100, 2)}%"

def get_all_time_high(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="10y")
        return hist["High"].max() if not hist.empty else None
    except:
        return None

def format_price(value):
    return f"${value:.2f}" if value is not None else "N/A"

# 종목별 데이터 조회 및 출력
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
        st.write(f"- 현재가: **{format_price(current_price)}**")
        st.write(f"- 연중 최고가: **{format_price(high_52w)}**")
        st.write(f"- 연중 최저가: **{format_price(low_52w)}**")
        st.write(f"- (10년 기준) 사상 최고가: **{format_price(ath)}**")

        st.write(f"📉 사상 최고가 대비 하락률: {percent_change(current_price, ath)}")
        st.write(f"📉 연중 최고가 대비 하락률: {percent_change(current_price, high_52w)}")
        st.write(f"📈 연중 최저가 대비 상승률: {percent_change(current_price, low_52w)}")

        # 하락 구간 계산 및 표
        if ath:
            st.markdown("#### 📉 최고점 대비 하락 구간")
            levels = {f"{int(p*100)}% 하락": round(ath * (1 - p), 2) for p in [0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8]}
            df_levels = pd.DataFrame.from_dict(levels, orient='index', columns=['가격'])
            df_levels['가격'] = df_levels['가격'].map(lambda x: f"${x:.2f}")
            st.dataframe(df_levels)

            # 막대 그래프 시각화
            st.markdown("##### 🎯 현재 주가의 위치 (사상 최고가 기준)")
            fall_points = [ath * (1 - p) for p in [0.0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8]]
            labels = [f"{int(p*100)}%↓" for p in [0.0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8]]
            colors = ["green" if current_price >= price else "lightgray" for price in fall_points]

            fig, ax = plt.subplots(figsize=(8, 1.5))
            bars = ax.bar(labels, fall_points, color=colors, edgecolor='black')
            for bar in bars:
                height = bar.get_height()
                ax.annotate(f"${height:.2f}", xy=(bar.get_x() + bar.get_width()/2, height),
                            xytext=(0, 3), textcoords="offset points", ha='center', fontsize=8)
            ax.set_ylabel("가격 ($)")
            ax.set_title(f"{ticker} 현재가 위치", fontsize=10)
            st.pyplot(fig)

        # 최근 1년 종가 추세
        if not hist.empty:
            st.markdown("#### 📈 최근 1년간 종가 추세")
            fig2, ax2 = plt.subplots(figsize=(10, 3))
            ax2.plot(hist.index, hist['Close'], color='blue', label='종가', linewidth=1.5)
            ax2.set_ylabel("가격 ($)")
            ax2.set_xlabel("날짜")
            ax2.set_title(f"{ticker} - 최근 1년간 주가 추세", fontsize=10)
            ax2.legend()
            ax2.grid(True)
            st.pyplot(fig2)

        st.markdown("---")

    except Exception as e:
        st.error(f"{ticker} 조회 실패: {e}")
