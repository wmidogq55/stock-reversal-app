import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import requests
import io

st.set_page_config(page_title="低基期 + 反轉上升選股模型", layout="centered")
st.title("📈 低基期 + 反轉上升選股模型")
st.caption("支援 **台股/美股選擇 + 自動判別 + 匯出 Excel**")

# 使用者輸入
ticker_input = st.text_input("輸入股票代號（以逗號分隔）", "TSLA,AAPL,2330,2317")
start_date = st.date_input("選擇起始日期", datetime(2023, 1, 1))
end_date = st.date_input("選擇結束日期", datetime.today())

# 自動判別台股與美股
tickers = [x.strip().upper() for x in ticker_input.split(",") if x.strip()]
tw_tickers = [x for x in tickers if x.isdigit()]
us_tickers = [x for x in tickers if not x.isdigit()]

# Token for FinMind
finmind_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJkYXRlIjoiMjAyNS0wNC0wMyAxMDo0OTo1MiIsInVzZXJfaWQiOiJ3bWlkb2dxNTUiLCJpcCI6IjExMS4yNDYuODIuMjE1In0.WClrNkfmH8vKQkEIQb6rVmAnQToh4hQeYIAJLlO2siU"

def fetch_tw_stock_price(stock_id):
    url = "https://api.finmindtrade.com/api/v4/data"
    params = {
        "dataset": "TaiwanStockPrice",
        "data_id": stock_id,
        "start_date": str(start_date),
        "end_date": str(end_date),
        "token": finmind_token
    }
    resp = requests.get(url, params=params).json()
    if resp["status"] != 200 or not resp["data"]:
        return None
    df = pd.DataFrame(resp["data"])
    df["Date"] = pd.to_datetime(df["date"])
    df.set_index("Date", inplace=True)
    df.sort_index(inplace=True)
    df.rename(columns={"close": "Close"}, inplace=True)
    return df

def fetch_us_stock_price(symbol):
    df = yf.download(symbol, start=start_date, end=end_date)
    return df if not df.empty else None

def rsi(df, period=14):
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def kd(df, n=9, m1=3, m2=3):
    low_min = df['Low'].rolling(n).min()
    high_max = df['High'].rolling(n).max()
    rsv = (df['Close'] - low_min) / (high_max - low_min) * 100
    k = rsv.ewm(com=(m1 - 1), adjust=False).mean()
    d = k.ewm(com=(m2 - 1), adjust=False).mean()
    return k, d

def evaluate_stock(symbol, is_tw):
    df = fetch_tw_stock_price(symbol) if is_tw else fetch_us_stock_price(symbol)
    if df is None or "Close" not in df or len(df) < 30:
        return None
    df["RSI"] = rsi(df)
    df["MA20"] = df["Close"].rolling(20).mean()
    df["K"], df["D"] = kd(df)

    rsi_last = df["RSI"].iloc[-1]
    kd_cross = df["K"].iloc[-1] > df["D"].iloc[-1] and df["K"].iloc[-2] < df["D"].iloc[-2]
    ma_trend = df["Close"].iloc[-1] > df["MA20"].iloc[-1]
    condition = rsi_last < 40 and kd_cross and ma_trend

    return {
        "代號": symbol,
        "市場": "台股" if is_tw else "美股",
        "收盤": df["Close"].iloc[-1],
        "RSI": round(rsi_last, 2),
        "20日均線": round(df["MA20"].iloc[-1], 2),
        "K值": round(df["K"].iloc[-1], 2),
        "D值": round(df["D"].iloc[-1], 2),
        "符合條件": "✅" if condition else ""
    }

if st.button("開始篩選"):
    st.info("正在載入資料並篩選，請稍候...")
    results = []

    for symbol in tw_tickers:
        result = evaluate_stock(symbol, is_tw=True)
        if result: results.append(result)

    for symbol in us_tickers:
        result = evaluate_stock(symbol, is_tw=False)
        if result: results.append(result)

    if not results:
        st.warning("查無符合條件的股票")
    else:
        df_result = pd.DataFrame(results)
        st.dataframe(df_result, use_container_width=True)

        # 匯出下載
        csv = df_result.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="📥 匯出 Excel",
            data=csv,
            file_name="stock_selection_result.csv",
            mime="text/csv"
        )
