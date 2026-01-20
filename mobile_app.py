import streamlit as st
import pandas as pd

# --- 1. 版面設定 ---
st.set_page_config(page_title="現股估值反推", page_icon="🔭", layout="centered")

# --- 2. CSS 美化 ---
st.markdown("""
<style>
    .stApp { font-family: -apple-system, sans-serif; }
    .stNumberInput input { font-size: 20px !important; }
    
    /* 估值卡片 */
    .val-card {
        padding: 20px; border-radius: 12px; margin-bottom: 20px;
        text-align: center; border: 2px solid #ddd;
    }
    .val-title { font-size: 18px; color: #555; margin-bottom: 5px; }
    .val-price { font-size: 36px; font-weight: 900; color: #333; }
    .val-diff { font-size: 16px; font-weight: bold; margin-top: 5px; }
    
    /* 狀態標籤 */
    .tag-cheap { background-color: #e8f5e9; color: #2e7d32; padding: 5px 10px; border-radius: 5px; font-weight:bold;}
    .tag-fair { background-color: #fff3e0; color: #ef6c00; padding: 5px 10px; border-radius: 5px; font-weight:bold;}
    .tag-expensive { background-color: #ffebee; color: #c62828; padding: 5px 10px; border-radius: 5px; font-weight:bold;}

    .highlight-box { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 5px solid #2196f3; }
</style>
""", unsafe_allow_html=True)

st.title("🔭 現股估值反推機")
st.caption("用 CB 價格看穿現股是貴還是便宜")

# --- 3. 輸入區 ---
with st.container():
    st.markdown("### 1️⃣ 輸入關鍵參數")
    stock_name = st.text_input("股票名稱 (選填)", placeholder="例如：萬潤")
    
    c1, c2 = st.columns(2)
    conv_price = c1.number_input("轉換價格 (K)", min_value=0.0, value=0.0, step=0.1, help="DNA")
    cb_price = c2.number_input("CB 目前價格 (P)", min_value=0.0, value=0.0, step=0.5, help="大戶出的價")

    st.markdown("### 2️⃣ 輸入目前現股價")
    s_price = st.number_input("現股股價 (S)", min_value=0.0, value=0.0, step=0.5)

# --- 4. 反推邏輯運算 ---
if conv_price > 0 and cb_price > 0 and s_price > 0:
    
    # A. 核心公式
    # 1. 隱含目標價 (Implied Price): CB 價格完全轉換後的股價 (Premium = 0%)
    implied_s = (cb_price / 100) * conv_price
    
    # 2. 合理支撐價 (Fair Price): 假設 CB 應有 10% 正常溢價，回推股價應在哪
    # 公式推導: CB = Parity * 1.10 => CB = (S/K)*100 * 1.10 => S = (CB/110)*K
    fair_s = (cb_price / 110) * conv_price

    # 3. 溢價率 (用來輔助判斷)
    parity = (s_price / conv_price) * 100
    premium = ((cb_price - parity) / parity) * 100

    st.markdown("---")

    # B. 估值判斷 (現股到底是貴還是便宜？)
    # 邏輯：
    # 如果 現股 < 合理支撐價 (fair_s) => 股價落後 CB，便宜 (Cheap)
    # 如果 現股 > 隱含目標價 (implied_s) => 股價超漲，CB 變折價，現股太貴 (Expensive)
    
    if s_price < fair_s:
        valuation = "🟢 現股被低估 (便宜)"
        val_color = "#e8f5e9"
        text_color = "#2e7d32"
        gap = fair_s - s_price
        desc = f"CB 市場看好股價應值 **{fair_s:.1f}** 元以上。<br>現股尚有 **+{gap:.1f} 元** 的落後補漲空間。"
    elif fair_s <= s_price <= implied_s:
        valuation = "🟡 現股估值合理 (中性)"
        val_color = "#fff3e0"
        text_color = "#ef6c00"
        desc = f"現股價格符合 CB 的定價邏輯 (溢價 0~10% 之間)。<br>股價與債價同步，無明顯套利空間。"
    else:
        valuation = "🔴 現股被高估 (貴/過熱)"
        val_color = "#ffebee"
        text_color = "#c62828"
        gap = s_price - implied_s
        desc = f"現股已漲過頭！比 CB 隱含的極限價格還貴 **{gap:.1f} 元**。<br>CB 處於折價狀態，主力可能在拉高出貨或準備套利。"

    # C. 顯示大卡片
    st.markdown(f"""
    <div class="val-card" style="background-color: {val_color}; border-color: {text_color};">
        <div class="val-title">🔎 診斷結果</div>
        <div class="val-price" style="color: {text_color};">{valuation}</div>
        <div style="margin-top:15px; font-size:15px; text-align:left; padding:0 10px;">
            {desc}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # D. 數據細節
    c_res1, c_res2 = st.columns(2)
    with c_res1:
        st.markdown(f"**📉 隱含目標價**")
        st.markdown(f"<h2 style='margin:0; color:#333'>{implied_s:.1f}</h2>", unsafe_allow_html=True)
        st.caption("若 CB 溢價收斂至 0% 股價位置")
    with c_res2:
        st.markdown(f"**🛡️ 合理支撐價**")
        st.markdown(f"<h2 style='margin:0; color:#555'>{fair_s:.1f}</h2>", unsafe_allow_html=True)
        st.caption("假設 CB 帶有 10% 正常溢價")

    # E. 價差視覺化 (進度條概念)
    st.markdown("#### 📏 價格位階量尺")
    current_pos = (s_price - fair_s) / (implied_s - fair_s) * 100 if implied_s != fair_s else 50
    
    # 簡單的文字圖表
    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; font-size:12px; color:#888; margin-bottom:5px;">
        <span>便宜 (落後)</span>
        <span>合理</span>
        <span>昂貴 (超漲)</span>
    </div>
    <div style="height:10px; background:linear-gradient(90deg, #4caf50 0%, #ff9800 50%, #f44336 100%); border-radius:5px; position:relative;">
        <div style="position:absolute; left: {min(max(current_pos, 0), 100)}%; top:-5px; width:4px; height:20px; background:#333; border:1px solid #fff;"></div>
    </div>
    <div style="text-align:center; margin-top:5px; font-weight:bold; color:#333;">
        ▲ 目前現股 {s_price}
    </div>
    """, unsafe_allow_html=True)
    
    # F. 額外資訊：溢價率
    with st.expander("ℹ️ 查看詳細運算數據"):
        st.write(f"Parity (轉換價值): **{parity:.2f}**")
        st.write(f"Premium (溢價率): **{premium:.2f}%**")
        if premium > 20:
            st.warning("⚠️ 溢價率 > 20%，表示 CB 價格本身可能也虛胖，反推的目標價可能過於樂觀。")

else:
    st.info("👈 請輸入左側 3 個參數，幫你算出「現股」到底貴不貴。")
    st.markdown("""
    **💡 邏輯說明：**
    * 我們假設 CB 是聰明錢 (Smart Money)。
    * 如果 CB 價格很高，隱含股價算出來是 200，但現股只有 180 ➡️ **現股便宜 (有 20 元肉)**。
    * 如果 CB 價格不動，隱含股價是 180，但現股已經 200 ➡️ **現股太貴 (小心回檔)**。
    """)
