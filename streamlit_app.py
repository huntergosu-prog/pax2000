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
    .total-row { background-color: #f0f2f6; font-weight: bold; border-top: 2px solid #ddd; padding: 10px; margin-top: 5px; border-radius: 5px; }
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
    if pd.isna(money_str) or money_str == "": return 0.0
    try:
        clean = re.sub(r'[^\d.-]', '', str(money_str))
        return float(clean) if clean else 0.0
    except: return 0.0

# 3. 데이터 세션 초기화
if 'main_df' not in st.session_state: 
    st.session_state.main_df = pd.DataFrame(columns=["날짜", "종목명", "포지션", "매수가", "매도가", "수익", "비고"])
if 'loan_df' not in st.session_state: 
    # 합계를 제외한 순수 대출 내역만 관리
    st.session_state.loan_df = pd.DataFrame([
        {"대출처": "KB라이프", "대출금액": 50000000, "상환금액": 0, "비고": ""},
        {"대출처": "하나생명", "대출금액": 90000000, "상환금액": 0, "비고": ""},
        {"대출처": "마이너스", "대출금액": 100000000, "상환금액": 0, "비고": ""}
    ])
if 'monthly_df' not in st.session_state: st.session_state.monthly_df = pd.DataFrame()
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
    # 파일 업로드 로직 (기존과 동일하게 유지하되 파싱만 보강)
    up_file = st.file_uploader("파일 로드", type=["csv"], label_visibility="collapsed")
    if up_file:
        try:
            raw = pd.read_csv(io.StringIO(up_file.getvalue().decode('utf-8-sig')), header=None)
            st.session_state.summary_data = {"잔액": str(raw.iloc[2, 8]), "본전": str(raw.iloc[2, 10]), "수익": str(raw.iloc[2, 11]), "투입": str(raw.iloc[2, 12])}
            st.success("데이터 복구 성공!")
        except: st.error("파일 형식을 확인해 줘!")
    
    st.session_state.main_df = st.data_editor(st.session_state.main_df, num_rows="dynamic", use_container_width=True)
    if st.button("💾 매매일지 저장"): st.success("임시 저장 완료!")

with tab1:
    s = st.session_state.summary_data
    ca, cb, cc, cd = st.columns(4)
    def m(col, l, usd_v, krw_s):
        with col:
            st.caption(l); st.subheader(f"${usd_v:,.2f}"); st.markdown(f"<p class='krw-label'>{krw_s}</p>", unsafe_allow_html=True)
