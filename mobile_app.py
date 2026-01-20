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
with st.expander("⚙️ 步驟一：輸入債券參數 (DNA)", expanded=True):
    stock_name = st.text_input("債券名稱 (選填)", placeholder="例如：世紀鋼一")
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        conv_price = st.number_input("1. 轉換價格 (K)", min_value=0.0, value=0.0, step=0.1, help="查閱公開說明書或 App")
    with
