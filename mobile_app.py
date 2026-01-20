import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from datetime import datetime

# --- 1. 手機版面設定 ---
st.set_page_config(page_title="CB 計算機", page_icon="📱", layout="centered")

# --- 2. CSS 手機優化 ---
st.markdown("""
<style>
    .stApp { font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
    .stTextInput input { font-size: 18px; padding: 10px; }
    .stButton button { width: 100%; font-size: 18px; font-weight: bold; padding: 10px; }
    .card {
        background-color: #ffffff; padding: 15px; border-radius: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.08); margin-bottom: 12px; border: 1px solid #f0f0f0;
    }
    .card-header { font-size: 14px; color: #888; margin-bottom: 4px; }
    .card-value { font-size: 28px; font-weight: 800; color: #333; }
    .tag { font-size: 12px; padding: 3px 8px; border-radius: 4px; color: white; display: inline-block; margin-left: 5px; vertical-align: middle;}
    .tag-tw { background-color: #007bff; } /* 上市藍 */
    .tag-two { background-color: #28a745; } /* 上櫃綠 */
    
    .fallback-btn {
        display: block; text-decoration: none; background-color: #f8f9fa; 
        color: #333; padding: 12px; border-radius: 8px; margin: 8px 0; 
        font-weight: bold; border: 1px solid #ddd; text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. 強力股價搜尋 (專治上櫃抓不到) ---
def get_price_robust(stock_id):
    # 策略 A: 先假設它是上櫃 (.TWO) - 因為你反應上櫃抓不到，我們優先測
    try:
        t = yf.Ticker(f"{stock_id}.TWO")
        hist = t.history(period="1d")
        if not hist.empty:
            price = float(hist['Close'].iloc[-1])
            return price, "TWO" # 回傳標記：這是上櫃
    except: pass

    # 策略 B: 如果上櫃沒資料，再試上市 (.TW)
    try:
        t = yf.Ticker(f"{stock_id}.TW")
        hist = t.history(period="1d")
        if not hist.empty:
            price = float(hist['Close'].iloc[-1])
            return price, "TW" # 回傳標記：這是上市
    except: pass
    
    return None, None

# --- 4. 抓可轉債 (爬蟲 + 手動備案) ---
def get_cb_data(stock_id):
    # 嘗試 Goodinfo
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        url = f"https://goodinfo.tw/tw/StockIssuanceCB.asp?STOCK_ID={stock_id}"
        res = requests.get(url, headers=headers, timeout=4)
        if res.status_code == 200:
            dfs = pd.read_html(res.text)
            for df in dfs:
                if "轉換價格" in df.columns:
                    return df[['債券名稱', '轉換價格']].head(3), "Goodinfo"
    except: pass

    # 嘗試 HiStock (上櫃股這裡通常比較穩)
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        url = f"https://histock.tw/stock/{stock_id}/%E5%8F%AF%E8%BD%89%E5%82%B5"
        res = requests.get(url, headers=headers, timeout=4)
        if res.status_code == 200:
            dfs = pd.read_html(res.text)
            for df in dfs:
                if "名稱" in df.columns and "轉換價" in df.columns:
                     df = df.rename(columns={"名稱": "債券名稱", "轉換價": "轉換價格"})
                     return df[['債券名稱', '轉換價格']].head(3), "HiStock"
    except: pass

    return None, None

# --- 5. 輔助顯示 ---
def card(title, value, sub="", color_border=""):
    border_style = f"border-left: 5px solid {color_border};" if color_border else ""
    st.markdown(f"""
    <div class="card" style="{border_style}">
        <div class="card-header">{title}</div>
        <div class="card-value">{value}</div>
        <div style="font-size:13px; color:#666;">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

# --- 6. App 主介面 ---
st.title("📱 CB 價值精算機")
st.caption("v8.0 (OTC/上櫃 優化版)")

col1, col2 = st.columns([3, 1])
with col1:
    stock_input = st.text_input("股票代號", placeholder="如: 3293, 8069", label_visibility="collapsed")
with col2:
    run_btn = st.button("查詢")

if run_btn or stock_input:
    stock_id = stock_input.strip()
    
    with st.spinner(f'正在搜尋 {stock_id} (含上櫃資料庫)...'):
        
        # 1. 抓股價
        price, market_type = get_price_robust(stock_id)

        if price:
            # 顯示標籤
            tag_html = ""
            if market_type == "TWO":
                tag_html = "<span class='tag tag-two'>上櫃 OTC</span>"
                border_color = "#28a745" # 綠色
            else:
                tag_html = "<span class='tag tag-tw'>上市 TWSE</span>"
                border_color = "#007bff" # 藍色

            st.markdown(f"### 📊 {stock_id} {tag_html}", unsafe_allow_html=True)
            card("目前股價", f"{price} 元", f"資料來源: Yahoo Finance", border_color)
            
            # 2. 抓 CB
            cb_df, cb_source = get_cb_data(stock_id)
            
            if cb_df is not None and not cb_df.empty:
                st.success(f"✅ CB 資料來源：{cb_source}")
                for idx, row in cb_df.iterrows():
                    cb_name = row['債券名稱']
                    try:
                        raw = str(row['轉換價格']).replace(',', '').replace('*', '')
                        conv_price = float(raw)
                    except: conv_price = 0
                        
                    if conv_price > 0:
                        parity = (price / conv_price) * 100
                        st.markdown("---")
                        st.subheader(f"🔗 {cb_name}")
                        
                        c1, c2 = st.columns(2)
                        with c1: st.metric("轉換價", f"{conv_price}")
                        with c2: st.metric("平價", f"{parity:.2f}")

                        fair_val = parity * 1.05
                        st.info(f"💰 合理買點參考：{fair_val:.1f} 以下")
                        
                        target_120 = conv_price * 1.2
                        st.write(f"📈 目標 120 元 ➔ 現股需漲至 **{target_120:.1f}**")
            else:
                # 抓不到 CB 時的備案
                st.warning("⚠️ 自動抓取 CB 失敗 (IP 限制)")
                st.markdown("**👇 沒關係，點下方按鈕直接看：**")
                
                url_histock = f"https://histock.tw/stock/{stock_id}/%E5%8F%AF%E8%BD%89%E5%82%B5"
                url_goodinfo = f"https://goodinfo.tw/tw/StockIssuanceCB.asp?STOCK_ID={stock_id}"
                
                st.markdown(f"""
                <a href="{url_histock}" target="_blank" class="fallback-btn">👉 開啟 HiStock (推薦上櫃用)</a>
                <a href="{url_goodinfo}" target="_blank" class="fallback-btn">👉 開啟 Goodinfo</a>
                """, unsafe_allow_html=True)
                
                with st.expander("🧮 看到價格了？手動算一下"):
                    u_conv = st.number_input("輸入轉換價", min_value=0.0)
                    if u_conv > 0:
                        u_parity = (price / u_conv) * 100
                        st.metric("平價 (Parity)", f"{u_parity:.2f}")

        else:
            st.error(f"❌ 找不到代號 {stock_id}。")
            st.write("如果是剛上櫃的新股，可能資料庫尚未更新。")
