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

# 3. 데이터 세션 상태 초기화
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
            
            # A. 월별 수익 파싱
            try:
                m_header = raw.iloc[4, 8:20].tolist()
                m_usd = raw.iloc[5, 8:20].tolist()
                m_krw = raw.iloc[6, 8:20].tolist()
                st.session_state.monthly_df = pd.DataFrame({"월": m_header, "수익($)": m_usd, "수익(₩)": m_krw}).set_index("월").T
            except: pass
            
            # B. 대출 정보 파싱 + 상환액 컬럼 추가
            try:
                l_names = raw.iloc[1, 15:19].tolist()
                l_vals = raw.iloc[2, 15:19].tolist()
                st.session_state.loan_df = pd.DataFrame({
                    "대출처": l_names, 
                    "대출금액": l_vals,
                    "상환금액": ["₩0"] * len(l_names) # 초기값 설정
                })
            except: pass

            # C. 요약 지표 파싱 (달러/원화 분리 추출)
            try:
                st.session_state.summary_data = {
                    "잔액_USD": raw.iloc[2, 2], # 달러 잔액 위치
                    "잔액_KRW": raw.iloc[2, 8],
                    "수익_USD": raw.iloc[2, 3],
                    "수익_KRW": raw.iloc[2, 11],
                    "투입_KRW": raw.iloc[2, 12],
                    "본전_USD": raw.iloc[2, 10]
                }
            except: pass

            # D. 매매일지 파싱
            header_idx = -1
            for i in range(len(raw)):
                if "종목명" in str(raw.iloc[i].values):
                    header_idx = i
                    break
            if header_idx != -1:
                df = raw.iloc[header_idx:].copy()
                df.columns = df.iloc[0]
                df = df[1:].reset_index(drop=True)
                cols_to_drop = [c for c in df.columns if any(x in str(c).lower() for x in ['no', '비고2', 'unnamed'])]
                st.session_state.main_df = df.drop(columns=cols_to_drop, errors='ignore').dropna(how='all')
            
            st.success("데이터 로드 완료!")
        except Exception as e: st.error(f"로드 실패: {e}")

    if not st.session_state.main_df.empty:
        st.data_editor(st.session_state.main_df, num_rows="dynamic", use_container_width=True, height=550)

with tab1:
    ca, cb, cc, cd = st.columns(4)
    sum_d = st.session_state.summary_data
    
    # 이중 표기 함수 재적용
    def asset_metric(col, label, usd, krw):
        with col:
            st.caption(label)
            st.subheader(usd if usd else "$0.00")
            st.markdown(f"<p class='krw-label'>{krw if krw else '₩0'}</p>", unsafe_allow_html=True)

    asset_metric(ca, "총 투입금", f"${parse_money(sum_d.get('투입_KRW'))/ex_rate:,.2f}", sum_d.get("투입_KRW", "₩40,000,000"))
    asset_metric(cb, "현재 잔액", sum_d.get("잔액_USD", "$12,487.33"), sum_d.get("잔액_KRW", "₩18,012,969"))
    asset_metric(cc, "누적 수익", sum_d.get("수익_USD", "-$15,242.31"), sum_d.get("수익_KRW", "-₩21,987,031"))
    asset_metric(cd, "본전 수익목표", sum_d.get("본전_USD", "$14,410.42"), f"₩{parse_money(sum_d.get('본전_USD'))*ex_rate:,.0f}")
    
    st.write("---")
    st.subheader("🗓️ 월별 수익 요약")
    if not st.session_state.monthly_df.empty: st.table(st.session_state.monthly_df)

with tab3:
    st.subheader("💳 대출 및 상환 현황")
    if not st.session_state.loan_df.empty:
        # 상환금액을 입력할 수 있도록 에디터로 변경
        edited_loan = st.data_editor(st.session_state.loan_df, use_container_width=True)
        if st.button("💾 상환 정보 저장"):
            st.session_state.loan_df = edited_loan
            st.success("상환 정보가 반영됐어!")
