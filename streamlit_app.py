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

# 2. 실시간 환율 (4시간 캐시)
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
    try:
        clean_str = re.sub(r'[^\d.-]', '', str(money_str))
        return float(clean_str) if clean_str else 0.0
    except: return 0.0

# 3. 데이터 세션 상태 초기화
for key in ['main_df', 'monthly_df', 'loan_df']:
    if key not in st.session_state: st.session_state[key] = pd.DataFrame()

# 4. 최상단: 대시보드
st.title("🚀 팍스2000: 130억 로드맵 관리 시스템")
current_rate, last_update = get_exchange_rate()

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    if st.button("🔄 환율 갱신"):
        st.cache_data.clear(); st.rerun()
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

# 5. 탭 구성
tab1, tab2, tab3 = st.tabs(["📊 자산 통계", "📝 실시간 매매일지", "💸 출금 & 대출"])

with tab2:
    st.subheader("📉 선물 매매 기록 (CSV 업로드)")
    uploaded_file = st.file_uploader("엑셀 파일을 여기에 올려줘", type=["csv"], label_visibility="collapsed")
    
    if uploaded_file:
        try:
            content = uploaded_file.getvalue().decode('utf-8-sig')
            lines = content.splitlines()
            raw_df = pd.read_csv(io.StringIO(content), header=None)

            # A. 매매일지 파싱 (헤더 기반으로 튼튼하게 찾기)
            header_idx = -1
            for i, line in enumerate(lines):
                if "종목명" in line and "매수가" in line:
                    header_idx = i
                    break
            
            if header_idx != -1:
                df = pd.read_csv(io.StringIO("\n".join(lines[header_idx:])))
                # 'None' 텍스트나 불필요한 열 자동 제거
                cols_to_drop = [c for c in df.columns if any(x in str(c).lower() for x in ['no', '비고2', 'unnamed'])]
                st.session_state.main_df = df.drop(columns=cols_to_drop, errors='ignore').replace('None', None).dropna(how='all')
            
            # B. 월별 통계 파싱 (데이터 개수에 맞춰 유연하게)
            try:
                m_data = raw_df.iloc[1:3, 14:].dropna(axis=1, how='all').copy()
                if not m_data.empty:
                    col_names = [f"{i+1}월" for i in range(m_data.shape[1])]
                    m_data.columns = col_names[:m_data.shape[1]]
                    m_data.index = ["수익($)", "수익(₩)"]
                    st.session_state.monthly_df = m_data
            except: pass
            
            # C. 대출 정보 파싱
            try:
                l_data = raw_df.iloc[3:5, 6:10].dropna(axis=1, how='all').copy()
                st.session_state.loan_df = l_data
            except: pass
            
            st.success("데이터를 다시 정렬해서 불러왔어!")
        except Exception as e:
            st.error(f"로드 에러: {e}")

    if not st.session_state.main_df.empty:
        st.data_editor(st.session_state.main_df, num_rows="dynamic", use_container_width=True, height=600)

with tab1:
    ca, cb, cc, cd = st.columns(4)
    def asset_metric(col, label, usd, krw):
        with col:
            st.caption(label); st.subheader(f"${usd}"); st.markdown(f"<p class='krw-label'>₩{krw}</p>", unsafe_allow_html=True)
    
    asset_metric(ca, "총 투입금", "27,729.64", "40,000,000")
    asset_metric(cb, "현재 잔액", "12,487.33", "18,012,969")
    asset_metric(cc, "누적 수익", "-15,242.31", "-21,987,031")
    asset_metric(cd, "본전 수익목표", "14,410.42", "20,787,031")
    
    st.write("---")
    st.subheader("🗓️ 월별 수익 요약")
    if not st.session_state.monthly_df.empty:
        st.table(st.session_state.monthly_df)

with tab3:
    st.subheader("💳 대출 및 출금 현황")
    if not st.session_state.loan_df.empty:
        st.table(st.session_state.loan_df)
