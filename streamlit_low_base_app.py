
import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime

st.set_page_config(page_title="低基期 + 反轉上升選股模型", layout="wide")

st.title("📈 低基期 + 反轉上升選股模型")
st.caption("支援 台股/美股選擇 + 自動判別 + 匯出 Excel")

st.subheader("選擇起始日期")
start_date = st.text_input("選擇起始日期", "2023/01/01")

st.subheader("選擇結束日期")
end_date = st.text_input("選擇結束日期", datetime.now().strftime("%Y/%m/%d"))

st.subheader("輸入股票代號（以逗號分隔）")
symbol_input = st.text_input("例如：TSLA,AAPL,2330,2317", "TSLA,AAPL")

def fetch_stock_data(symbol, start, end):
    try:
        data = yf.download(symbol, start=start, end=end)
        return data
    except Exception as e:
        return None

def is_low_base_reversal(df):
    try:
        if df is None or df.empty:
            return False
        df['MA20'] = df['Close'].rolling(window=20).mean()
        recent_close = df['Close'].iloc[-1]
        recent_ma20 = df['MA20'].iloc[-1]
        prev_close = df['Close'].iloc[-2]
        if prev_close < recent_ma20 and recent_close > recent_ma20:
            return True
    except:
        return False
    return False

if st.button("開始篩選"):
    if not symbol_input:
        st.warning("請輸入股票代號")
    else:
        st.subheader("符合條件的標的（示意）")
        symbols = [s.strip() for s in symbol_input.split(",")]
        matched = []
        for symbol in symbols:
            df = fetch_stock_data(symbol, start_date, end_date)
            if is_low_base_reversal(df):
                matched.append(symbol)
        if matched:
            st.success("符合條件的標的如下：")
            st.write(matched)
            result_df = pd.DataFrame({"符合條件標的": matched})
            st.download_button("📥 下載結果 Excel", result_df.to_csv(index=False).encode("utf-8"), file_name="selected_stocks.csv")
        else:
            st.info("目前無符合條件的標的")
