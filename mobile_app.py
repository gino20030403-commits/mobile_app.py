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
    .highlight-blue { border-left: 5px solid #2196f3; }
    .highlight-green { border-left: 5px solid #4caf50; }
    .fallback-btn {
        display: inline-block; text-decoration: none; background-color: #f1f3f4; 
        color: #333; padding: 10px 15px; border-radius: 8px; margin: 5px 0; 
        font-weight: bold; border: 1px solid #ccc; width: 100%; text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. 核心功能：多重來源抓股價 ---
def get_price_smart(stock_id):
    # Yahoo
    try:
        t = yf.Ticker(f"{stock_id}.TW")
        hist = t.history(period="1d")
        if not hist.empty: return float(hist['Close'].iloc[-1]), "Yahoo (TW)"
        t = yf.Ticker(f"{stock_id}.TWO")
        hist = t.history(period="1d")
        if not hist.empty: return float(hist['Close'].iloc[-1]), "Yahoo (TWO)"
    except: pass

    # twstock
    try:
        stock = twstock.realtime.get(stock_id)
        if stock['success']:
            price = stock['realtime'].get('latest_trade_price')
            if price == '-' or not price:
                price = stock['realtime'].get('best_bid_price', [None])[0]
            if price and price != '-': return float(price), "證交所/櫃買"
    except: pass

    # Goodinfo (最後手段)
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        url = f"https://goodinfo.tw/tw/StockDetail.asp?STOCK_ID={stock_id}"
        res = requests.get(url, headers=headers, timeout=3)
        res.encoding = "utf-8"
        dfs = pd.read_html(res.text)
        for df in dfs:
            if "成交價" in df.columns: return float(df.iloc[0]["成交價"]), "Goodinfo"
    except: pass

    return None, None

# --- 4. 抓可轉債 (附帶狀態回傳) ---
def get_cb_data_robust(stock_id):
    # 1. 嘗試 Goodinfo
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        url = f"https://goodinfo.tw/tw/StockIssuanceCB.asp?STOCK_ID={stock_id}"
        res = requests.get(url, headers=headers, timeout=3)
        if res.status_code == 200:
            dfs = pd.read_html(res.text)
            for df in dfs:
                if "轉換價格" in df.columns:
                    return df[['債券名稱', '轉換價格']].head(3), "Goodinfo", None
    except Exception as e:
        pass # 失敗就繼續

    # 2. 嘗試 HiStock
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        url = f"https://histock.tw/stock/{stock_id}/%E5%8F%AF%E8%BD%89%E5%82%B5"
        res = requests.get(url, headers=headers, timeout=3)
        if res.status_code == 200:
            dfs = pd.read_html(res.text)
            for df in dfs:
                # HiStock 欄位可能有變，嘗試模糊搜尋
                if "轉換價" in df.columns or "名稱" in df.columns:
                    df = df.rename(columns={"名稱": "債券名稱", "轉換價": "轉換價格", "代碼": "代號"})
                    if "債券名稱" in df.columns and "轉換價格" in df.columns:
                         return df[['債券名稱', '轉換價格']].head(3), "HiStock", None
    except Exception as e:
        pass

    # 3. 嘗試 MoneyDJ (新來源)
    try:
        url = f"https://www.moneydj.com/KMDJ/Common/ListBond.aspx?a={stock_id}"
        res = requests.get(url, timeout=3)
        if res.status_code == 200:
            dfs = pd.read_html(res.text)
            for df in dfs:
                if "轉換價格" in df.columns:
                     return df[['債券名稱', '轉換價格']].head(3), "MoneyDJ", None
    except:
        pass

    return None, None, "所有來源皆連線失敗 (IP被擋)"

# --- 5. 輔助顯示函數 ---
def card(title, value, sub="", color_class=""):
    st.markdown(f"""
    <div class="card {color_class}">
        <div class="card-header">{title}</div>
        <div class="card-value">{value}</div>
        <div style="font-size:13px; color:#666;">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

# --- 6. App 主介面 ---
st.title("📱 CB 價值精算機")
st.caption("v7.0 (Resilient Fallback Mode)")

col1, col2 = st.columns([3, 1])
with col1:
    stock_input = st.text_input("股票代號", placeholder="如: 3715", label_visibility="collapsed")
with col2:
    run_btn = st.button("計算")

if run_btn or stock_input:
    stock_id = stock_input.strip()
    
    with st.spinner(f'搜尋中...'):
        # A. 抓股價
        price, p_source = get_price_smart(stock_id)

        if price:
            st.write(f"### 📊 {stock_id} 股價資訊")
            # 股價卡片
            card("目前股價", f"{price} 元", f"來源: {p_source}", "highlight-blue")
            
            # B. 抓 CB
            cb_df, cb_source, error_msg = get_cb_data_robust(stock_id)
            
            if cb_df is not None and not cb_df.empty:
                # === 成功抓取 ===
                st.success(f"✅ 資料來源：{cb_source}")
                for idx, row in cb_df.iterrows():
                    cb_name = row['債券名稱']
                    try:
                        raw_val = str(row['轉換價格']).replace(',', '').replace('*', '')
                        conv_price = float(raw_val)
                    except: conv_price = 0
                        
                    if conv_price > 0:
                        parity = (price / conv_price) * 100
                        st.markdown("---")
                        st.subheader(f"🔗 {cb_name}")
                        
                        c1, c2 = st.columns(2)
                        with c1: st.metric("轉換價", f"{conv_price}")
                        with c2: st.metric("平價", f"{parity:.2f}")

                        fair_low = parity * 1.05
                        card("合理買進區間", f"{fair_low:.1f} 起", f"Parity: {parity:.1f}", "highlight-green")
            else:
                # === 抓取失敗 (啟用備用方案) ===
                st.warning("⚠️ 自動抓取失敗，可能是雲端 IP 被暫時封鎖。")
                
                st.markdown("### 👇 點擊下方按鈕直接查看 (最穩)")
                
                # 產生直接連結 (這是最保險的，絕對能看到資料)
                url_histock = f"https://histock.tw/stock/{stock_id}/%E5%8F%AF%E8%BD%89%E5%82%B5"
                url_goodinfo = f"https://goodinfo.tw/tw/StockIssuanceCB.asp?STOCK_ID={stock_id}"
                url_moneydj = f"https://www.moneydj.com/KMDJ/Common/ListBond.aspx?a={stock_id}"

                st.markdown(f"""
                <a href="{url_histock}" target="_blank" class="fallback-btn">👉 開啟 HiStock (嗨投資)</a>
                <a href="{url_goodinfo}" target="_blank" class="fallback-btn">👉 開啟 Goodinfo</a>
                <a href="{url_moneydj}" target="_blank" class="fallback-btn">👉 開啟 MoneyDJ</a>
                """, unsafe_allow_html=True)
                
                st.info("💡 提示：點開後找「轉換價格」，輸入到下方手動計算：")
                
                # 手動計算器 (讓 App 即使沒資料也有用)
                with st.expander("🧮 手動輸入轉換價來計算"):
                    user_conv = st.number_input("輸入您看到的轉換價", min_value=0.0, step=0.1)
                    if user_conv > 0:
                        user_parity = (price / user_conv) * 100
                        st.metric("即時平價 (Parity)", f"{user_parity:.2f}")
                        st.write(f"合理買進價約：{user_parity*1.05:.1f}")

        else:
            st.error(f"❌ 找不到代號 {stock_id}，請確認是否正確。")
