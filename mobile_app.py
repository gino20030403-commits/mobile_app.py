import streamlit as st
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

# --- 3. 核心爬蟲設定 (偽裝成一般人) ---
def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://goodinfo.tw/'
    }

# --- 4. 抓股價 (從 Goodinfo StockDetail 頁面) ---
# 這是這次修復的重點：不依賴 Yahoo 也不依賴證交所，直接爬網頁
def get_price_from_goodinfo(stock_id):
    try:
        url = f"https://goodinfo.tw/tw/StockDetail.asp?STOCK_ID={stock_id}"
        res = requests.get(url, headers=get_headers())
        res.encoding = "utf-8"
        
        # 解析網頁中的所有表格
        dfs = pd.read_html(res.text)
        
        # Goodinfo 的股價通常在最上面的表格，欄位包含 "成交價"
        # 我們遍歷表格尋找正確的數值
        for df in dfs:
            # 將表格轉為字串方便搜尋，或直接檢查欄位
            # Goodinfo 的表格排版有時是直的，有時是橫的，這裡做一個暴力搜尋
            if "成交價" in str(df.columns) or "成交價" in df.to_string():
                # 嘗試標準化表格
                # 情況A: 成交價是欄位名稱 (Header)
                if "成交價" in df.columns:
                    price = df.iloc[0]["成交價"]
                    return float(price), df.iloc[0].get("名稱", stock_id)
                
                # 情況B: 表格是 Key-Value 型 (例如第一欄是項目，第二欄是數值)
                # 這種情況比較複雜，我們把表格轉成字典來查
                try:
                    # 嘗試在整個 dataframe 裡找 "成交價" 這個字，然後取它右邊或下面的值
                    # 這裡簡化邏輯：Goodinfo 第一個大表格通常有一格叫 "成交價"
                    # 我們直接解析 HTML 本體可能更準，但用 pandas 比較快
                    # 針對 Goodinfo 第一張表通常如下：
                    # [0]   [1]    [2]   [3]
                    # 成交價  1050  昨收  1040
                    
                    # 搜尋所有格子
                    for r in range(len(df)):
                        for c in range(len(df.columns)):
                            if str(df.iloc[r, c]).strip() == "成交價":
                                # 找到成交價這三個字，數值通常在右邊 (c+1)
                                price_val = df.iloc[r, c+1]
                                return float(price_val), stock_id
                except:
                    continue
                    
        return None, None
    except Exception as e:
        # print(e) # 除錯用
        return None, None

# --- 5. 抓可轉債 (從 Goodinfo CB 頁面) ---
@st.cache_data(ttl=1800)
def get_cb_data(stock_id):
    try:
        url = f"https://goodinfo.tw/tw/StockIssuanceCB.asp?STOCK_ID={stock_id}"
        res = requests.get(url, headers=get_headers())
        res.encoding = "utf-8"
        dfs = pd.read_html(res.text)
        for df in dfs:
            if "轉換價格" in df.columns:
                return df[['債券名稱', '轉換價格']].head(3)
        return None
    except:
        return None

# --- 6. 輔助顯示函數 ---
def card(title, value, sub="", color_class=""):
    st.markdown(f"""
    <div class="card {color_class}">
        <div class="card-header">{title}</div>
        <div class="card-value">{value}</div>
        <div class="card-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

# --- 7. App 主介面 ---
st.title("📱 CB 價值精算機")
st.caption("v4.0 (All-Goodinfo Version)")

col1, col2 = st.columns([3, 1])
with col1:
    stock_input = st.text_input("股票代號", placeholder="如: 3293", label_visibility="collapsed")
with col2:
    run_btn = st.button("計算")

if run_btn or stock_input:
    stock_id = stock_input.strip()
    
    with st.spinner('正在從 Goodinfo 抓取資料...'):
        # 1. 抓現股 (Goodinfo)
        price, stock_name = get_price_from_goodinfo(stock_id)

        if price:
            st.write(f"### 📊 {stock_name} ({stock_id})")
            card("目前股價", f"{price} 元", "來源: Goodinfo", "highlight-blue")
            
            # 2. 抓 CB (Goodinfo)
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
                st.warning("此股無近期可轉債，或資料讀取失敗")
        else:
            # 如果還是失敗，顯示詳細建議
            st.error(f"找不到代號 {stock_id} 的股價。")
            st.info("💡 提示：請確認代號正確。若確定正確，可能是 Goodinfo 暫時阻擋了頻繁查詢，請過幾分鐘再試。")
