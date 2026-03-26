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

st.set_page_config(page_title="통합 대시보드", layout="wide")

# 1. 디자인 CSS (글자 크기 축소 및 빨간색 원화 강조)
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

# 2. 환율 함수 (4시간 캐시 및 수동 갱신)
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
    if pd.isna(money_str): return 0.0
    try: return float(re.sub(r'[^\d.-]', '', str(money_str)))
    except: return 0.0

# 3. 최상단: 대시보드
st.title("🚀130억 로드맵 관리 시스템")
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

# 데이터 세션 초기화
if 'main_df' not in st.session_state: st.session_state.main_df = pd.DataFrame()
if 'monthly_df' not in st.session_state: st.session_state.monthly_df = pd.DataFrame()
if 'loan_df' not in st.session_state: st.session_state.loan_df = pd.DataFrame()

# 4. 파일 업로드 및 정밀 파싱 로직
uploaded_file = st.sidebar.file_uploader("엑셀(CSV) 업로드", type=["csv"])
if uploaded_file:
    try:
        raw_data = pd.read_csv(uploaded_file, header=None, encoding='utf-8-sig')
        
        # A. 월별 수익 파싱 (2~3행)
        try:
            m_header = raw_data.iloc[1, 14:26].tolist() # 1월~12월 헤더
            m_usd = raw_data.iloc[1, 14:26].tolist()
            m_krw = raw_data.iloc[2, 14:26].tolist()
            st.session_state.monthly_df = pd.DataFrame({"월": [f"{i+1}월" for i in range(12)], "수익($)": m_usd, "수익(₩)": m_krw}).T
        except: pass

        # B. 대출 정보 파싱 (4~5행)
        try:
            l_names = raw_data.iloc[3, 6:10].tolist() # KB, 하나, 마이너스 등
            l_vals = raw_data.iloc[4, 6:10].tolist()
            st.session_state.loan_df = pd.DataFrame({"대출처": l_names, "금액": l_vals})
        except: pass

        # C. 매매일지 파싱 ('종목명' 줄 찾기)
        for i, row in raw_data.iterrows():
            if "종목명" in str(row.values):
                df = pd.read_csv(io.StringIO("\n".join(raw_data.iloc[i:].astype(str).apply(lambda x: ",".join(x), axis=1))))
                df.columns = df.iloc[0]
                df = df[1:].reset_index(drop=True)
                # NO, 비고2 삭제
                cols_to_drop = [c for c in df.columns if any(x in str(c).lower() for x in ['no', '비고2', 'unnamed'])]
                st.session_state.main_df = df.drop(columns=cols_to_drop, errors='ignore').dropna(how='all')
                break
        st.sidebar.success("로드 완료!")
    except Exception as e: st.sidebar.error(f"에러: {e}")

# 5. 탭 구성
tab1, tab2, tab3 = st.tabs(["📊 자산 통계", "📝 실시간 매매일지", "💸 출금 & 대출"])

with tab1:
    ca, cb, cc, cd = st.columns(4)
    # 엑셀 데이터 기반 요약 (실제 값 파싱 로직 추가 가능)
    def asset_metric(col, label, usd, krw):
        with col:
            st.caption(label); st.subheader(f"${usd}"); st.markdown(f"<p class='krw-label'>₩{krw}</p>", unsafe_allow_html=True)
    
    asset_metric(ca, "총 투입금", "27,729.64", "40,000,000")
    asset_metric(cb, "현재 잔액", "12,487.33", "18,012,969")
    asset_metric(cc, "누적 수익", "-15,242.31", "-21,987,031")
    asset_metric(cd, "본전 수익목표", "14,410.42", "20,787,031")
    
    st.write("---")
    st.subheader("🗓️ 월별 수익 요약")
    if not st.session_state.monthly_df.empty: st.table(st.session_state.monthly_df)

with tab2:
    if not st.session_state.main_df.empty:
        edited = st.data_editor(st.session_state.main_df, num_rows="dynamic", use_container_width=True, height=550)
        if st.button("💾 데이터 저장"):
            st.session_state.main_df = edited
            st.success("업데이트 완료!")
    else: st.info("일지가 없어. 파일을 올려줘!")

with tab3:
    st.subheader("💳 대출 및 출금 현황")
    if not st.session_state.loan_df.empty: st.table(st.session_state.loan_df)
