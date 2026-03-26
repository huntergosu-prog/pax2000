import streamlit as st
import pandas as pd
import io
import re

# 실시간 환율을 위한 yfinance 안전 로드
try:
    import yfinance as yf
    YF_AVAILABLE = True
except ImportError:
    YF_AVAILABLE = False

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="팍스2000 통합 대시보드", layout="wide")

# 콤팩트한 화면을 위한 CSS
st.markdown("""
    <style>
    html, body, [class*="css"] { font-size: 13px !important; }
    div[data-testid="stMetricValue"] { font-size: 16px !important; }
    h1 { font-size: 20px !important; margin-bottom: 5px; }
    h3 { font-size: 15px !important; margin-top: 10px; }
    .stDataFrame { font-size: 12px !important; }
    .krw-label { color: #ff4b4b; font-size: 12px; font-weight: bold; margin-top: -5px; margin-bottom: 5px; }
    div[data-testid="stVerticalBlock"] > div { gap: 0rem !important; }
    </style>
    """, unsafe_allow_html=True)

# 실시간 환율 가져오기 함수
@st.cache_data(ttl=3600)
def get_realtime_exchange_rate():
    if not YF_AVAILABLE: return 1442.50
    try:
        ticker = yf.Ticker("USDKRW=X")
        data = ticker.history(period="1d")
        return round(data['Close'].iloc[-1], 2)
    except: return 1442.50

# 금액 문자열에서 숫자만 추출
def parse_money(money_str):
    try: return float(re.sub(r'[^\d.]', '', str(money_str)))
    except: return 0.0

# 2. 최상단: 실시간 환율 및 로드맵
st.title("🚀 팍스2000: 130억 로드맵 관리 시스템")

auto_rate = get_realtime_exchange_rate()
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    ex_rate = st.number_input(f"현재 환율(실시간: {auto_rate})", value=auto_rate, step=0.1)

# 로드맵 박스 (달러 위 / 원화 중간 / 날짜 아래)
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

# 3. 자산 요약 현황 (달러 위 / 원화 아래)
def asset_metric(col, label, usd_val):
    with col:
        st.caption(label)
        st.subheader(f"${usd_val:,.2f}")
        st.markdown(f"<p class='krw-label'>₩{usd_val * ex_rate:,.0f}</p>", unsafe_allow_html=True)

ca, cb, cc, cd = st.columns(4)
asset_metric(ca, "총 투입금", 40000000 / ex_rate)
asset_metric(cb, "현재 잔액", 18012969 / ex_rate)
asset_metric(cc, "누적 수익", -21987031 / ex_rate)
asset_metric(cd, "본전 수익목표", 14410.42)

st.divider()

# 4. 탭 구성
tab1, tab2, tab3 = st.tabs(["📊 자산 통계", "📝 실시간 매매일지", "💸 출금 & 대출"])

with tab1:
    st.subheader("🗓️ 월별 수익 요약")
    summary_df = pd.DataFrame({
        "구분": ["1월", "2월", "3월", "합계"],
        "수익(달러)": ["$1,908", "-$6,694", "$0", "-$4,786"],
        "수익(원화)": ["₩2,752,527", "-₩9,656,989", "₩0", "-₩6,904,462"]
    })
    st.table(summary_df)

with tab2:
    st.subheader("📉 선물 매매 기록 (입출금 포함)")
    uploaded_file = st.file_uploader("CSV 업로드", type=["csv"], label_visibility="collapsed")
    if 'main_df' not in st.session_state: st.session_state.main_df = pd.DataFrame()

    if uploaded_file:
        try:
            content = uploaded_file.getvalue().decode('utf-8-sig')
            lines = content.splitlines()
            h_idx = next((i for i, line in enumerate(lines) if "종목명" in line or "날짜" in line), 0)
            df = pd.read_csv(io.StringIO("\n".join(lines[h_idx:])))
            # NO, 비고2 컬럼 삭제
            df = df.drop(columns=[c for c in df.columns if c.lower() in ['no', '비고2']], errors='ignore')
            st.session_state.main_df = df.dropna(how='all')
            st.success("데이터 로드 완료!")
        except Exception as e: st.error(f"파일 에러: {e}")

    if not st.session_state.main_df.empty:
        edited_df = st.data_editor(st.session_state.main_df, num_rows="dynamic", use_container_width=True, height=550)
        if st.button("💾 변경사항 저장"):
            st.session_state.main_df = edited_df
            st.success("업데이트 완료!")

with tab3:
    st.subheader("💳 대출 및 출금 현황")
    st.table(pd.DataFrame({
        "대출처": ["KB라이프", "하나생명", "마이너스통장"],
        "금액": ["₩10,000,000", "₩5,000,000", "₩20,000,000"],
        "비고": ["보험약관대출", "신용대출", "생활비"]
    }))
