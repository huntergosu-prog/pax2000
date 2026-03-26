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

# 3. 데이터 세션 상태 초기화 (영구 저장용 히스토리 추가)
if 'main_df' not in st.session_state: 
    st.session_state.main_df = pd.DataFrame(columns=["날짜", "종목명", "포지션", "매수가", "매도가", "수익", "비고"])
if 'monthly_df' not in st.session_state: 
    st.session_state.monthly_df = pd.DataFrame(index=["수익($)", "수익(₩)"])
if 'loan_df' not in st.session_state: 
    st.session_state.loan_df = pd.DataFrame(columns=["대출처", "대출금액", "상환금액", "비고"])
if 'summary_data' not in st.session_state: 
    st.session_state.summary_data = {"투입": "₩40,000,000", "잔액": "₩18,012,969", "수익": "-₩21,987,031", "본전": "$14,410.42"}
if 'save_history' not in st.session_state: st.session_state.save_history = []

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
    up_file = st.file_uploader("파일 업로드 (공백 제거된 파일)", type=["csv"], label_visibility="collapsed")
    
    if up_file:
        try:
            raw = pd.read_csv(io.StringIO(up_file.getvalue().decode('utf-8-sig')), header=None)
            
            # 지능형 파싱: 특정 키워드를 찾아서 데이터 추출
            for r in range(min(15, len(raw))):
                row_str = " ".join(raw.iloc[r].astype(str))
                # 요약 정보 찾기
                if "현 잔액" in row_str:
                    for c in range(raw.shape[1]):
                        val = str(raw.iloc[r, c])
                        if "현 잔액" in val: st.session_state.summary_data["잔액"] = str(raw.iloc[r+1, c])
                        if "본전" in val and "$" in val: st.session_state.summary_data["본전"] = str(raw.iloc[r+1, c])
                        if "수익" in val and "누적" in val: st.session_state.summary_data["수익"] = str(raw.iloc[r+1, c])
                        if "총 투입금" in val: st.session_state.summary_data["투입"] = str(raw.iloc[r+1, c])
                
                # 월별 수익률 찾기
                if "1월" in row_str:
                    m_header = [f"{i}월" for i in range(1, 13)]
                    start_c = next((i for i, h in enumerate(raw.iloc[r].tolist()) if "1월" in str(h)), 0)
                    st.session_state.monthly_df = pd.DataFrame([raw.iloc[r+1, start_c:start_c+12].tolist(), raw.iloc[r+2, start_c:start_c+12].tolist()], columns=m_header, index=["수익($)", "수익(₩)"])

                # 매매일지 찾기
                if "종목명" in row_str:
                    df = raw.iloc[r:].copy()
                    df.columns = df.iloc[0]; df = df[1:].reset_index(drop=True)
                    cols_to_drop = [c for c in df.columns if any(x in str(c).lower() for x in ['no', '비고2', 'unnamed'])]
                    st.session_state.main_df = df.drop(
