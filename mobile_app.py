import streamlit as st
import pandas as pd

# --- 1. 版面設定 ---
st.set_page_config(page_title="競拍鑑識反推", page_icon="⚖️", layout="centered")

# --- 2. CSS 美化 ---
st.markdown("""
<style>
    .stApp { font-family: -apple-system, sans-serif; }
    .stNumberInput input { font-size: 20px !important; }
    
    /* 鑑識卡片 */
    .result-card {
        padding: 20px; border-radius: 12px; margin-bottom: 20px;
        text-align: center; border: 2px solid #ddd;
    }
    .card-title { font-size: 20px; font-weight: bold; margin-bottom: 10px; }
    .card-content { font-size: 16px; line-height: 1.6; text-align: left; background: rgba(255,255,255,0.6); padding: 10px; border-radius: 8px;}
    
    /* 顏色狀態 */
    .status-weak { background-color: #ffebee; border-color: #ef5350; color: #c62828; } /* 現股太弱 */
    .status-neutral { background-color: #fff3e0; border-color: #ffb74d; color: #ef6c00; } /* 中性 */
    .status-strong { background-color: #e8f5e9; border-color: #66bb6a; color: #2e7d32; } /* 現股強 */

    .highlight-val { font-weight: 900; font-size: 1.1em; }
</style>
""", unsafe_allow_html=True)

st.title("⚖️ 競拍成本鑑識機")
st.caption("用得標價反推：現股要在哪裡才合理？")

# --- 3. 設定區 (輸入 CB DNA) ---
with st.expander("⚙️ 參數設定 (預設志聖三)", expanded=True):
    col_k, col_min = st.columns(2)
    conv_price = col_k.number_input("轉換價格 (K)", value=246.6, step=0.1)
    auction_min = col_min.number_input("最低得標價 (P_min)", value=121.8, step=0.1)

# --- 4. 盤中輸入區 ---
st.markdown("### 👇 開盤輸入現股價")
s_price = st.number_input("目前現股股價 (S)", value=0.0, step=0.5, help="輸入開盤價或即時價")

# --- 5. 核心運算邏輯 ---
if conv_price > 0 and auction_min > 0:
    
    # 1. 建立反推矩陣 (得標價在不同溢價下，對應的現股價格)
    # 公式: S = K * [ P_min / 100(1+p) ]
    def get_implied_s(premium_rate):
        return conv_price * (auction_min / (100 * (1 + premium_rate)))

    s_p10 = get_implied_s(0.10) # 溢價 10%
    s_p15 = get_implied_s(0.15) # 溢價 15%
    s_p20 = get_implied_s(0.20) # 溢價 20%
    s_p25 = get_implied_s(0.25) # 溢價 25%

    # 顯示反推表格 (這是你的靜態分析表)
    if s_price == 0:
        st.info("請輸入現股股價以進行鑑識")
        st.markdown("#### 📊 得標價 121.8 暗示的現股區間")
        data = {
            "市場給予溢價": ["10% (樂觀)", "15% (中性)", "20% (保守)", "25% (悲觀)"],
            "現股應有價格": [f"{s_p10:.1f}", f"{s_p15:.1f}", f"{s_p20:.1f}", f"{s_p25:.1f}"]
        }
        st.table(pd.DataFrame(data))

    # 2. 即時鑑識 (當用戶輸入股價後)
    else:
        st.markdown("---")
        
        # 計算：要維持得標價 121.8，現在市場「被迫」給出的溢價是多少？
        # 逆推溢價公式: Required_Premium = (P_min - Parity) / Parity
        current_parity = (s_price / conv_price) * 100
        required_premium = ((auction_min - current_parity) / current_parity) * 100
        
        # 判斷邏輯 (依照你的 250 / 260 / 270 區間)
        # s_p20 大約是 250.2
        # s_p10 大約是 273.0
        
        if s_price < s_p20: # 現股 < 250 (溢價需 > 20%)
            status = "🔴 現股太弱 (得標價危險)"
            style = "status-weak"
            desc = f"""
            <b>⚠️ 警報：現股撐不住競拍成本！</b><br>
            現股 {s_price} 元低於 250。<br>
            要維持得標價 {auction_min}，市場必須給出高達 <span class="highlight-val">{required_premium:.1f}%</span> 的溢價。<br>
            👉 <b>結論：</b>除非市場情緒極度亢奮，否則 121.8 難以防守，CB 容易破發或回檔。
            """
        elif s_p20 <= s_price <= s_p10: # 現股 250 ~ 273 (溢價 10~20%)
            status = "🟡 現股中性 (得標價合理)"
            style = "status-neutral"
            desc = f"""
            <b>⚖️ 正常區間。</b><br>
            現股 {s_price} 落在合理範圍。<br>
            要維持得標價 {auction_min}，需 <span class="highlight-val">{required_premium:.1f}%</span> 的溢價。<br>
            👉 <b>結論：</b>這是 CB 的舒適區，121.8 會形成有效的成本支撐帶。
            """
        else: # 現股 > 273 (溢價 < 10%)
            status = "🟢 現股強勢 (得標價穩固)"
            style = "status-strong"
            desc = f"""
            <b>💎 得標者賺翻了！</b><br>
            現股 {s_price} 已衝過 273。<br>
            得標價 {auction_min} 所需溢價僅 <span class="highlight-val">{required_premium:.1f}%</span> (甚至更低)。<br>
            👉 <b>結論：</b>得標者處於絕對獲利狀態，CB 價格將隨現股噴出，支撐極強。
            """

        # 顯示結果卡片
        st.markdown(f"""
        <div class="result-card {style}">
            <div class="card-title">{status}</div>
            <div class="card-content">{desc}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # 輔助數據
        c1, c2 = st.columns(2)
        with c1:
            st.metric("目前 Parity", f"{current_parity:.2f}")
        with c2:
            st.metric("維持得標價所需溢價", f"{required_premium:.1f}%")
            
        # 顯示對照表 (標記落點)
        st.markdown("#### 📉 競拍成本反推對照表")
        rows = []
        for rate in [0.10, 0.15, 0.20, 0.25]:
            imp_s = get_implied_s(rate)
            marker = "👈 目前位置" if abs(s_price - imp_s) < 5 else ""
            rows.append({
                "假設溢價": f"{rate*100:.0f}%",
                "反推現股應在": f"{imp_s:.1f}",
                "狀態": marker
            })
        st.table(pd.DataFrame(rows))
