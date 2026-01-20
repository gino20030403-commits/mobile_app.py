import streamlit as st
import pandas as pd

# --- 1. 版面設定 ---
st.set_page_config(page_title="萬用戰情室", page_icon="🛡️", layout="centered")

# --- 2. CSS 美化 (戰情室風格) ---
st.markdown("""
<style>
    .stApp { font-family: -apple-system, sans-serif; }
    .stNumberInput input { font-size: 20px !important; }
    .stTextInput input { font-size: 20px !important; }
    
    /* 訊號燈卡片 */
    .signal-card {
        padding: 15px; border-radius: 10px; margin-bottom: 15px;
        text-align: center; border-width: 2px; border-style: solid;
    }
    .signal-title { font-size: 22px; font-weight: 900; margin-bottom: 5px; }
    .signal-desc { font-size: 15px; opacity: 0.9; text-align: left; margin-top: 10px; }
    
    /* 顏色定義 */
    .danger { background-color: #ffebee; border-color: #ef5350; color: #c62828; }
    .warning { background-color: #fff3e0; border-color: #ffb74d; color: #ef6c00; }
    .safe { background-color: #e8f5e9; border-color: #66bb6a; color: #2e7d32; }
    .neutral { background-color: #f5f5f5; border-color: #bdbdbd; color: #616161; }

    /* 數據強調 */
    .big-num { font-size: 24px; font-weight: bold; }
    .small-label { font-size: 12px; color: #666; }
</style>
""", unsafe_allow_html=True)

st.title("🛡️ CB 萬用戰情室")
st.caption("通用版：適用新債掛牌 / 舊債套利")

# --- 3. 戰前準備 (設定參數) ---
# 這裡讓使用者輸入該檔 CB 的「DNA」
with st.expander("⚙️ 步驟一：輸入債券參數 (DNA)", expanded=True):
    stock_name = st.text_input("債券名稱 (選填)", placeholder="例如：世紀鋼一")
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        conv_price = st.number_input("1. 轉換價格 (K)", min_value=0.0, value=0.0, step=0.1, help="查閱公開說明書或 App")
    with col_p2:
        # 如果是舊債，可以輸入 100；如果是新掛牌，輸入競拍最低得標價
        auction_cost = st.number_input("2. 大戶成本/得標價", min_value=0.0, value=100.0, step=0.1, help="新債請填競拍最低價，舊債可填 100 或市場平均成本")

# --- 4. 戰場輸入區 (盤中動態) ---
st.markdown("### ⚔️ 步驟二：盤中輸入即時價格")
col1, col2 = st.columns(2)
with col1:
    s_price = st.number_input("現股股價 (S)", min_value=0.0, value=0.0, step=0.5)
with col2:
    cb_price = st.number_input("CB 成交價 (P)", min_value=0.0, value=0.0, step=0.5)

# --- 5. 核心運算 ---
if conv_price > 0 and s_price > 0 and cb_price > 0:
    # 基礎計算
    parity = (s_price / conv_price) * 100
    premium = ((cb_price - parity) / parity) * 100
    implied_s = (cb_price / 100) * conv_price
    
    # 大戶回本股價 (Break-even Stock Price)
    # 邏輯：大戶成本價 / 100 * 轉換價
    breakeven_s = (auction_cost / 100) * conv_price 

    st.markdown("---")

    # === A. 訊號判讀 (通用邏輯) ===
    # 這裡沿用你的「追高風險教材」邏輯
    if premium >= 20:
        status = "🔴 追高風險 (貴)"
        style = "danger"
        advice = f"""
        <b>🔥 溢價 > 20%：危險區！</b><br>
        CB 價格比理論值貴太多。常見於籌碼過熱。<br>
        除非現股噴出，否則 CB 回檔速度會很快。建議觀望。
        """
    elif 10 <= premium < 20:
        status = "🟡 中性觀察 (穩)"
        style = "warning"
        advice = f"""
        <b>⚖️ 溢價 10~20%：合理區間。</b><br>
        這是大多頭市場常見的溢價範圍。<br>
        若現股強勢，CB 會跟漲；若現股盤整，溢價會慢慢收斂。
        """
    elif 5 <= premium < 10:
        status = "🟢 相對便宜 (安)"
        style = "safe"
        advice = f"""
        <b>💎 溢價 5~10%：高勝率區。</b><br>
        溢價低，下檔有 Parity 保護。<br>
        若現股基本面無虞，這裡是長線投資或套利的甜蜜點。
        """
    elif premium < 5:
        status = "❄️ 貼近平價
