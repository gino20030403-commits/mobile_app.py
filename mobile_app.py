import streamlit as st
import pandas as pd

# --- 1. 版面設定 ---
st.set_page_config(page_title="CB 全能操盤手", page_icon="📈", layout="centered")

# --- 2. CSS 美化 ---
st.markdown("""
<style>
    .stApp { font-family: -apple-system, sans-serif; }
    .stNumberInput input { font-size: 20px !important; }
    
    /* 訊號卡片通用樣式 */
    .card {
        padding: 15px; border-radius: 10px; margin-bottom: 15px;
        text-align: center; border: 2px solid #ddd;
    }
    .card-title { font-size: 20px; font-weight: 900; margin-bottom: 5px; }
    .card-desc { font-size: 15px; text-align: left; margin-top: 10px; line-height: 1.5; }
    
    /* 顏色定義 */
    .danger { background-color: #ffebee; border-color: #ef5350; color: #c62828; }
    .warning { background-color: #fff3e0; border-color: #ffb74d; color: #ef6c00; }
    .safe { background-color: #e8f5e9; border-color: #66bb6a; color: #2e7d32; }
    .neutral { background-color: #f5f5f5; border-color: #bdbdbd; color: #616161; }

    /* 數據強調 */
    .big-num { font-size: 24px; font-weight: bold; }
    .highlight { font-weight: bold; background-color: rgba(255,255,255,0.5); padding: 2px 5px; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

st.title("📈 CB 全能操盤手")

# --- 3. 全局參數 (DNA) ---
with st.expander("⚙️ 設定參數 (預設志聖三)", expanded=True):
    c1, c2 = st.columns(2)
    conv_price = c1.number_input("轉換價格 (K)", value=246.6, step=0.1)
    auction_min = c2.number_input("最低得標價 (P_min)", value=121.8, step=0.1)

# --- 4. 盤中輸入 ---
st.markdown("### ⚡ 盤中輸入區")
c3, c4 = st.columns(2)
s_price = c3.number_input("現股股價 (S)", value=0.0, step=0.5)
cb_price = c4.number_input("CB 成交價 (P)", value=0.0, step=0.5)

# --- 5. 分頁功能 ---
tab1, tab2, tab3 = st.tabs(["⚔️ 盤中戰情室", "⚖️ 競拍成本鑑識", "📋 防雷檢查表"])

# ==================================================
# TAB 1: 盤中戰情室 (溢價紅綠燈)
# ==================================================
with tab1:
    if conv_price > 0 and s_price > 0 and cb_price > 0:
        parity = (s_price / conv_price) * 100
        premium = ((cb_price - parity) / parity) * 100
        
        st.markdown("---")
        
        # 訊號判讀
        if premium >= 20:
            status = "🔴 追高風險 (貴)"
            style = "danger"
            advice = "溢價 > 20%：危險區！CB 價格比理論值貴太多，常見於籌碼過熱。除非現股噴出，否則 CB 回檔速度會很快。"
        elif 10 <= premium < 20:
            status = "🟡 中性觀察 (穩)"
            style = "warning"
            advice = "溢價 10~20%：合理區間。大多頭市場常見範圍。若現股強勢，CB 會跟漲；若盤整，溢價會收斂。"
        elif 5 <= premium < 10:
            status = "🟢 相對便宜 (安)"
            style = "safe"
            advice = "溢價 5~10%：高勝率區。溢價低，下檔有 Parity 保護。若現股基本面無虞，這是長線投資甜蜜點。"
        elif premium < 5:
            status = "❄️ 貼近平價 (殺)"
            style = "neutral"
            advice = "溢價 < 5%：警示或機會。市場不給時間價值。1. 若現股跌：主力棄守。 2. 若現股漲：CB 被低估 (極佳買點)。"
        else:
            status = "⚪ 計算中"
            style = "neutral"
            advice = "..."

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
        st.info("👈 請輸入現股與 CB 價格以啟動戰情室")

# ==================================================
# TAB 2: 競拍成本鑑識 (反推邏輯)
# ==================================================
with tab2:
    if conv_price > 0 and auction_min > 0:
        st.markdown("#### 🕵️‍♂️ 用得標價反推：現股要在哪裡才合理？")
        
        # 反推矩陣函數
        def get_implied_s(p_rate): return conv_price * (auction_min / (100 * (1 + p_rate)))
        
        s_p10 = get_implied_s(0.10) # 273.0
        s_p20 = get_implied_s(0.20) # 250.2
        
        if s_price > 0:
            # 計算維持得標價所需的溢價
            curr_parity = (s_price / conv_price) * 100
            req_premium = ((auction_min - curr_parity) / curr_parity) * 100
            
            # 判斷邏輯
            if s_price < s_p20:
                status = "🔴 現股太弱 (得標價危險)"
                style = "danger"
                desc = f"現股低於 {s_p20:.1f}。要維持得標價 {auction_min}，市場需給出 <span class='highlight'>{req_premium:.1f}%</span> 的高溢價。除非情緒極度亢奮，否則成本線難守。"
            elif s_p20 <= s_price <= s_p10:
                status = "🟡 現股中性 (得標價合理)"
                style = "warning"
                desc = f"現股落在合理區間。維持得標價需 <span class='highlight'>{req_premium:.1f}%</span> 溢價。這是 CB 的舒適區，{auction_min} 具參考支撐。"
            else:
                status = "🟢 現股強勢 (得標價穩固)"
                style = "safe"
                desc = f"現股已衝過 {s_p10:.1f}。得標者處於絕對獲利狀態，CB 價格將隨現股噴出，支撐極強。"
            
            st.markdown(f"""
            <div class="card {style}">
                <div class="card-title">{status}</div>
                <div class="card-desc">{desc}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # 靜態對照表
        st.caption("📉 競拍成本反推對照表")
        data = []
        for rate in [0.10, 0.15, 0.20, 0.25]:
            imp_s = get_implied_s(rate)
            marker = "👈 目前" if abs(s_price - imp_s) < 5 and s_price > 0 else ""
            data.append({"假設溢價": f"{rate*100:.0f}%", "反推現股應在": f"{imp_s:.1f}", "狀態": marker})
        st.table(pd.DataFrame(data))

# ==================================================
# TAB 3: 防雷檢查表 (你的核心 SOP)
# ==================================================
with tab3:
    st.markdown("### 🛡️ 買前必看：防雷 SOP")
    
    with st.expander("一、條款面：決定上下限", expanded=True):
        st.markdown("""
        * **1. 票息/到期還本**：
            * 若用 120 買且票息 0%，等於先吞負利息。
            * ✅ **看：** 到期還本率、利息支付方式。
        * **2. 賣回權 (Put)**：
            * 下檔保護核心。越早 Put、價格越高 = 越安全。
            * ⚠️ **險：** 無 Put 或 Put 很晚，下檔難看。
        * **3. 贖回權 (Call)**：
            * 公司強制贖回 (如股價 > 轉換價130%)。
            * ⚠️ **險：** 上檔路徑會被截斷 (強迫中獎/拿回面額)。
        * **4. 重設 (下修條款)**：
            * 有重設對投資人友善 (股價跌時轉換價下修)。
        * **5. 轉換期間**：
            * 注意閉鎖期 (通常發行後 3 個月不可轉)。
        * **6. 稀釋與發行量**：
            * 量大 = 潛在賣壓大，現股上方壓力大。
        """)

    with st.expander("二、交易結構：初期踩坑點"):
        st.markdown("""
        * **7. 承銷方式 (競拍/詢圈)**：
            * 初期價格由「得標者」主導，非公平價值。
            * ✅ **看：** 得標均價、承銷商自留比例。
        * **8. 流動性**：
            * CB 常見量不連續、價差大。
            * ✅ **看：** 日成交量、掛單是否空虛。
        * **9. 隱形成本**：
            * 短線交易需注意手續費與稅費磨損。
        """)

    with st.expander("三、價格判讀：買債或選擇權？"):
        st.markdown("""
        * **10. Parity vs Premium**：
            * Parity = (現股/轉換價)*100。
            * ⚠️ 波動率降時，溢價會跌得比股價快。
        * **11. 股性 vs 債性**：
            * Parity > 130：像股票 (Delta高)。
            * Parity < 90：像債券 (抗跌但漲不動)。
        * **12. 隱含波動率 (IV)**：
            * 股價沒跌 CB 卻跌？通常是 IV 降導致溢價縮水。
        """)

    with st.expander("四、實務陷阱 (新手必讀)", expanded=True):
        st.markdown("""
        * ❌ **13. 誤把「得標價」當鐵板支撐**：那只是別人的成本，非價值線。
        * ❌ **14. 忽略信用風險**：無擔保 CB 要看公司體質 (負債比/現金流)。
        * ❌ **15. 忽略「強制贖回」**：以為能跟股一路飛，結果被 Call 截斷。
        * ❌ **16. 把「掛牌首日價」當合理價**：首日是籌碼戰，價格常失真。
        * ✅ **建議：** 等 3-5 天量縮止穩再評估。
        """)
