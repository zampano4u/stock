import streamlit as st
import requests
from datetime import datetime
import matplotlib.pyplot as plt

# CNN Fear & Greed Index 데이터를 가져오는 함수
def get_fear_greed_index():
    try:
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata/"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        latest = data['fear_and_greed_historical']['data'][-1]
        index_value = latest['y']
        timestamp = latest['x'] / 1000
        return index_value, datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S'), data
    except Exception as e:
        return None, None, None

# 상단부에 CNN Fear & Greed Index를 고정적으로 표기
fg_index, fg_date, fg_data = get_fear_greed_index()
if fg_index is not None:
    st.markdown(f"### CNN Fear & Greed Index: **{fg_index}** (Last Updated: {fg_date})")
    # 그래픽 (추세선) 표시
    dates = [datetime.fromtimestamp(point['x'] / 1000) for point in fg_data['fear_and_greed_historical']['data']]
    values = [point['y'] for point in fg_data['fear_and_greed_historical']['data']]
    
    fig_fg, ax_fg = plt.subplots(figsize=(10, 3))
    ax_fg.plot(dates, values, color='blue', label='Fear & Greed Index')
    ax_fg.set_xlabel("Date")
    ax_fg.set_ylabel("Index Value")
    ax_fg.set_title("CNN Fear & Greed Index Trend")
    ax_fg.legend()
    ax_fg.grid(True)
    st.pyplot(fig_fg)
else:
    st.error("CNN Fear & Greed Index 데이터를 가져올 수 없습니다.")
import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import gspread
from gspread_dataframe import get_as_dataframe, set_with_dataframe

# ✅ 비밀번호 설정
PASSWORD = "jelso0428"
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 로그인 필요")
    password = st.text_input("비밀번호를 입력하세요", type="password")
    if st.button("로그인"):
        if password == PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("비밀번호가 틀렸습니다.")
    st.stop()

# ✅ Google Sheets 연동
SHEET_NAME = "stock_tickers"
gc = gspread.service_account_from_dict(st.secrets["gspread"])
sh = gc.open(SHEET_NAME)
worksheet = sh.sheet1

def load_tickers():
    df = get_as_dataframe(worksheet, header=None)
    if df.empty:
        return []
    return df.iloc[:, 0].dropna().tolist()

def save_tickers(tickers):
    df = pd.DataFrame(tickers)
    worksheet.clear()
    set_with_dataframe(worksheet, df, include_index=False, include_column_header=False)

# ✅ 세션 상태 초기화
if "tickers" not in st.session_state:
    st.session_state.tickers = load_tickers()
if "selected" not in st.session_state:
    st.session_state.selected = st.session_state.tickers[0] if st.session_state.tickers else None
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False

# ✅ 사이드바 – 종목 관리 및 수정 모드 토글
st.sidebar.title("📌 종목 관리")
new_ticker = st.sidebar.text_input("추가할 티커 입력 (예: AAPL)")
if st.sidebar.button("추가"):
    ticker = new_ticker.upper()
    if ticker and ticker not in st.session_state.tickers:
        st.session_state.tickers.append(ticker)
        save_tickers(st.session_state.tickers)

# 수정 모드 토글 버튼
if st.sidebar.button("수정"):
    st.session_state.edit_mode = not st.session_state.edit_mode

st.sidebar.markdown("### 🔍 종목 목록")
for i, ticker in enumerate(st.session_state.tickers):
    # 티커 선택 버튼
    if st.sidebar.button(f"{ticker}", key=f"sel_{ticker}"):
        st.session_state.selected = ticker
    # 수정 모드일 때만 추가 버튼 노출
    if st.session_state.edit_mode:
        html = f"""
        <div style="display: flex; gap: 5px; margin: 0.2em 0;">
            <form method="get">
                <button name="action" value="up_{i}" style="padding:2px 6px;">⬆️</button>
            </form>
            <form method="get">
                <button name="action" value="down_{i}" style="padding:2px 6px;">⬇️</button>
            </form>
            <form method="get">
                <button name="action" value="del_{ticker}" style="padding:2px 6px;">❌</button>
            </form>
        </div>
        """
        st.sidebar.markdown(html, unsafe_allow_html=True)
# ✅ 액션 처리 (최신 Streamlit API)
params = st.query_params
action = params.get("action", [None])[0]
if action:
    if action.startswith("up_"):
        i = int(action.split("_")[1])
        if i > 0:
            st.session_state.tickers[i], st.session_state.tickers[i-1] = st.session_state.tickers[i-1], st.session_state.tickers[i]
            save_tickers(st.session_state.tickers)
            st.query_params.clear()
            st.rerun()
    elif action.startswith("down_"):
        i = int(action.split("_")[1])
        if i < len(st.session_state.tickers)-1:
            st.session_state.tickers[i], st.session_state.tickers[i+1] = st.session_state.tickers[i+1], st.session_state.tickers[i]
            save_tickers(st.session_state.tickers)
            st.query_params.clear()
            st.rerun()
    elif action.startswith("del_"):
        ticker = action.replace("del_", "")
        if ticker in st.session_state.tickers:
            st.session_state.tickers.remove(ticker)
            save_tickers(st.session_state.tickers)
            if st.session_state.selected == ticker:
                st.session_state.selected = st.session_state.tickers[0] if st.session_state.tickers else None
            st.query_params.clear()
            st.rerun()

# ✅ 분석 유틸 함수
def percent_change(current, reference):
    if not current or not reference or reference == 0:
        return "N/A"
    return f"{round(((current - reference) / reference) * 100, 2)}%"

def format_price(value):
    return f"${value:.2f}" if value is not None else "N/A"
# ✅ 선택된 종목 분석
selected = st.session_state.selected
if selected:
    try:
        stock = yf.Ticker(selected)
        info = stock.info
        hist = stock.history(period="1y")
        ath = stock.history(period="10y")["High"].max()
        low_6mo = stock.history(period="6mo")["Low"].min() if not hist.empty else None

        current_price = info.get("regularMarketPrice")
        high_52w = hist["High"].max() if not hist.empty else None
        low_52w = hist["Low"].min() if not hist.empty else None
        prev_close = info.get("previousClose")

        st.title(f"📈 {selected} 분석 결과")
        st.write(f"- 현재가: **{format_price(current_price)}**")
        st.write(f"- 전일 종가: **{format_price(prev_close)}**")
        st.write(f"📊 전일 대비 변화율: {percent_change(current_price, prev_close)}")
        st.write(f"- 연중 최고가: **{format_price(high_52w)}**")
        st.write(f"- 연중 최저가: **{format_price(low_52w)}**")
        st.write(f"- 6개월 최저가: **{format_price(low_6mo)}**")
        st.write(f"📈 6개월 최저가 대비 상승률: {percent_change(current_price, low_6mo)}")
        st.write(f"- 사상 최고가 (10년): **{format_price(ath)}**")
        st.write(f"📉 사상 최고가 대비 하락률: {percent_change(current_price, ath)}")
        st.write(f"📉 연중 최고가 대비 하락률: {percent_change(current_price, high_52w)}")
        st.write(f"📈 연중 최저가 대비 상승률: {percent_change(current_price, low_52w)}")

        st.markdown("#### 📉 최고점 대비 하락 구간 (5% 단위)")
        drop_levels = [i/100 for i in range(0, 85, 5)]
        levels = {f"{int(level*100)}% 하락": round(ath * (1 - level), 2) for level in drop_levels}
        df_levels = pd.DataFrame.from_dict(levels, orient='index', columns=['가격'])
        df_levels['가격'] = df_levels['가격'].map(lambda x: f"${x:.2f}")
        st.dataframe(df_levels)

        st.markdown("#### 🎯 현재 주가의 위치")
        fall_points = [ath * (1 - level) for level in drop_levels]
        labels = [f"{int(level*100)}%" for level in drop_levels]

        current_drop = 1 - (current_price / ath) if ath and current_price else 0
        highlight_index = 0
        for idx in range(len(drop_levels) - 1):
            if drop_levels[idx] <= current_drop < drop_levels[idx+1]:
                highlight_index = idx
                break
        if current_drop >= drop_levels[-1]:
            highlight_index = len(drop_levels) - 1

        colors = ["green" if idx == highlight_index else "lightgray" for idx in range(len(fall_points))]

        fig, ax = plt.subplots(figsize=(8, 1.5))
        bars = ax.bar(labels, fall_points, color=colors, edgecolor='black')
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f"${height:.2f}",
                        xy=(bar.get_x() + bar.get_width()/2, height),
                        xytext=(0, 3), textcoords="offset points",
                        ha='center', fontsize=8)
        ax.set_ylabel("가격 ($)")
        ax.set_title(f"{selected} 현재가 위치", fontsize=10)
        st.pyplot(fig)

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
