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
    .highlight-orange { border-left: 5px solid #ff9800; }
</style>
""", unsafe_allow_html=True)

# --- 3. 核心功能：多重來源抓股價 (Smart Fetch) ---
def get_price_smart(stock_id):
    logs = [] 
    
    # === A: Yahoo Finance (History) ===
    try:
        t = yf.Ticker(f"{stock_id}.TW")
        hist = t.history(period="1d")
        if not hist.empty: return float(hist['Close'].iloc[-1]), "Yahoo (TW)"
        
        t = yf.Ticker(f"{stock_id}.TWO")
        hist = t.history(period="1d")
        if not hist.empty: return float(hist['Close'].iloc[-1]), "Yahoo (TWO)"
    except Exception as e: logs.append(f"Yahoo: {e}")

    # === B: twstock (證交所) ===
    try:
        stock = twstock.realtime.get(stock_id)
        if stock['success']:
            price = stock['realtime'].get('latest_trade_price')
            if price == '-' or not price:
                price = stock['realtime'].get('best_bid_price', [None])[0]
            if price and price != '-': return float(price), "證交所/櫃買"
    except Exception as e: logs.append(f"Twstock: {e}")

    # === C: Goodinfo (備用) ===
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        url = f"https://goodinfo.tw/tw/StockDetail.asp?STOCK_ID={stock_id}"
        res = requests.get(url, headers=headers, timeout=5)
        res.encoding = "utf-8"
        dfs = pd.read_html(res.text)
        for df in dfs:
            if "成交價" in df.columns: return float(df.iloc[0]["成交價"]), "Goodinfo"
    except: pass

    return None, None

# --- 4. 抓可轉債 (雙引擎：Goodinfo + HiStock) ---
def get_cb_from_goodinfo(stock_id):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        url = f"https://goodinfo.tw/tw/StockIssuanceCB.asp?STOCK_ID={stock_id}"
        res = requests.get(url, headers=headers, timeout=5)
        res.encoding = "utf-8"
        dfs = pd.read_html(res.text)
        for df in dfs:
            if "轉換價格" in df.columns:
                return df[['債券名稱', '轉換價格']].head(3), "Goodinfo"
        return None, None
    except:
        return None, None

def get_cb_from_histock(stock_id):
    # HiStock 嗨投資 - 結構比較簡單，通常較少擋 IP
    try:
        url = f"https://histock.tw/stock/{stock_id}/%E5%8F%AF%E8%BD%89%E5%82%B5" # /可轉債
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=5)
        # HiStock 有時不需要特定 encoding，pandas 會自動處理
        
        dfs = pd.read_html(res.text)
        # HiStock 的表格通常包含 "名稱", "代碼", "轉換價"
        for df in dfs:
            if "名稱" in df.columns and "轉換價" in df.columns:
                # 重新命名以符合我們的格式
                df = df.rename(columns={"名稱": "債券名稱", "轉換價": "轉換價格"})
                # 過濾掉已經下市或無效的 (通常HiStock只列出有效的)
                return df[['債券名稱', '轉換價格']].head(3), "HiStock"
        return None, None
    except:
        return None, None

@st.cache_data(ttl=1800)
def get_cb_data_smart(stock_id):
    # 策略 1: 先試 Goodinfo (資料最詳細)
    df, source = get_cb_from_goodinfo(stock_id)
    if df is not None and not df.empty:
        return df, source
        
    # 策略 2: 如果失敗，試試 HiStock (防擋能力較強)
    df, source = get_cb_from_histock(stock_id)
    if df is not None and not df.empty:
        return df, source
        
    return None, None

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
st.caption("v6.0 (Dual-Engine CB Fetch)")

col1, col2 = st.columns([3, 1])
with col1:
    stock_input = st.text_input("股票代號", placeholder="如: 3715", label_visibility="collapsed")
with col2:
    run_btn = st.button("計算")

if run_btn or stock_input:
    stock_id = stock_input.strip()
    
    with st.spinner(f'正在為您掃描 {stock_id} ...'):
        
        # 1. 抓股價
        price, p_source = get_price_smart(stock_id)

        if price:
            # 決定顏色
            p_color = "highlight-blue"
            if "Yahoo" not in p_source and "證交所" not in p_source: p_color = "highlight-orange"
            
            st.write(f"### 📊 {stock_id} 股價資訊")
            card("目前股價", f"{price} 元", f"來源: {p_source}", p_color)
            
            # 2. 抓 CB (智慧雙引擎)
            cb_df, cb_source = get_cb_data_smart(stock_id)
            
            if cb_df is not None and not cb_df.empty:
                st.info(f"✅ 可轉債資料來源：{cb_source}")
                
                for idx, row in cb_df.iterrows():
                    cb_name = row['債券名稱']
                    try:
                        # 清理數據 (有些網站會有 * 或 ,)
                        raw_price = str(row['轉換價格']).replace(',', '').replace('*', '')
                        conv_price = float(raw_price)
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
                        st.markdown(f"""
                        <div style="background-color:#e8f5e9; padding:10px; border-radius:5px; font-size:14px;">
                        🚀 目標債價 <b>120</b> 元 ➔ 現股需漲至 <b>{target_120:.1f}</b>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.warning("查無可轉債 (Goodinfo 與 HiStock 皆無資料或連線失敗)")
                st.markdown("[👉 點此直接去 HiStock 確認](https://histock.tw/stock/" + stock_id + "/%E5%8F%AF%E8%BD%89%E5%82%B5)")
        else:
            st.error(f"❌ 找不到 {stock_id} 的股價，請稍後再試。")
