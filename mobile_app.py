import streamlit as st
import pandas as pd

# --- 1. 版面設定 ---
st.set_page_config(page_title="CB 市場解碼器", page_icon="🔓", layout="centered")

# --- 2. CSS 美化 ---
st.markdown("""
<style>
    .stApp { font-family: -apple-system, sans-serif; }
    .stNumberInput input { font-size: 20px !important; }
    .stTextInput input { font-size: 20px !important; }
    
    /* 卡片通用 */
    .card { padding: 15px; border-radius: 10px; margin-bottom: 15px; text-align: center; border: 2px solid #ddd; }
    .card-title { font-size: 20px; font-weight: 900; margin-bottom: 5px; }
    .card-desc { font-size: 15px; text-align: left; margin-top: 10px; line-height: 1.6; color: #333; }
    
    /* 重點數據 */
    .highlight-box { background-color: #f8f9fa; padding: 10px; border-radius: 8px; border-left: 5px solid #007bff; margin-top: 10px; text-align: left;}
    .metric-label { font-size: 13px; color: #666; }
    .metric-val { font-size: 22px; font-weight: bold; color: #333; }
    
    /* 顏色定義 */
    .danger { background-color: #ffebee; border-color: #ef5350; color: #c62828; }
    .warning { background-color: #fff3e0; border-color: #ffb74d; color: #ef6c00; }
    .safe { background-color: #e8f5e9; border-color: #66bb6a; color: #2e7d32; }
    .neutral { background-color: #f5f5f5; border-color: #bdbdbd; color: #616161; }
</style>
""", unsafe_allow_html=True)

st.title("🔓 CB 市場潛在漲幅解碼")

# --- 3. 參數設定區 ---
with st.container():
    st.markdown("### 1️⃣ 設定參數 (DNA)")
    # 這裡只做純紀錄用
    cb_name = st.text_input("代號或名稱", placeholder="例: 志聖三 / 64633")

    c1, c2 = st.columns(2)
    # 預設值改為你提到的範例：志聖三
    conv_price = c1.number_input("1. 轉換價格 (K)", min_value=0.0, step=0.1, value=246.6)
    auction_min = c2.number_input("2. 最低得標/成本", min_value=0.0, step=0.1, value=123.8)

# --- 4. 盤中戰場 ---
st.markdown("### 2️⃣ 盤中輸入 (即時)")
c3, c4 = st.columns(2)
s_price = c3.number_input("現股股價 (S)", value=0.0, step=0.5)
cb_price = c4.number_input("CB 成交價 (P)", value=0.0, step=0.5)

# --- 5. 核心分頁 ---
tab1, tab2, tab3 = st.tabs(["🔮 隱含漲幅解碼", "⚖️ 得標共識反推", "📋 防雷 SOP"])

# ==================================================
# TAB 1: 隱含漲幅解碼 (市場押注劇本)
# ==================================================
with tab1:
    if conv_price > 0 and s_price > 0 and cb_price > 0:
        # A. 基礎運算
        parity = (s_price / conv_price) * 100
        premium = ((cb_price - parity) / parity) * 100
        
        # B. 隱含股價與潛在漲幅 (你的核心邏輯)
        # S_imp = (P / 100) * K
        implied_s = (cb_price / 100) * conv_price
        # 隱含上檔 %
        upside_pct = ((implied_s - s_price) / s_price) * 100

        st.markdown("---")
        
        # 1. 隱含劇本卡片
        st.markdown(f"""
        <div style="background-color:#e3f2fd; padding:15px; border-radius:10px; border:2px solid #2196f3; text-align:center; margin-bottom:15px;">
            <div style="font-size:18px; font-weight:bold; color:#1565c0;">🎬 市場正在押注的劇本</div>
            <div style="font-size:32px; font-weight:900; color:#0d47a1;">${implied_s:.1f}</div>
            <div style="font-size:14px; color:#555;">(隱含目標股價)</div>
            <hr style="margin:10px 0; border-top:1px dashed #90caf9;">
            <div style="text-align:left; line-height:1.5; color:#333;">
                CB 成交在 <b>{cb_price}</b> 元，代表市場願意為這個價格買單。<br>
                這暗示市場預期未來股價有機會看到 <b>{implied_s:.1f}</b>。<br>
                相比現股 {s_price}，潛在想像空間約： <span style="background-color:#ffeb3b; padding:2px 5px; border-radius:4px; font-weight:bold;">+{upside_pct:.1f}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        

        # 2. 溢價熱度解讀 (Temperature Check)
        if premium >= 20:
            status, style = "🔥 市場過熱 (積極看多)", "danger"
            interpret = "市場願意支付高額溢價，強烈押注上漲與波動。但注意：若沒漲，溢價會被殺得很慘。"
        elif 10 <= premium < 20:
            status, style = "⚖️ 溫和偏多 (正常)", "warning"
            interpret = "市場給予合理的 10~20% 溢價，對上漲保持中性偏樂觀的期待。"
        elif 5 <= premium < 10:
            status, style = "❄️ 情緒冷卻 (保守)", "safe"
            interpret = "市場對上漲想像保守，但也因此下檔有撐 (Parity保護)。"
        else:
            status, style = "💎 貼近價值 (低估)", "neutral"
            interpret = "市場完全不給時間價值，通常是極佳買點或是主力棄守。"

        st.markdown(f"""
        <div class="card {style}">
            <div class="card-title">{status}</div>
            <div style="display:flex; justify-content:center; gap:20px; margin:10px 0;">
                <div><small>Premium (溢價)</small><br><span class="big-num">{premium:+.1f}%</span></div>
                <div><small>Parity</small><br><span class="big-num">{parity:.1f}</span></div>
            </div>
            <div class="card-desc">
                <b>💡 解讀：</b>{interpret}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 3. 專業觀點 (你的金句)
        st.info("""
        📢 **觀點：** Premium 高代表市場願意為「上漲可能性」與「波動」付錢。
        但這不代表「確定」會漲；若波動下降，價格會修正。
        """)

    else:
        st.info("👈 請輸入現股與 CB 價格")

# ==================================================
# TAB 2: 得標共識反推 (Auction Reverse)
# ==================================================
with tab2:
    if conv_price > 0 and auction_min > 0:
        st.markdown("#### 🕵️‍♂️ 承銷時，市場覺得現股值多少？")
        st.caption(f"以得標價 {auction_min} 反推不同溢價下的合理現股")
        
        # 反推公式: S = K * [ P / 100(1+Premium) ]
        def get_auction_implied_s(p_rate): 
            return conv_price * (auction_min / (100 * (1 + p_rate)))
        
        # 計算各種情境
        s_p10 = get_auction_implied_s(0.10)
        s_p15 = get_auction_implied_s(0.15)
        s_p20 = get_auction_implied_s(0.20)
        s_p25 = get_auction_implied_s(0.25)
        
        # 建立表格數據
        data = [
            {"溢價假設": "10% (樂觀)", "隱含現股區間": f"{s_p10:.1f}", "解讀": "市場覺得股價應更高"},
            {"溢價假設": "15% (中性)", "隱含現股區間": f"{s_p15:.1f}", "解讀": "得標價的合理支撐區"},
            {"溢價假設": "20% (保守)", "隱含現股區間": f"{s_p20:.1f}", "解讀": "需要高溢價才撐得住"},
            {"溢價假設": "25% (悲觀)", "隱含現股區間": f"{s_p25:.1f}", "解讀": "現股若低於此，得標價危險"}
        ]
        df = pd.DataFrame(data)
        st.table(df)

        if s_price > 0:
            st.markdown("---")
            # 即時比對
            # 計算維持得標價所需的溢價
            curr_parity = (s_price / conv_price) * 100
            req_premium = ((auction_min - curr_parity) / curr_parity) * 100
            
            st.markdown(f"**📉 目前現股 {s_price} 元：**")
            
            if s_price < s_p20: # 現股低於 "溢價20%的區間"
                st.error(f"""
                🔴 **得標價壓力大！**
                現股過低，要維持 {auction_min} 的得標價，市場需給出 **{req_premium:.1f}%** 的高溢價。
                這通常難以長久，得標價容易變成套牢區。
                """)
            elif s_p20 <= s_price <= s_p15:
                st.warning(f"""
                🟡 **得標價合理支撐**
                現股落在合理區間 (15~20% 溢價帶)。
                維持得標價需 **{req_premium:.1f}%** 溢價，屬於 CB 正常運作範圍。
                """)
            else:
                st.success(f"""
                🟢 **得標者舒適區**
                現股強勢！得標者僅需 **{req_premium:.1f}%** (或更低) 的溢價即可獲利。
                {auction_min} 是極強的鐵板支撐。
                """)

# ==================================================
# TAB 3: 防雷 SOP
# ==================================================
with tab3:
    st.markdown("### 🛡️ 買前檢查清單")
    with st.expander("一、條款面", expanded=True):
        st.write("- [ ] **Put (賣回權)**：幾年賣回？價格多少？")
        st.write("- [ ] **Call (贖回權)**：有無強迫贖回條款？")
        st.write("- [ ] **轉換期間**：是否還在閉鎖期？")
    with st.expander("二、交易結構"):
        st.write("- [ ] **競拍成本**：現在價格離得標價多遠？")
        st.write("- [ ] **首日效應**：是否為掛牌前 5 日？")
        st.write("- [ ] **溢價率**：是否 > 20% (過熱)？")
    with st.expander("三、價格判讀"):
        st.write("- [ ] **Parity**：是否 > 130 (股性) 或 < 90 (債性)？")
        st.write("- [ ] **隱含波動率**：股價沒跌 CB 跌？(小心殺溢價)")
