import streamlit as st
import pandas as pd
import requests

# --- 1. 版面設定 ---
st.set_page_config(page_title="CB 智能戰情室", page_icon="🤖", layout="centered")

# --- 2. CSS 美化 ---
st.markdown("""
<style>
    .stApp { font-family: -apple-system, sans-serif; }
    .stNumberInput input { font-size: 20px !important; }
    .stTextInput input { font-size: 20px !important; }
    
    /* 卡片樣式 */
    .card { padding: 15px; border-radius: 10px; margin-bottom: 15px; text-align: center; border: 2px solid #ddd; }
    .card-title { font-size: 20px; font-weight: 900; margin-bottom: 5px; }
    .card-desc { font-size: 15px; text-align: left; margin-top: 10px; line-height: 1.5; }
    
    /* 狀態色 */
    .danger { background-color: #ffebee; border-color: #ef5350; color: #c62828; }
    .warning { background-color: #fff3e0; border-color: #ffb74d; color: #ef6c00; }
    .safe { background-color: #e8f5e9; border-color: #66bb6a; color: #2e7d32; }
    .neutral { background-color: #f5f5f5; border-color: #bdbdbd; color: #616161; }

    .big-num { font-size: 24px; font-weight: bold; }
    .highlight { font-weight: bold; background-color: rgba(255,255,255,0.5); padding: 2px 5px; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

st.title("🤖 CB 智能戰情室")

# --- 3. 爬蟲核心 (抓取基本資料) ---
def fetch_cb_basic_info(code):
    """
    從 HiStock 抓取可轉債的基本資料 (名稱、轉換價)
    備用來源：如果是新掛牌，嘗試抓取發行資訊
    """
    try:
        # 來源 1: HiStock (資料結構最完整)
        url = f"https://histock.tw/stock/{code}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        res = requests.get(url, headers=headers, timeout=5)
        
        if res.status_code == 200:
            dfs = pd.read_html(res.text)
            
            # 初始化回傳變數
            name = ""
            conv_price = 0.0
            
            # 1. 抓名稱 (通常在 meta tag 或 title，這裡簡化用表格判斷)
            # HiStock 的表格通常第一個是即時報價，裡面有簡稱
            
            # 2. 抓轉換價 (在「可轉債基本資料」表格中)
            for df in dfs:
                # 尋找含有 "轉換價格" 字眼的表格
                # 表格通常是直向 Key-Value，需要轉置或遍歷
                df_str = df.to_string()
                if "轉換價" in df_str:
                    # 暴力搜尋
                    for idx, row in df.iterrows():
                        for col in df.columns:
                            val = str(row[col])
                            if "轉換價" in val:
                                # 假設數值在下一欄
                                try:
                                    # 嘗試找同一列的下一個值，或是下一列的值
                                    # HiStock 表格結構較固定，通常是: [標籤] [數值]
                                    # 我們直接把整個 df 轉成 dict 來找
                                    pass 
                                except: pass
            
            # 針對 HiStock 結構的特定解析 (較穩定的寫法)
            # 直接解析 HTML 會更準，但這裡用 pandas 快速處理
            # 搜尋所有表格，只要看到數值類似轉換價 (通常 10~300) 且欄位對應
            
            # 為了避免過度複雜的解析導致錯誤，這裡改用備案：
            # 如果是新上市，轉換價通常等於 (發行面額 / 轉換比例) 但這太難算
            # 我們直接抓「基本資料表」
            
            for df in dfs:
                if df.shape[1] >= 2: # 至少兩欄
                    # 將表格轉為字典列表，尋找關鍵字
                    for i in range(len(df)):
                        row_text = "".join([str(x) for x in df.iloc[i].values])
                        if "轉換價" in row_text:
                            # 提取該列中的數字
                            import re
                            nums = re.findall(r"\d+\.?\d*", row_text)
                            # 通常轉換價是該行唯一的浮點數
                            for n in nums:
                                f_n = float(n)
                                if 10 <= f_n <= 1000: # 合理範圍
                                    conv_price = f_n
                                    break
                        if "名稱" in row_text or "代碼" in row_text:
                            # 嘗試抓名稱 (略過，用代號即可)
                            pass
            
            return conv_price
            
    except Exception as e:
        return 0.0
    return 0.0

# --- 4. 智能輸入區 ---
with st.container():
    st.markdown("### 1️⃣ 設定目標 (輸入代號自動抓)")
    
    col_input, col_btn = st.columns([3, 1])
    with col_input:
        cb_code = st.text_input("輸入可轉債代號", placeholder="例如 64633 (志聖三)", max_chars=6)
    with col_btn:
        st.write("") # 佔位
        st.write("") 
        auto_fill = st.button("🔍 抓資料")

    # 初始化 Session State
    if 'conv_price_val' not in st.session_state: st.session_state['conv_price_val'] = 0.0
    if 'auction_cost_val' not in st.session_state: st.session_state['auction_cost_val'] = 100.0

    # 按下按鈕後的邏輯
    if auto_fill and cb_code:
        with st.spinner(f"正在從 HiStock 抓取 {cb_code} 資料..."):
            fetched_price = fetch_cb_basic_info(cb_code)
            if fetched_price > 0:
                st.session_state['conv_price_val'] = fetched_price
                st.success(f"✅ 成功抓取！轉換價：{fetched_price}")
            else:
                st.warning("⚠️ 自動抓取失敗 (可能是新掛牌資料尚未同步)，請手動輸入。")

    # 參數顯示與修正區
    st.markdown("👇 **確認參數 (可手動修改)**")
    c1, c2 = st.columns(2)
    conv_price = c1.number_input("1. 轉換價格 (K)", value=st.session_state['conv_price_val'], step=0.1, key='k_input')
    auction_min = c2.number_input("2. 最低得標價/成本", value=st.session_state['auction_cost_val'], step=0.1, help="新債請查新聞，舊債預設 100")

# --- 5. 盤中戰場 ---
st.markdown("### 2️⃣ 盤中輸入 (即時)")
c3, c4 = st.columns(2)
s_price = c3.number_input("現股股價 (S)", value=0.0, step=0.5)
cb_price = c4.number_input("CB 成交價 (P)", value=0.0, step=0.5)

# --- 6. 核心功能分頁 ---
tab1, tab2, tab3 = st.tabs(["⚔️ 戰情室", "⚖️ 競拍反推", "📋 防雷SOP"])

# ==================================================
# TAB 1: 戰情室
# ==================================================
with tab1:
    if conv_price > 0 and s_price > 0 and cb_price > 0:
        parity = (s_price / conv_price) * 100
        premium = ((cb_price - parity) / parity) * 100
        
        # 訊號邏輯
        if premium >= 20:
            status, style, advice = "🔴 追高風險 (貴)", "danger", "溢價 > 20%！小心籌碼過熱，除非現股噴出，否則回檔快。"
        elif 10 <= premium < 20:
            status, style, advice = "🟡 中性觀察 (穩)", "warning", "溢價 10~20%：合理區間。多頭市場常見，隨現股漲跌。"
        elif 5 <= premium < 10:
            status, style, advice = "🟢 相對便宜 (安)", "safe", "溢價 5~10%：甜蜜點。有 Parity 保護，長線投資佳。"
        elif premium < 5:
            status, style, advice = "❄️ 貼近平價 (殺)", "neutral", "溢價 < 5%：警示或機會。若現股漲，CB 被低估 (買點)。"
        else: status, style, advice = "⚪ 計算中", "neutral", "..."

        st.markdown(f"""
        <div class="card {style}">
            <div class="card-title">{status}</div>
            <div style="display:flex; justify-content:center; gap:20px; margin:10px 0;">
                <div><small>溢價率</small><br><span class="big-num">{premium:+.1f}%</span></div>
                <div><small>Parity</small><br><span class="big-num">{parity:.1f}</span></div>
            </div>
            <div class="card-desc">{advice}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("👈 請先完成上方「步驟 1 & 2」的輸入")

# ==================================================
# TAB 2: 競拍反推
# ==================================================
with tab2:
    if conv_price > 0 and auction_min > 0:
        def get_implied_s(p_rate): return conv_price * (auction_min / (100 * (1 + p_rate)))
        s_p20 = get_implied_s(0.20)
        
        if s_price > 0:
            curr_parity = (s_price / conv_price) * 100
            req_premium = ((auction_min - curr_parity) / curr_parity) * 100
            
            if s_price < s_p20:
                status, style = "🔴 得標價危險", "danger"
                desc = f"現股太弱。要維持得標價 {auction_min}，需 <span class='highlight'>{req_premium:.1f}%</span> 高溢價，成本線難守。"
            else:
                status, style = "🟢 得標價穩固", "safe"
                desc = f"現股強勢。得標價 {auction_min} 僅需 <span class='highlight'>{req_premium:.1f}%</span> 溢價 (或更低) 即可維持。"
            
            st.markdown(f"""
            <div class="card {style}">
                <div class="card-title">{status}</div>
                <div class="card-desc">{desc}</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.caption("📉 競拍成本反推表")
        data = []
        for rate in [0.10, 0.15, 0.20, 0.25]:
            imp_s = get_implied_s(rate)
            marker = "👈 目前" if abs(s_price - imp_s) < 5 and s_price > 0 else ""
            data.append({"假設溢價": f"{rate*100:.0f}%", "反推現股": f"{imp_s:.1f}", "狀態": marker})
        st.table(pd.DataFrame(data))

# ==================================================
# TAB 3: 防雷 SOP
# ==================================================
with tab3:
    st.markdown("### 🛡️ 買前檢查清單")
    with st.expander("1. 條款與結構", expanded=True):
        st.write("- [ ] **Put (賣回權)**：幾年賣回？價格多少？(下檔保護)")
        st.write("- [ ] **Call (贖回權)**：有無強迫贖回條款？(上檔天花板)")
        st.write("- [ ] **轉換期間**：是否還在閉鎖期？")
    with st.expander("2. 籌碼與價格"):
        st.write("- [ ] **競拍成本**：現在價格離得標價多遠？")
        st.write("- [ ] **首日效應**：是否為掛牌前 5 日？(無漲跌幅限制，波動大)")
        st.write("- [ ] **溢價率**：是否 > 20% (過熱)？")
