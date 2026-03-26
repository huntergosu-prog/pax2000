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

# 3. 데이터 세션 초기화 (중요: 모든 탭 데이터 구조 미리 생성)
if 'main_df' not in st.session_state: 
    st.session_state.main_df = pd.DataFrame(columns=["날짜", "종목명", "포지션", "매수가", "매도가", "수량", "수수료", "비고"])
if 'monthly_df' not in st.session_state: 
    st.session_state.monthly_df = pd.DataFrame(index=["수익($)", "수익(₩)"])
if 'loan_df' not in st.session_state: 
    st.session_state.loan_df = pd.DataFrame(columns=["대출처", "대출금액", "상환금액", "비고"])
if 'summary_data' not in st.session_state: 
    st.session_state.summary_data = {"투입": "₩40,000,000", "잔액": "₩18,012,969", "수익": "-₩21,987,031", "본전": "$14,410.42"}

# 4. 상단 대시보드 (로드맵)
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
    up_file = st.file_uploader("엑셀(CSV) 업로드하여 장부 동기화", type=["csv"], label_visibility="collapsed")
    
    if up_file:
        try:
            raw = pd.read_csv(io.StringIO(up_file.getvalue().decode('utf-8-sig')), header=None)
            
            # A. 요약 지표 복구
            st.session_state.summary_data = {
                "잔액": str(raw.iloc[2, 8]), "본전": str(raw.iloc[2, 10]), 
                "수익": str(raw.iloc[2, 11]), "투입": str(raw.iloc[2, 12])
            }
            
            # B. 월별 수익률 복구 (Row 4, 5, 6 / Col 8~19)
            m_header = raw.iloc[4, 8:20].tolist()
            m_usd = raw.iloc[5, 8:20].tolist()
            m_krw = raw.iloc[6, 8:20].tolist()
            st.session_state.monthly_df = pd.DataFrame([m_usd, m_krw], columns=m
