
import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# 標題
st.set_page_config(layout="wide")
st.title("📈 低基期 + 反轉上升選股模型")

# 日期選擇
start_date = st.date_input("選擇起始日期", pd.to_datetime("2023-01-01"))
end_date = st.date_input("選擇結束日期", pd.to_datetime("2025-04-03"))

# 自動掃描美股 S&P 500 標的
sp500_symbols = ["AAPL", "TSLA", "MSFT", "GOOGL", "META", "NVDA"]

@st.cache_data
def get_stock_data(symbol, start, end):
    data = yf.download(symbol, start=start, end=end)
    return data

def calculate_indicators(df):
    df["RSI"] = df["Close"].rolling(window=14).mean()
    df["MACD"] = df["Close"].ewm(span=12).mean() - df["Close"].ewm(span=26).mean()
    df["Signal"] = df["MACD"].ewm(span=9).mean()
    return df

st.subheader("符合條件的標的（示意）")

results = []
for symbol in sp500_symbols:
    df = get_stock_data(symbol, start_date, end_date)
    if df.empty:
        continue
    df = calculate_indicators(df)
    latest_rsi = df["RSI"].iloc[-1]
    if latest_rsi < 50:  # 假設條件
        results.append({"股票代號": symbol, "最新 RSI": round(latest_rsi, 2)})

# 顯示結果表格
if results:
    result_df = pd.DataFrame(results)
    st.dataframe(result_df)

    # 匯出 Excel
    st.download_button(
        label="📥 匯出 Excel",
        data=result_df.to_csv(index=False).encode("utf-8-sig"),
        file_name="選股結果.csv",
        mime="text/csv"
    )

    # 顯示技術圖
    selected_symbol = st.selectbox("點選股票顯示技術圖", result_df["股票代號"])
    chart_data = get_stock_data(selected_symbol, start_date, end_date)
    chart_data = calculate_indicators(chart_data)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(chart_data["Close"], label="Close")
    ax.plot(chart_data["RSI"], label="RSI", linestyle="--")
    ax.plot(chart_data["MACD"], label="MACD")
    ax.plot(chart_data["Signal"], label="Signal", linestyle=":")
    ax.set_title(f"{selected_symbol} 技術圖")
    ax.legend()
    st.pyplot(fig)
else:
    st.info("目前無符合條件的標的")
