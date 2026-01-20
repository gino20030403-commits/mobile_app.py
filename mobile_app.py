import streamlit as st
import pandas as pd
import requests
import twstock
import yfinance as yf

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
    .card-value { font-size: 24px; font-weight: 700; color: #333; }
    .card-sub { font-size: 13px; color: #666; margin-top: 4px; }
    .highlight-blue { border-left: 5px solid #2196f3; }
    .highlight-green { border-left: 5px solid #4caf50; }
</style>
""", unsafe_allow_html=True)

# --- 3. 核心功能：多重來源抓股價 (Smart Fetch) ---
def get_price_smart(stock_id):
    logs = [] # 紀錄嘗試過程
    
    # === 來源 A: Yahoo Finance (使用 history 函數，最穩) ===
    try:
        # 先試上市
        t = yf.Ticker(f"{stock_id}.TW")
        hist = t.history(period="1d")
        if not hist.empty:
            price = hist['Close'].iloc[-1]
            return float(price), "Yahoo Finance (TW)"
        
        # 再試上櫃
        t = yf.Ticker(f"{stock_id}.TWO")
        hist = t.history(period="1d")
        if not hist.empty:
            price = hist['Close'].iloc[-1]
            return float(price), "Yahoo Finance (TWO)"
        
        logs.append("Yahoo: 無資料")
    except Exception as e:
        logs.append(f"Yahoo Error: {str(e)}")

    # === 來源 B: twstock (證交所官方 API) ===
    try:
        stock = twstock.realtime.get(stock_id)
        if stock['success']:
            price = stock['realtime'].get('latest_trade_price')
            # 處理沒成交價的情況 (改抓買進價)
            if price == '-' or not price:
                price = stock['realtime'].get('best_bid_price', [None])[0]
            
            if price and price != '-':
                return float(price), "證交所/櫃買中心"
        logs.append("twstock: 抓取失敗")
    except Exception as e:
        logs.append(f"twstock Error: {str(e)}")

    # === 來源 C: Goodinfo (爬蟲，最後手段) ===
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        url = f"https://goodinfo.tw/tw/StockDetail.asp?STOCK_ID={stock_id}"
        res = requests.get(url, headers=headers, timeout=5)
        res.encoding = "utf-8"
        dfs = pd.read_html(res.text)
        for df in dfs:
            if "成交價" in df.columns:
                price = df.iloc[0]["成交價"]
                return float(price), "Goodinfo"
            # 暴力搜尋表格內容
            if "成交價" in df.to_string():
                # 這裡省略複雜解析，只要上面兩種都失敗，通常 Goodinfo 也會擋 IP
                pass
        logs.append("Goodinfo: 解析失敗")
    except Exception as e:
        logs.append(f"Goodinfo Error: {str(e)}")

    # 全部失敗
    print(logs) # 在後台印出錯誤日誌方便除錯
    return None, None

# --- 4. 抓可轉債 (維持 Goodinfo) ---
@st.cache_data(ttl=1800)
def get_cb_data(stock_id):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        url = f"https://goodinfo.tw/tw/StockIssuanceCB.asp?STOCK_ID={stock_id}"
        res = requests.get(url, headers=headers, timeout=5)
        res.encoding = "utf-8"
        dfs = pd.read_html(res.text)
        for df in dfs:
            if "轉換價格" in df.columns:
                return df[['債券名稱', '轉換價格']].head(3)
        return None
    except:
        return None

# --- 5. 輔助顯示函數 ---
def card(title, value, sub="", color_class=""):
    st.markdown(f"""
    <div class="card {color_class}">
        <div class="card-header">{title}</div>
        <div class="card-value">{value}</div>
        <div class="card-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

# --- 6. App 主介面 ---
st.title("📱 CB 價值精算機")
st.caption("v5.0 (Smart Multi-Source)")

col1, col2 = st.columns([3, 1])
with col1:
    stock_input = st.text_input("股票代號", placeholder="如: 2467", label_visibility="collapsed")
with col2:
    run_btn = st.button("計算")

if run_btn or stock_input:
    stock_id = stock_input.strip()
    
    # 顯示進度條，因為會嘗試多個來源
    with st.spinner(f'正在多方搜尋 {stock_id} 股價...'):
        
        # 1. 智慧抓股價
        price, source = get_price_smart(stock_id)

        if price:
            st.write(f"### 📊 {stock_id} 股價資訊")
            # 根據不同來源給不同顏色，讓你知道是誰立功了
            badge_color = "highlight-blue"
            if "Yahoo" in source: badge_color = "highlight-blue" # 藍色
            elif "證交所" in source: badge_color = "highlight-green" # 綠色
            elif "Goodinfo" in source: badge_color = "highlight-orange" # 橘色
            
            card("目前股價", f"{price} 元", f"資料來源: {source}", badge_color)
            
            # 2. 抓 CB
            cb_df = get_cb_data(stock_id)
            
            if cb_df is not None and not cb_df.empty:
                for idx, row in cb_df.iterrows():
                    cb_name = row['債券名稱']
                    try:
                        conv_price = float(str(row['轉換價格']).replace(',', ''))
                    except:
                        conv_price = 0
                        
                    if conv_price > 0:
                        parity = (price / conv_price) * 100
                        st.markdown("---")
                        st.subheader(f"🔗 {cb_name}")
                        
                        c1, c2 = st.columns(2)
                        with c1: st.metric("轉換價", f"{conv_price}")
                        with c2: st.metric("平價 (Parity)", f"{parity:.2f}")

                        fair_low = parity * 1.05
                        fair_high = parity * 1.10
                        
                        card("合理買進區間", 
                             f"{fair_low:.1f} ~ {fair_high:.1f}", 
                             f"平價: {parity:.1f}", 
                             "highlight-green")
                        
                        target_120 = conv_price * 1.2
                        st.info(f"🚀 若希望債券漲到 120，現股需漲到: **{target_120:.1f}**")
            else:
                st.warning("查無可轉債 (或資料讀取失敗)")
        else:
            st.error(f"❌ 找不到代號 {stock_id}。")
            st.markdown("""
            **可能原因：**
            1. 代號輸入錯誤。
            2. 雲端主機目前同時被 Yahoo、證交所與 Goodinfo 封鎖 (機率較低，但可能發生)。
            3. 請過 5 分鐘後再試一次。
            """)
