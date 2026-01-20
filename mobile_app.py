import streamlit as st
import pandas as pd

# --- 1. 版面設定 ---
st.set_page_config(page_title="萬用戰情室", page_icon="🛡️", layout="centered")

# --- 2. CSS 美化 ---
st.markdown("""
<style>
    .stApp { font-family: -apple-system, sans-serif; }
    .stNumberInput input { font-size: 20px !important; }
    
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

    .big-num { font-size: 24px; font-weight: bold; }
    .small-label { font-size: 12px; color: #666; }
</style>
""", unsafe_allow_html=True)

st.title("🛡️ CB 萬用戰情室")
st.caption("v14.2 (防縮排錯誤版)")

# --- 3. 步驟一：輸入參數 (移除 with 寫法，改用直列式) ---
st.markdown("### ⚙️ 步驟一：輸入債券參數 (DNA)")
stock_name = st.text_input("債券名稱 (選填)", placeholder="例如：世紀鋼一")

c1, c2 = st.columns(2)
# 使用物件導向寫法，避免縮排錯誤
conv_price = c1.number_input("1. 轉換價格 (K)", min_value=0.0, value=0.0, step=0.1)
auction_cost = c2.number_input("2. 大戶成本/得標價", min_value=0.0, value=100.0, step=0.1)

# --- 4. 步驟二：盤中輸入 ---
st.markdown("### ⚔️ 步驟二：盤中輸入即時價格")
c3, c4 = st.columns(2)
s_price = c3.number_input("現股股價 (S)", min_value=0.0, value=0.0, step=0.5)
cb_price = c4.number_input("CB 成交價 (P)", min_value=0.0, value=0.0, step=0.5)

# --- 5. 核心運算 ---
if conv_price > 0 and s_price > 0 and cb_price > 0:
    # 基礎計算
    parity = (s_price / conv_price) * 100
    premium = ((cb_price - parity) / parity) * 100
    breakeven_s = (auction_cost / 100) * conv_price 

    st.markdown("---")

    # === A. 訊號判讀 ===
    if premium >= 20:
        status = "🔴 追高風險 (貴)"
        style = "danger"
        advice = "溢價 > 20%：危險區！CB 價格比理論值貴太多，常見於籌碼過熱。除非現股噴出，否則 CB 回檔速度會很快。建議觀望。"
    elif 10 <= premium < 20:
        status = "🟡 中性觀察 (穩)"
        style = "warning"
        advice = "溢價 10~20%：合理區間。這是大多頭市場常見的溢價範圍。若現股強勢，CB 會跟漲；若現股盤整，溢價會慢慢收斂。"
    elif 5 <= premium < 10:
        status = "🟢 相對便宜 (安)"
        style = "safe"
        advice = "溢價 5~10%：高勝率區。溢價低，下檔有 Parity 保護。若現股基本面無虞，這裡是長線投資或套利的甜蜜點。"
    elif premium < 5:
        status = "❄️ 貼近平價 (殺)"
        style = "neutral"
        advice = "溢價 < 5%：警示或機會。市場完全不給時間價值。1. 若現股在跌：代表主力棄守。 2. 若現股在漲：代表 CB 被低估 (極佳買點)。"
    else:
        status = "⚪ 計算中"
        style = "neutral"
        advice = "..."

    # 顯示卡片
    st.markdown(f"""
    <div class="signal-card {style}">
        <div class="signal-title">{status}</div>
        <div style="display:flex; justify-content:center; gap:20px; margin:10px 0;">
            <div>
                <div class="small-label">目前溢價率</div>
                <div class="big-num">{premium:+.1f}%</div>
            </div>
            <div>
                <div class="small-label">Parity (理論價)</div>
                <div class="big-num">{parity:.1f}</div>
            </div>
        </div>
        <div class="signal-desc">{advice}</div>
    </div>
    """, unsafe_allow_html=True)

    # === B. 大戶成本雷達 ===
    profit_status = '✅ 獲利中' if s_price > breakeven_s else '❌ 虧損/成本保衛戰'
    st.info(f"大戶持有成本 {auction_cost} 元 👉 回本股價需 {breakeven_s:.1f} 元\n\n(目前大戶處於：{profit_status})")
    
    # === C. 秒判對照表 ===
    st.markdown("#### 📊 即時秒判對照表")
    data = []
    base_s = int(s_price / 5) * 5 
    if base_s == 0: base_s = 100
    
    stock_range = [base_s-10, base_s-5, base_s, base_s+5, base_s+10]
    
    for s in stock_range:
        p = (s / conv_price) * 100
        marker = "👈" if abs(s - s_price) < 2.5 else ""
        data.append({
            "現股": f"{s} {marker}",
            "Parity": f"{p:.1f}",
            "+5%(俗)": f"{p*1.05:.1f}",
            "+10%(普)": f"{p*1.10:.1f}",
            "+15%(貴)": f"{p*1.15:.1f}",
        })
    
    st.table(pd.DataFrame(data))

else:
    st.info("👈 請輸入：1.轉換價、2.大戶成本、3.現股價、4.CB價")
