import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import gspread
from gspread_dataframe import get_as_dataframe, set_with_dataframe

# ✅ 구글 시트 설정
SHEET_NAME = "stock_tickers"

# 구글 시트 불러오기
gc = gspread.service_account_from_dict(st.secrets["gspread"])
sh = gc.open(SHEET_NAME)
worksheet = sh.sheet1

# 현재 시트에서 티커 불러오기
def load_tickers():
    df = get_as_dataframe(worksheet, header=None)
    tickers = df[0].dropna().tolist()
    return tickers

# 시트에 티커 저장
def save_tickers(tickers):
    df = pd.DataFrame(tickers)
    worksheet.clear()
    set_with_dataframe(worksheet, df, include_index=False, include_column_header=False)

# ✅ 세션 상태 초기화
if "tickers" not in st.session_state:
    st.session_state.tickers = load_tickers()
if "selected" not in st.session_state:
    st.session_state.selected = st.session_state.tickers[0] if st.session_state.tickers else None

# ✅ 사이드바 UI
st.sidebar.title("📌 종목 관리")

# 티커 추가
new_ticker = st.sidebar.text_input("추가할 티커 입력 (예: AAPL)")
if st.sidebar.button("추가"):
    ticker = new_ticker.upper()
    if ticker and ticker not in st.session_state.tickers:
        st.session_state.tickers.append(ticker)
        save_tickers(st.session_state.tickers)

# 티커 목록 출력 및 선택
st.sidebar.markdown("### 🔍 종목 목록")
for i, ticker in enumerate(st.session_state.tickers):
    cols = st.sidebar.columns([4, 1, 1, 1])
    if cols[0].button(ticker, key=f"sel_{ticker}"):
        st.session_state.selected = ticker
    if cols[1].button("🔼", key=f"up_{i}") and i > 0:
        st.session_state.tickers[i], st.session_state.tickers[i-1] = st.session_state.tickers[i-1], st.session_state.tickers[i]
        save_tickers(st.session_state.tickers)
    if cols[2].button("🔽", key=f"down_{i}") and i < len(st.session_state.tickers)-1:
        st.session_state.tickers[i], st.session_state.tickers[i+1] = st.session_state.tickers[i+1], st.session_state.tickers[i]
        save_tickers(st.session_state.tickers)
    if cols[3].button("❌", key=f"del_{ticker}"):
        st.session_state.tickers.remove(ticker)
        save_tickers(st.session_state.tickers)
        if st.session_state.selected == ticker:
            st.session_state.selected = st.session_state.tickers[0] if st.session_state.tickers else None

# ✅ 선택된 종목 분석
selected = st.session_state.selected
if selected:
    try:
        stock = yf.Ticker(selected)
        info = stock.info
        hist = stock.history(period="1y")

        current_price = info.get("regularMarketPrice")
        high_52w = hist["High"].max() if not hist.empty else None
        low_52w = hist["Low"].min() if not hist.empty else None
        ath = stock.history(period="10y")["High"].max()

        def percent_change(current, reference):
            if not current or not reference or reference == 0:
                return "N/A"
            return f"{round(((current - reference) / reference) * 100, 2)}%"

        def format_price(value):
            return f"${value:.2f}" if value is not None else "N/A"

        st.title(f"📈 {selected} 분석 결과")
        st.write(f"- 현재가: **{format_price(current_price)}**")
        st.write(f"- 연중 최고가: **{format_price(high_52w)}**")
        st.write(f"- 연중 최저가: **{format_price(low_52w)}**")
        st.write(f"- 사상 최고가 (10Y): **{format_price(ath)}**")
        st.write(f"📉 사상 최고가 대비 하락률: {percent_change(current_price, ath)}")
        st.write(f"📉 연중 최고가 대비 하락률: {percent_change(current_price, high_52w)}")
        st.write(f"📈 연중 최저가 대비 상승률: {percent_change(current_price, low_52w)}")

        # 하락 구간 분석
        st.markdown("#### 📉 최고점 대비 하락 구간")
        levels = {f"{int(p*100)}% 하락": round(ath * (1 - p), 2) for p in [0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8]}
        df_levels = pd.DataFrame.from_dict(levels, orient='index', columns=['가격'])
        df_levels['가격'] = df_levels['가격'].map(lambda x: f"${x:.2f}")
        st.dataframe(df_levels)

        # 현재가 위치 시각화
        st.markdown("#### 🎯 현재 주가의 위치")
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
        ax.set_title(f"{selected} 현재가 위치", fontsize=10)
        st.pyplot(fig)

        # 주가 추세
        st.markdown("#### 📈 최근 1년간 종가 추세")
        fig2, ax2 = plt.subplots(figsize=(10, 3))
        ax2.plot(hist.index, hist['Close'], color='blue', label='종가', linewidth=1.5)
        ax2.set_ylabel("가격 ($)")
        ax2.set_xlabel("날짜")
        ax2.set_title(f"{selected} - 최근 1년 추세", fontsize=10)
        ax2.legend()
        ax2.grid(True)
        st.pyplot(fig2)

    except Exception as e:
        st.error(f"{selected} 분석 실패: {e}")
