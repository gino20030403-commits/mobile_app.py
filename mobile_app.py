import streamlit as st
import yfinance as yf
import pandas as pd
import requests

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

# --- 核心修復：建立偽裝 Session ---
# 這是解決 "Rate Limited" 的關鍵，偽裝成一般的瀏覽器
def get_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    })
    return session

# --- 3. 爬蟲函數 (抓 CB 資料) ---
@st.cache_data(ttl=1800)
def get_cb_data(stock_id):
    try:
        url = f"https://goodinfo.tw/tw/StockIssuanceCB.asp?STOCK_ID={stock_id}"
        # 使用我們設定好的 Session
        session = get_session()
        res = session.get(url)
        res.encoding = "utf-8"
        dfs = pd.read_html(res.text)
        for df in dfs:
            if "轉換價格" in df.columns:
                return df[['債券名稱', '轉換價格']].head(3)
        return None
    except:
        return None

# --- 4. 輔助顯示函數 ---
def card(title, value, sub="", color_class=""):
    st.markdown(f"""
    <div class="card {color_class}">
        <div class="card-header">{title}</div>
        <div class="card-value">{value}</div>
        <div class="card-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

# --- 5. App 主介面 ---
st.title("📱 CB 價值精算機")
st.caption("防擋版 v2.0")

col1, col2 = st.columns([3, 1])
with col1:
    stock_input = st.text_input("股票代號", placeholder="如: 3293", label_visibility="collapsed")
with col2:
    run_btn = st.button("計算")

if run_btn or stock_input:
    stock_id = stock_input.strip()
    
    with st.spinner('連線中 (已啟用防擋機制)...'):
        try:
            # 建立 Session
            session = get_session()
            
            # A. 抓現股 (將 Session 傳入 yfinance)
            ticker = f"{stock_id}.TW"
            stock = yf.Ticker(ticker, session=session) # 關鍵修改
            
            # 嘗試獲取價格，如果失敗則試試上櫃
            try:
                info = stock.info
                price = info.get('currentPrice') or info.get('regularMarketPrice')
            except:
                price = None

            if not price:
                ticker = f"{stock_id}.TWO"
                stock = yf.Ticker(ticker, session=session) # 關鍵修改
                try:
                    info = stock.info
                    price = info.get('currentPrice') or info.get('regularMarketPrice')
                except:
                    price = None

            if price:
                name = info.get('longName', stock_id)
                st.write(f"### 📊 {name} ({stock_id})")
                card("目前股價", f"{price} 元", "Yahoo Finance 即時數據", "highlight-blue")
                
                # B. 抓 CB
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
                            
                            # 簡易反推
                            target_120 = conv_price * 1.2
                            st.info(f"🚀 若希望債券漲到 120，現股需漲到: **{target_120:.1f}**")
                else:
                    st.warning("查無可轉債，或來源暫時封鎖")
            else:
                st.error("無法抓取股價，可能流量限制仍在冷卻中，請過 5 分鐘再試。")
        except Exception as e:
            st.error(f"連線錯誤: {e}")
