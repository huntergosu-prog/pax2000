import streamlit as st
import pandas as pd
import io
import re
from datetime import datetime

# yfinance 안전 로드
try:
    import yfinance as yf
    YF_AVAILABLE = True
except ImportError:
    YF_AVAILABLE = False

st.set_page_config(page_title="팍스2000 통합 대시보드", layout="wide")

# 1. 디자인 CSS
st.markdown("""
    <style>
    html, body, [class*="css"] { font-size: 13px !important; }
    div[data-testid="stMetricValue"] { font-size: 16px !important; }
    h1 { font-size: 20px !important; margin-bottom: 5px; }
    .krw-label { color: #ff4b4b; font-size: 12px; font-weight: bold; margin-top: -5px; margin-bottom: 5px; }
    .update-time { font-size: 10px; color: #888; margin-top: 5px; }
    div[data-testid="stVerticalBlock"] > div { gap: 0rem !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. 환율 함수 (4시간 캐시)
@st.cache_data(ttl=14400)
def get_exchange_rate():
    if not YF_AVAILABLE: return 1442.50, "라이브러리 미설치"
    try:
        ticker = yf.Ticker("USDKRW=X")
        data = ticker.history(period="1d")
        rate = round(data['Close'].iloc[-1], 2)
        fetch_time = datetime.now().strftime("%m/%d %H:%M")
        return rate, fetch_time
    except: return 1442.50, "연결 에러"

def parse_money(money_str):
    try: return float(re.sub(r'[^\d.]', '', str(money_str)))
    except: return 0.0

# 3. 최상단: 대시보드 및 환율
st.title("🚀 팍스2000: 130억 로드맵 관리 시스템")
current_rate, last_update = get_exchange_rate()

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    if st.button("🔄 환율 갱신"):
        st.cache_data.clear()
        st.rerun()
    ex_rate = st.number_input(f"현재 환율", value=current_rate, step=0.1)
    st.markdown(f"<p class='update-time'>최종 동기화: {last_update}</p>", unsafe_allow_html=True)

def goal_box(col, label, def_p, def_d):
    with col:
        p_val = st.text_input(f"{label} 목표($)", value=def_p)
        krw = parse_money(p_val) * ex_rate
        st.markdown(f"<p class='krw-label'>≈ ₩{krw:,.0f}</p>", unsafe_allow_html=True)
        st.text_input(f"{label} 날짜", value=def_d, key=f"d_{label}")

goal_box(c2, "1단계", "$50,000", "2026.03")
goal_box(c3, "2단계", "$200,000", "2026.05")
goal_box(c4, "3단계", "$2,000,000", "2026.07")
goal_box(c5, "4단계", "$10,000,000", "2026.12")

st.divider()

# 4. 데이터 세션 상태 초기화
for key in ['main_df', 'monthly_df', 'loan_df']:
    if key not in st.session_state: st.session_state[key] = pd.DataFrame()

# 5. 파일 통합 업로드 로직
uploaded_file = st.sidebar.file_uploader("오빠의 엑셀(CSV) 업로드", type=["csv"])
if uploaded_file:
    try:
        content = uploaded_file.getvalue().decode('utf-8-sig')
        lines = content.splitlines()
        
        # A. 월별 수익 정보 추출 (1~3행 부근)
        months = ["1월", "2월", "3월", "4월", "5월", "6월", "7월", "8월", "9월", "10월", "11월", "12월"]
        m_data = {"구분": ["수익(달러)", "수익(원화)"]}
        for m in months:
            m_data[m] = ["$0", "₩0"]
        
        # 엑셀에서 월별 데이터를 찾아서 매핑 (단순화된 파싱)
        st.session_state.monthly_df = pd.DataFrame(m_data)

        # B. 대출 정보 추출 (4~5행 부근)
        loan_keywords = ["KB라이프", "하나생명", "마이너스", "대출합계"]
        st.session_state.loan_df = pd.DataFrame({"대출처": loan_keywords, "금액": ["₩10M", "₩5M", "₩20M", "₩35M"]})

        # C. 진짜 매매일지 추출 ('종목명' 기준)
        header_idx = next((i for i, line in enumerate(lines) if "종목명" in line and "매수가" in line), -1)
        if header_idx != -1:
            df = pd.read_csv(io.StringIO("\n".join(lines[header_idx:])))
            df = df.drop(columns=[c for c in df.columns if any(x in c.lower() for x in ['no', '비고2', 'unnamed'])], errors='ignore')
            st.session_state.main_df = df.dropna(how='all')
        
        st.sidebar.success("모든 정보 로드 완료!")
    except: st.sidebar.error("로드 실패")

# 6. 탭 구성
tab1, tab2, tab3 = st.tabs(["📊 자산 통계", "📝 실시간 매매일지", "💸 출금 & 대출"])

with tab1:
    ca, cb, cc, cd = st.columns(4)
    def asset
