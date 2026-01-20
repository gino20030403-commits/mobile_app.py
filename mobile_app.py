import streamlit as st
import pandas as pd
import requests
import re

# --- 1. 版面設定 ---
st.set_page_config(page_title="CB 深度鑑識", page_icon="🧐", layout="centered")

# --- 2. CSS 美化 ---
st.markdown("""
<style>
    .stApp { font-family: -apple-system, sans-serif; }
    .stNumberInput input { font-size: 20px !important; }
    .stTextInput input { font-size: 20px !important; }
    
    /* 卡片通用 */
    .card { padding: 15px; border-radius: 10px; margin-bottom: 15px; text-align: center; border: 2px solid #ddd; }
    .card-title { font-size: 20px; font-weight: 900; margin-bottom: 5px; }
    .card-desc { font-size: 15px; text-align: left; margin-top: 10px; line-height: 1.5; }
    
    /* 風險分析區塊 */
    .risk-box { background-color: #f1f8e9; padding: 15px; border-radius: 8px; border-left: 5px solid #33691e; margin-top: 10px; text-align: left;}
    .risk-title { font-weight: bold; color: #33691e; font-size: 16px; margin-bottom: 5px; }
    
    /* 顏色定義 */
    .danger { background-color: #ffebee; border-color: #ef5350; color: #c62828; }
    .warning { background-color: #fff3e0; border-color: #ffb74d; color: #ef6c00; }
    .safe { background-color: #e8f5e9; border-color: #66bb6a; color: #2e7d32; }
    .neutral { background-color: #f5f5f5; border-color: #bdbdbd; color: #616161; }

    .big-num { font-size: 24px; font-weight: bold; }
    .highlight { font-weight: bold; background-color: rgba(255,255,255,0.5); padding: 2px 5px; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

st.title("🧐 CB 深度鑑識系統")

# --- 3. 爬蟲輔助 ---
def fetch_cb_data(text_input):
    code_match = re.search(r"\d{4,6}", text_input)
    if not code_match: return 0.0
    code = code_match.group(0)
    try:
        url = f"https://histock.tw/stock/{code}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=3)
        if res.status_code == 200:
            dfs = pd.read_html(res.text)
            for df in dfs:
                row_text = df.to_string()
                if "轉換價" in row_text:
                    nums = re.findall(r"\d+\.?\d*", row_text)
                    for n in nums:
                        f_n = float(n)
                        if 10 <= f_n <= 2000: return f_n
    except: return 0.0
    return 0.0

# --- 4. 輸入區 ---
with st.container():
    st.markdown("### 1️⃣ 設定參數")
    col_input, col_btn = st.columns([3, 1])
    with col_input:
        cb_text = st.text_input("代號或名稱", placeholder="例: 64633 / 志聖三", key="cb_input_key")
    with col_btn:
        st.write("") 
        st.write("") 
        auto_fill = st.button("🪄 試抓")

    if 'k_val' not in st.session_state: st.session_state['k_val'] = 0.0
    if 'auc_val' not in st.session_state: st.session_state['auc_val'] = 100.0

    if auto_fill and cb_text:
        with st.spinner("搜尋中..."):
            fetched_price = fetch_cb_data(cb_text)
            if fetched_price > 0:
                st.session_state['k_val'] = fetched_price
                st.success(f"✅ 抓到了！K：{fetched_price}")
            else:
                st.warning("⚠️ 查無資料，請手動輸入")

    c1, c2 = st.columns(2)
    conv_price = c1.number_input("1. 轉換價格 (K)", min_value=0.0, step=0.1, key='k_val')
    auction_min = c2.number_input("2. 最低得標/成本", min_value=0.0, step=0.1, key='auc_val')

st.markdown("### 2️⃣ 盤中戰場")
c3, c4 = st.columns(2)
s_price = c3.number_input("現股股價 (S)", value=0.0, step=0.5)
cb_price = c4.number_input("CB 成交價 (P)", value=0.0, step=0.5)

# --- 5. 核心分頁 ---
tab1, tab2, tab3 = st.tabs(["⚔️ 深度戰情室", "⚖️ 競拍反推", "📋 防雷SOP"])

# ==================================================
# TAB 1: 深度戰情室 (你的核心邏輯)
# ==================================================
with tab1:
    if conv_price > 0 and s_price > 0 and cb_price > 0:
        # 基礎計算
        parity = (s_price / conv_price) * 100
        premium = ((cb_price - parity) / parity) * 100
        implied_s = (cb_price / 100) * conv_price  # 隱含股價
        
        # 你的判斷邏輯
        if premium >= 20:
            status = "🔴 市場過熱 (High Premium)"
            style = "danger"
            one_sentence = f"溢價 {premium:.1f}% 偏熱！現股短線不便宜，CB 買家有殺溢價風險。"
            risk_who = """
            <b>💀 對 CB 買家：危險！</b><br>你付了 Parity + 超過 20% 的溢價。只要情緒冷卻，CB 價格會比股價跌得更慘 (殺溢價)。<br>
            <b>⚠️ 對現股買家：偏貴。</b><br>市場在賭上漲劇本，但價格已含大量情緒與波動率，容易震盪。
            """
        elif 10 <= premium < 20:
            status = "🟡 中性區間 (Neutral)"
            style = "warning"
            one_sentence = f"溢價 {premium:.1f}% 中性。行情由現股主導，觀察籌碼與量能。"
            risk_who = """
            <b>⚖️ 風險平衡。</b><br>市場給予合理的 10~15% 時間價值。<br>若現股續強，CB 會跟漲；若盤整，溢價會慢慢收斂。
            """
        elif 5 <= premium < 10:
            status = "🟢 情緒退潮 (Safe)"
            style = "safe"
            one_sentence = f"溢價 {premium:.1f}% 冷卻。現股進入「不貴」區，長線甜蜜點。"
            risk_who = """
            <b>💎 對 CB 買家：安全。</b><br>下檔有 Parity 保護，溢價低，勝率高。<br>
            <b>✅ 對現股買家：機會。</b><br>市場不給太多情緒溢價，若基本面好，這是佈局良機。
            """
        elif premium < 5:
            status = "❄️ 貼近價值 (Undervalued)"
            style = "neutral"
            one_sentence = f"溢價 {premium:.1f}% 極低！若現股沒爛，這是送分題。"
            risk_who = "<b>🚀 極佳買點。</b><br>市場完全不給時間價值，通常是錯殺或起漲前兆。"
        else:
            status, style = "⚪ 計算中", "neutral"

        # 顯示主卡片
        st.markdown(f"""
        <div class="card {style}">
            <div class="card-title">{status}</div>
            <div style="display:flex; justify-content:center; gap:20px; margin:10px 0;">
                <div><small>溢價率 (Premium)</small><br><span class="big-num">{premium:+.1f}%</span></div>
                <div><small>Parity</small><br><span class="big-num">{parity:.1f}</span></div>
            </div>
            <div style="background:rgba(255,255,255,0.7); padding:5px; border-radius:5px; font-weight:bold; color:#333;">
                💬 {one_sentence}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 隱含劇本分析 (Implied Script)
        st.markdown("#### 🎬 市場正在押注的劇本")
        st.info(f"""
        CB 成交在 **{cb_price}** 元 
        👉 等於市場在押 **「未來股價會看到 {implied_s:.1f} 元」**
        
        (目前現股 {s_price}，距離劇本還有 {implied_s - s_price:+.1f} 元的想像空間)
        """)

        # 風險歸屬分析 (Risk Attribution)
        st.markdown("#### 🔍 深度解讀：誰在承擔風險？")
        st.markdown(f"""
        <div class="risk-box">
            {risk_who}
        </div>
        """, unsafe_allow_html=True)
        
        # 你的觀察指標
        if premium > 25:
             st.caption("👀 **觀察重點**：若 Premium 開始從 30% 掉到 15% 以下，且現股沒崩，代表短線風險正在下降 (泡沫擠乾)。")

    else:
        st.info("👈 請輸入現股與 CB 價格")

# ==================================================
# TAB 2: 競拍反推 (保留 v18)
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
                desc = f"現股強勢。
