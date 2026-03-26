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
    .update-time { font-size: 11px; color: #888; }
    div[data-testid="stVerticalBlock"] > div { gap: 0rem !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. 환율 함수
@st.cache_data(ttl=14400)
def get_exchange_rate():
    if not YF_AVAILABLE: return 1442.50, "기본값"
    try:
        ticker = yf.Ticker("USDKRW=X")
        data = ticker.history(period="1d")
        rate = round(data['Close'].iloc[-1], 2)
        fetch_time = datetime.now().strftime("%m/%d %H:%M")
        return rate, fetch_time
    except: return 1442.50, "연결에러"

def parse_money(money_str):
    if pd.isna(money_str): return 0.0
    try:
        clean = re.sub(r'[^\d.-]', '', str(money_str))
        return float(clean) if clean else 0.0
    except: return 0.0

# 3. 데이터 세션 상태 초기화 (중요: 에러 방지를 위해 summary_data를 딕셔너리로 초기화)
if 'main_df' not in st.session_state: st.session_state.main_df = pd.DataFrame()
if 'monthly_df' not in st.session_state: st.session_state.monthly_df = pd.DataFrame()
if 'loan_df' not in st.session_state: st.session_state.loan_df = pd.DataFrame()
if 'summary_data' not in st.session_state: st.session_state.summary_data = {}

# 4. 상단 레이아웃: 로드맵
st.title("🚀 팍스2000: 130억 로드맵 관리 시스템")
current_rate, last_update = get_exchange_rate()

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    if st.button("🔄 환율 갱신"):
        st.cache_data.clear(); st.rerun()
    ex_rate = st.number_input(f"현재 환율", value=current_rate, step=0.1)
    st.markdown(f"<p class='update-time'>동기화: {last_update}</p>", unsafe_allow_html=True)

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

# 5. 탭 구성
tab1, tab2, tab3 = st.tabs(["📊 자산 통계", "📝 실시간 매매일지", "💸 출금 & 대출"])

with tab2:
    st.subheader("📉 선물 매매 기록 (CSV 업로드)")
    uploaded_file = st.file_uploader("파일을 여기에 올려줘", type=["csv"], label_visibility="collapsed")
    
    if uploaded_file:
        try:
            content = uploaded_file.getvalue().decode('utf-8-sig')
            raw = pd.read_csv(io.StringIO(content), header=None)
            
            # A. 월별 수익 파싱 (Row 4~6)
            try:
                m_header = raw.iloc[4, 8:20].tolist()
                m_usd = raw.iloc[5, 8:20].tolist()
                m_krw = raw.iloc[6, 8:20].tolist()
                st.session_state.monthly_df = pd.DataFrame({"월": m_header, "수익($)": m_usd, "수익(₩)": m_krw}).set_index("월").T
            except: pass
            
            # B. 대출 정보 파싱 (Row 1~2, Col 15~18)
            try:
                l_names = raw.iloc[1, 15:19].tolist()
                l_vals = raw.iloc[2, 15:19].tolist()
                st.session_state.loan_df = pd.DataFrame({"대출처": l_names, "금액": l_vals})
            except: pass

            # C. 요약 지표 (Row 2)
            try:
                st.session_state.summary_data = {
                    "총투입": str(raw.iloc[2, 12]),
                    "잔액": str(raw.iloc[2, 8]),
                    "누적수익": str(raw.iloc[2, 11]),
                    "본전목표": str(raw.iloc[2, 10])
                }
            except: pass

            # D. 매매일지 파싱 (헤더 기반)
            header_idx = -1
            for i in range(len(raw)):
                row_vals = raw.iloc[i].astype(str).tolist()
                if "종목명" in row_vals and "매수가" in row_vals:
                    header_idx = i
                    break
            
            if header_idx != -1:
                df = raw.iloc[header_idx:].copy()
                df.columns = df.iloc[0]
                df = df[1:].reset_index(drop=True)
                cols_to_drop = [c for c in df.columns if any(x in str(c).lower() for x in ['no', '비고2', 'unnamed'])]
                st.session_state.main_df = df.drop(columns=cols_to_drop, errors='ignore').dropna(how='all')
            
            st.success("데이터 로드 완료!")
        except Exception as e:
            st.error(f"로드 실패: {e}")

    if not st.session_state.main_df.empty:
        st.data_editor(st.session_state.main_df, num_rows="dynamic", use_container_width=True, height=600)

with tab1:
    ca, cb, cc, cd = st.columns(4)
    # 딕셔너리에서 데이터 가져오기 (에러 방지)
    sum_d = st.session_state.summary_data
    
    ca.metric("총 투입금", sum_d.get("총투입", "₩40,000,000"))
    cb.metric("현재 잔액", sum_d.get("잔액", "₩18,012,969"))
    cc.metric("누적 수익", sum_d.get("누적수익", "-₩21,987,031"))
    cd.metric("본전 수익목표", sum_d.get("본전목표", "$14,410.42"))
    
    st.write("---")
    st.subheader("🗓️ 월별 수익 요약")
    if not st.session_state.monthly_df.empty:
        st.table(st.session_state.monthly_df)

with tab3:
    st.subheader("💳 대출 및 출금 현황")
    if not st.session_state.loan_df.empty:
        st.table(st.session_state.loan_df)
