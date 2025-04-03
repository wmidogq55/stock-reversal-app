
import io

if not filtered_stocks_df.empty:
    excel_file = io.BytesIO()
    with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
        filtered_stocks_df.to_excel(writer, index=False, sheet_name='選股結果')

    excel_file.seek(0)
    st.download_button(
        label="📥 下載選股結果 Excel",
        data=excel_file,
        file_name='reversal_stock_selection.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def add_indicators(df):
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA20_slope'] = df['MA20'].diff()
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    low_min = df['Low'].rolling(window=9).min()
    high_max = df['High'].rolling(window=9).max()
    df['%K'] = (df['Close'] - low_min) / (high_max - low_min) * 100
    df['%D'] = df['%K'].rolling(window=3).mean()
    return df

def filter_low_base_reversal(df):
    latest = df.iloc[-1]
    previous = df.iloc[-2]
    try:
        cond_rsi = latest['RSI'] < 30
        cond_macd_cross = latest['MACD'] > latest['Signal'] and previous['MACD'] <= previous['Signal']
        cond_ma20 = latest['Close'] > latest['MA20'] and latest['MA20_slope'] > 0
        cond_kd = latest['%K'] > latest['%D'] and latest['%K'] < 50 and latest['%D'] < 50
        return cond_rsi and cond_macd_cross and cond_ma20 and cond_kd
    except:
        return False

def main():
    st.title("📈 低基期＋反轉上升選股模型")
    tickers = st.text_input("輸入股票代號（以逗號分隔）", "TSLA,AAPL,NVDA,MSFT").split(",")
    start_date = st.date_input("選擇起始日期", pd.to_datetime("2023-01-01"))
    end_date = st.date_input("選擇結束日期", pd.to_datetime("today"))

    qualified_stocks = []
    result_data = {}

    if st.button("開始篩選"):
        for ticker in tickers:
            ticker = ticker.strip()
            df = yf.download(ticker, start=start_date, end=end_date)
            if df.empty:
                continue
            df = add_indicators(df)
            if filter_low_base_reversal(df):
                qualified_stocks.append(ticker)
                result_data[ticker] = df

        if qualified_stocks:
            st.success(f"✅ 符合條件的股票：{', '.join(qualified_stocks)}")
            with pd.ExcelWriter("選股結果.xlsx") as writer:
                for ticker in qualified_stocks:
                    result_data[ticker].to_excel(writer, sheet_name=ticker)

            with open("選股結果.xlsx", "rb") as f:
                st.download_button("📥 下載選股結果 Excel", f, file_name="選股結果.xlsx")

            for ticker in qualified_stocks:
                df = result_data[ticker]
                st.subheader(f"📊 {ticker} 指標圖")
                st.line_chart(df[['Close', 'MA20']])
                st.line_chart(df[['RSI']])
                st.line_chart(df[['MACD', 'Signal']])
        else:
            st.warning("❌ 沒有符合條件的股票")

if __name__ == "__main__":
    main()
