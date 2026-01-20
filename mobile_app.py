import streamlit as st
import yfinance as yf
import pandas as pd
import requests

# --- 1. 手機版面設定 ---
st.set_page_config(page_title="CB 計算機", page_icon="📱", layout="centered")

# --- 2. CSS 手機優化 (大按鈕、卡片式、去除多餘邊距) ---
st.markdown("""
<style>
    /* 全域字體優化 */
    .stApp { font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
    
    /* 輸入框與按鈕加大，方便手指點擊 */
    .stTextInput input { font-size: 18px; padding: 10px; }
    .stButton button { width: 100%; font-size: 18px; font-weight: bold; padding: 10px; }
    
    /* 數據卡片樣式 */
    .card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.08);
        margin-bottom: 12px;
        border: 1px solid #f0f0f0;
    }
    .card-header { font-size: 14px; color: #888; margin-bottom: 4px; }
    .card-value { font-size: 24px; font-weight: 700; color: #333; }
    .card-sub { font-size: 13px; color: #666; margin-top: 4px; }
    
    /* 重點區塊顏色 */
    .highlight-blue { border-left: 5px solid #2196f3; }
    .highlight-green { border-left: 5px solid #4caf50; }
    .highlight-orange { border-left: 5px solid #ff9800; }
</style>
""", unsafe_allow_html=True)

# --- 3. 爬蟲函數 (抓 CB 資料) ---
@st.cache_data(ttl=1800)
def get_cb_data(stock_id):
    try:
        url = f"https://goodinfo.tw/tw/StockIssuanceCB.asp?STOCK_ID={stock_id}"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers)
        res.encoding = "utf-8"
        dfs = pd.read_html(res.text)
        for df in dfs:
            if "轉換價格" in df.columns:
                # 只取最新的一筆有效資料
                return df[['債券名稱', '轉換價格']].head(3)
        return None
    except:
        return None

# --- 4. 輔助顯示函數 (生成 HTML 卡片) ---
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
st.write("輸入股號，一鍵計算合理價")

# 輸入區 (置頂)
col1, col2 = st.columns([3, 1])
with col1:
    stock_input = st.text_input("股票代號", placeholder="如: 3293", label_visibility="collapsed")
with col2:
    run_btn = st.button("計算")

if run_btn or stock_input:
    stock_id = stock_input.strip()
    
    with st.spinner('連線中...'):
        try:
            # A. 抓現股
            ticker = f"{stock_id}.TW"
            stock = yf.Ticker(ticker)
            info = stock.info
            price = info.get('currentPrice') or info.get('regularMarketPrice')
            
            if not price:
                ticker = f"{stock_id}.TWO"
                stock = yf.Ticker(ticker)
                info = stock.info
                price = info.get('currentPrice') or info.get('regularMarketPrice')

            if price:
                name = info.get('longName', stock_id)
                
                # 顯示現股資訊
                st.write(f"### 📊 {name} ({stock_id})")
                card("目前股價 (Spot Price)", f"{price} 元", "即時/收盤價", "highlight-blue")
                
                # B. 抓 CB
                cb_df = get_cb_data(stock_id)
                
                if cb_df is not None and not cb_df.empty:
                    
                    # 遍歷每一個 CB (例如 鈊象一, 鈊象二)
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
                            
                            # 顯示基本轉換數據
                            c1, c2 = st.columns(2)
                            with c1:
                                st.metric("轉換價", f"{conv_price}")
                            with c2:
                                st.metric("平價 (Parity)", f"{parity:.2f}")

                            # 1️⃣ 合理債券價格計算
                            st.markdown("#### 💰 合理債券價格")
                            st.caption("若市價低於此區間則相對便宜")
                            
                            fair_low = parity * 1.05
                            fair_high = parity * 1.10
                            
                            card("合理買進區間 (溢價 5%~10%)", 
                                 f"{fair_low:.1f} ~ {fair_high:.1f} 元", 
                                 f"保守估值: {parity:.1f} 元", 
                                 "highlight-green")

                            # 2️⃣ 合理現股價格反推
                            st.markdown("#### 📈 合理現股價格")
                            st.caption("若希望債券漲到目標價，現股需漲到多少？")
                            
                            # 為了手機顯示，改用列點式，不用寬表格
                            target_120 = conv_price * (120 / 100)
                            target_130 = conv_price * (130 / 100)
                            
                            diff_120 = ((target_120 - price) / price) * 100
                            diff_130 = ((target_130 - price) / price) * 100

                            st.markdown(f"""
                            <div style="background:#fff; padding:15px; border-radius:10px; border:1px solid #eee;">
                                <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                                    <span>🎯 債券目標 <b>120</b> 元</span>
                                    <span>現股需漲至 <b style="color:#d32f2f;">{target_120:.1f}</b> ({diff_120:+.1f}%)</span>
                                </div>
                                <div style="border-top:1px solid #eee; margin:5px 0;"></div>
                                <div style="display:flex; justify-content:space-between; margin-top:10px;">
                                    <span>🚀 債券目標 <b>130</b> 元</span>
                                    <span>現股需漲至 <b style="color:#d32f2f;">{target_130:.1f}</b> ({diff_130:+.1f}%)</span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                        else:
                            st.warning(f"{cb_name} 資料異常 (無轉換價)")
                else:
                    st.info("此股近期無發行可轉債")
            else:
                st.error("查無此股價，請確認代號")
        except Exception as e:
            st.error(f"錯誤: {e}")