import streamlit as st
import pandas as pd
import io
import re
from datetime import datetime

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="팍스2000 통합 대시보드", layout="wide")
st.markdown("""
    <style>
    html, body, [class*="css"] { font-size: 13px !important; }
    div[data-testid="stMetricValue"] { font-size: 16px !important; }
    h1 { font-size: 20px !important; margin-bottom: 5px; }
    .krw-label { color: #ff4b4b; font-size: 12px; font-weight: bold; margin-top: -5px; margin-bottom: 5px; }
    .total-row { background-color: #f0f2f6; font-weight: bold; border-top: 2px solid #ddd; padding: 15px; margin-top: 10px; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# 2. 유틸리티 함수
try:
    import yfinance as yf
    YF_AVAILABLE = True
except ImportError:
    YF_AVAILABLE = False

@st.cache_data(ttl=14400)
def get_exchange_rate():
    if not YF_AVAILABLE: return 1442.50, "기본값"
    try:
        ticker = yf.Ticker("USDKRW=X")
        data = ticker.history(period="1d")
        return round(data['Close'].iloc[-1], 2), datetime.now().strftime("%m/%d %H:%M")
    except: return 1442.50, "연결에러"

def parse_money(money_str):
    if pd.isna(money_str) or str(money_str).strip() == "": return 0.0
    try:
        clean = re.sub(r'[^\d.-]', '', str(money_str))
        return float(clean) if clean else 0.0
    except: return 0.0

# 3. 데이터 세션 상태 초기화
if 'main_df' not in st.session_state: 
    st.session_state.main_df = pd.DataFrame(columns=["날짜", "종목명", "포지션", "매수가", "매도가", "수량", "수수료", "비고"])
if 'monthly_df' not in st.session_state: 
    st.session_state.monthly_df = pd.DataFrame(index=["수익($)", "수익(₩)"])
if 'loan_df' not in st.session_state: 
    st.session_state.loan_df = pd.DataFrame([
        {"대출처": "KB라이프", "대출금액": 50000000, "상환금액": 0, "비고": ""},
        {"대출처": "하나생명", "대출금액": 90000000, "상환금액": 0, "비고": ""},
        {"대출처": "마이너스", "대출금액": 100000000, "상환금액": 0, "비고": ""}
    ])
if 'summary_data' not in st.session_state: 
    st.session_state.summary_data = {"투입": "₩40,000,000", "잔액": "₩18,012,969", "수익": "-₩21,987,031", "본전": "$14,410.42"}

# 4. 상단 대시보드
st.title("🚀 팍스2000: 130억 로드맵 관리 시스템")
ex_rate, last_up = get_exchange_rate()

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    if st.button("🔄 환율 갱신"): st.cache_data.clear(); st.rerun()
    cur_ex = st.number_input("현재 환율", value=ex_rate, step=0.1)

def goal_box(col, label, def_p, def_d):
    with col:
        p_val = st.text_input(f"{label} 목표($)", value=def_p)
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
    st.subheader("📉 선물 매매 기록")
    up_file = st.file_uploader("엑셀(CSV) 업로드", type=["csv"], label_visibility="collapsed")
    
    if up_file:
        try:
            raw = pd.read_csv(io.StringIO(up_file.getvalue().decode('utf-8-sig')), header=None)
            
            # 안전 파싱 (Summary)
            if raw.shape[0] > 2:
                st.session_state.summary_data = {
                    "잔액": str(raw.iloc[2, 8]) if raw.shape[1] > 8 else "₩0",
                    "본전": str(raw.iloc[2, 10]) if raw.shape[1] > 10 else "$0",
                    "수익": str(raw.iloc[2, 11]) if raw.shape[1] > 11 else "₩0",
                    "투입": str(raw.iloc[2, 12]) if raw.shape[1] > 12 else "₩0"
                }
            
            # 월별 수익 파싱
            if raw.shape[0] > 6:
                m_header = raw.iloc[4, 8:20].tolist()
                m_usd = raw.iloc[5, 8:20].tolist()
                m_krw = raw.iloc[6, 8:20].tolist()
                st.session_state.monthly_df = pd.DataFrame([m_usd, m_krw], columns=m_header, index=["수익($)", "수익(₩)"])
            
            # 매매일지 파싱
            for i in range(len(raw)):
                if "종목명" in str(raw.iloc[i].values):
                    df = raw.iloc[i:].copy()
                    df.columns = df.iloc[0]
                    df = df[1:].reset_index(drop=True)
                    cols_to_drop = [c for c in df.columns if any(x in str(c).lower() for x in ['no', '비고2', 'unnamed'])]
                    st.session_state.main_df = df.drop(columns=cols_to_drop, errors='ignore').dropna(how='all')
                    break
            st.success("데이터를 성공적으로 불러왔어!")
        except Exception as e: st.error(f"파일 로드 에러: {e}")

    # 일지 에디터 및 다운로드
    st.session_state.main_df = st.data_editor(st.session_state.main_df, num_rows="dynamic", use_container_width=True)
    c_down1, c_save1 = st.columns([1, 1])
    with c_save1:
        if st.button("💾 매매일지 저장"): st.success("임시 저장 완료!")
    with c_down1:
        csv_log = st.session_state.main_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 매매일지 다운로드", csv_log, "trading_log.csv", "text/csv")

with tab1:
    s = st.session_state.summary_data
    ca, cb, cc, cd = st.columns(4)
    def m(col, l, usd_v, krw_s):
        with col:
            st.caption(l); st.subheader(f"${usd_v:,.2f}"); st.markdown(f"<p class='krw-label'>{krw_s}</p>", unsafe_allow_html=True)
    
    m(ca, "총 투입금", parse_money(s['투입'])/cur_ex, s['투입'])
    m(cb, "현재 잔액", parse_money(s['잔액'])/cur_ex, s['잔액'])
    m(cc, "누적 수익", parse_money(s['수익'])/cur_ex, s['수익'])
    m(cd, "본전 수익목표", parse_money(s['본전']), f"₩{parse_money(s['본전'])*cur_ex:,.0f}")
    
    st.write("---")
    st.subheader("🗓️ 월별 수익 현황")
    if not st.session_state.monthly_df.empty: st.table(st.session_state.monthly_df)

with tab3:
    st.subheader("💳 대출 내역 및 실시간 상환 관리")
    st.info("💡 표 아래 (+) 버튼으로 항목을 추가해 봐! 합계는 실시간으로 계산돼.")
    
    # 대출 에디터
    edited_loan = st.data_editor(st.session_state.loan_df, num_rows="dynamic", use_container_width=True)
    st.session_state.loan_df = edited_loan

    # 실시간 합계 자동 계산
    total_l = edited_loan['대출금액'].apply(parse_money).sum()
    total_r = edited_loan['상환금액'].apply(parse_money).sum()
    rem = total_l - total_r

    st.markdown(f"""
    <div class="total-row">
        <div style="display: flex; justify-content: space-between;">
            <span>💰 총 대출액: ₩{total_l:,.0f}</span>
            <span style="color: blue;">✅ 총 상환액: ₩{total_r:,.0f}</span>
            <span style="color: red;">🚨 남은 잔액: ₩{rem:,.0f}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    c_down2, c_save2 = st.columns([1, 1])
    with c_save2:
        if st.button("💾 금융 데이터 저장"): st.success("저장 완료!")
    with c_down2:
        csv_loan = edited_loan.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 대출내역 다운로드", csv_loan, "loan_history.csv", "text/csv")
