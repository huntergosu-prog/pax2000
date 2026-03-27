import streamlit as st
import pandas as pd
import io
import re
from datetime import datetime, timedelta

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="팍스2000 통합 대시보드", layout="wide")
st.markdown("""
    <style>
    html, body, [class*="css"] { font-size: 13px !important; }
    div[data-testid="stMetricValue"] { font-size: 16px !important; }
    h1 { font-size: 20px !important; margin-bottom: 5px; }
    .krw-label { color: #ff4b4b; font-size: 12px; font-weight: bold; margin-top: -5px; margin-bottom: 5px; }
    .total-row { background-color: #f8f9fa; font-weight: bold; border-top: 2px solid #ff4b4b; padding: 15px; margin-top: 10px; border-radius: 8px; font-size: 14px; }
    .hl-parser { background-color: #f0f7ff; padding: 15px; border-radius: 10px; margin-bottom: 20px; border: 1px dashed #007bff; }
    </style>
    """, unsafe_allow_html=True)

# 2. 유틸리티 함수
def get_kst_time():
    return (datetime.utcnow() + timedelta(hours=9)).strftime("%m/%d %H:%M")

def parse_money(money_str):
    if pd.isna(money_str) or str(money_str).strip() == "" or str(money_str).lower() == "nan": return 0.0
    try:
        clean = re.sub(r'[^\d.-]', '', str(money_str))
        return float(clean) if clean else 0.0
    except: return 0.0

# 3. 데이터 세션 상태 초기화
for key in ['main_df', 'monthly_data', 'loan_df', 'summary_data']:
    if key not in st.session_state:
        if key == 'main_df': st.session_state.main_df = pd.DataFrame(columns=["날짜", "종목명", "포지션", "매수가", "매도가", "수익", "비고"])
        if key == 'monthly_data': st.session_state.monthly_data = {"2026": pd.DataFrame(0.0, index=["수익($)", "수익(₩)"], columns=[f"{i}월" for i in range(1, 13)])}
        if key == 'loan_df': st.session_state.loan_df = pd.DataFrame([{"대출처": "KB라이프", "대출금액": 50000000.0, "상환금액": 0.0, "비고": ""}, {"대출처": "하나생명", "대출금액": 90000000.0, "상환금액": 0.0, "비고": ""}, {"대출처": "마이너스", "대출금액": 100000000.0, "상환금액": 0.0, "비고": ""}])
        if key == 'summary_data': st.session_state.summary_data = {"투입": "₩40,000,000", "잔액": "₩16,818,623", "수익": "-₩21,981,377", "본전": "$14,513.95"}

# 4. 상단 대시보드
st.title("🚀 팍스2000: 130억 로드맵 통합 관리")
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    if st.button("🔄 환율 갱신"): st.cache_data.clear(); st.rerun()
    cur_ex = st.number_input("현재 환율", value=1514.50, step=0.1)

def goal_box(col, label, def_p, def_d):
    with col:
        p_val = st.text_input(f"{label} 목표($)", value=def_p, key=f"p_{label}")
        krw = parse_money(p_val) * cur_ex
        st.markdown(f"<p class='krw-label'>≈ ₩{krw:,.0f}</p>", unsafe_allow_html=True)
        st.text_input(f"{label} 날짜", value=def_d, key=f"d_{label}")

goal_box(c2, "1단계", "$50,000", "2026.03")
goal_box(c3, "2단계", "$200,000", "2026.05")
goal_box(c4, "3단계", "$2,000,000", "2026.07")
goal_box(c5, "4단계", "$10,000,000", "2026.12")

st.divider()

# 5. 탭 구성
tab1, tab2, tab3 = st.tabs(["📊 자산 통계", "📝 실시간 매매일지", "💸 대출 & 상환"])

with tab2:
    # --- [V30 핵심] 여러 줄을 엑셀 1줄로 요약하는 지능형 파서 ---
    st.markdown('<div class="hl-parser">', unsafe_allow_html=True)
    st.subheader("🔗 하이퍼리퀴드 거래 통합 (엑셀 복붙용)")
    hl_input = st.text_area("쪼개진 HL 거래 이력들을 모두 붙여넣어줘", height=150, placeholder="여러 줄을 한꺼번에 복사해서 넣으세요")
    
    if st.button("🪄 엑셀 양식 한 줄로 요약"):
        if hl_input:
            lines = hl_input.strip().split('\n')
            raw_data = []
            for line in lines:
                parts = re.split(r'\t|\s{2,}', line.strip())
                if len(parts) >= 4:
                    raw_data.append({
                        "time": parts[0].split(' ')[0],
                        "asset": parts[1].split('-')[0].split('/')[0],
                        "side": parts[2],
                        "price": parse_money(parts[3]),
                        "pnl": parse_money(parts[-1])
                    })
            
            if raw_data:
                df_raw = pd.DataFrame(raw_data)
                # 자산별로 그룹화해서 통합 계산
                for asset, group in df_raw.groupby('asset'):
                    # 날짜는 가장 첫 번째 데이터 기준
                    trade_date = group['time'].iloc[0]
                    # 총 수익 합산
                    total_pnl = group['pnl'].sum()
                    
                    # 매수/매도 단가 분리 계산
                    # Long: Open=매수, Close=매도 | Short: Open=매도, Close=매수
                    open_prices = group[group['side'].str.contains("Open|Buy")]['price']
                    close_prices = group[group['side'].str.contains("Close|Sell")]['price']
                    
                    avg_open = open_prices.mean() if not open_prices.empty else 0
                    avg_close = close_prices.mean() if not close_prices.empty else 0
                    
                    # 포지션 판단
                    is_long = any("Long" in s or "Buy" in s for s in group['side'])
                    pos_str = "Long" if is_long else "Short"
                    
                    # 엑셀 7칸 양식: [날짜] [종목명] [포지션] [매수가] [매도가] [수익] [비고]
                    if is_long:
                        buy_p = f"{avg_open:.2f}" if avg_open > 0 else ""
                        sell_p = f"{avg_close:.2f}" if avg_close > 0 else ""
                    else: # Short
                        buy_p = f"{avg_close:.2f}" if avg_close > 0 else ""
                        sell_p = f"{avg_open:.2f}" if avg_open > 0 else ""
                    
                    excel_line = f"{trade_date}\t{asset}\t{pos_str}\t{buy_p}\t{sell_p}\t{total_pnl:.2f}\tHL 통합정리"
                    st.code(excel_line, language="text")
                st.caption("▲ 위 박스 내용을 복사해서 엑셀 '날짜' 칸부터 붙여넣으면 끝!")
            else:
                st.error("데이터를 분석할 수 없어. 하이퍼리퀴드 Fills 내용을 그대로 긁어와줘!")
    st.markdown('</div>', unsafe_allow_html=True)

    # 매매일지 본문 로직 유지
    st.session_state.main_df = st.data_editor(st.session_state.main_df, num_rows="dynamic", use_container_width=True, key="main_editor_v30")

with tab3:
    st.subheader("💸 대출 & 상환 관리")
    loan_editor_df = st.data_editor(st.session_state.loan_df, num_rows="dynamic", use_container_width=True,
                                    column_config={"대출금액": st.column_config.NumberColumn("대출금액(₩)", format="%,d"),
                                                   "상환금액": st.column_config.NumberColumn("상환금액(₩)", format="%,d")},
                                    key="loan_editor_v30")
    if not loan_editor_df.equals(st.session_state.loan_df):
        st.session_state.loan_df = loan_editor_df
        st.rerun()
    tl = st.session_state.loan_df['대출금액'].apply(parse_money).sum()
    tr = st.session_state.loan_df['상환금액'].apply(parse_money).sum()
    st.markdown(f'<div class="total-row">💰 총 대출: ₩{tl:,.0f} | ✅ 총 상환: ₩{tr:,.0f} | 🚨 잔액: ₩{tl-tr:,.0f}</div>', unsafe_allow_html=True)
