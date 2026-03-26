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

# 1. 디자인 CSS (콤팩트 테마)
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

# 2. 유틸리티 함수
@st.cache_data(ttl=14400)
def get_exchange_rate():
    if not YF_AVAILABLE: return 1442.50, "기본값"
    try:
        ticker = yf.Ticker("USDKRW=X")
        data = ticker.history(period="1d")
        rate = round(data['Close'].iloc[-1], 2)
        return rate, datetime.now().strftime("%m/%d %H:%M")
    except: return 1442.50, "연결에러"

def parse_money(money_str):
    if pd.isna(money_str): return 0.0
    try:
        clean = re.sub(r'[^\d.-]', '', str(money_str))
        return float(clean) if clean else 0.0
    except: return 0.0

# 3. 데이터 세션 상태 초기화 (에러 방지를 위해 기본값 꽉 채움)
if 'main_df' not in st.session_state: 
    st.session_state.main_df = pd.DataFrame(columns=["날짜", "종목명", "포지션", "매수가", "매도가", "수량", "수수료", "비고"])
if 'monthly_df' not in st.session_state: 
    st.session_state.monthly_df = pd.DataFrame(index=["수익($)", "수익(₩)"])
if 'loan_df' not in st.session_state: 
    st.session_state.loan_df = pd.DataFrame(columns=["대출처", "대출금액", "상환금액", "비고"])
if 'summary_data' not in st.session_state: 
    st.session_state.summary_data = {
        "투입_KRW": "₩40,000,000", 
        "잔액_KRW": "₩18,012,969", 
        "수익_KRW": "-₩21,987,031", 
        "본전_USD": "$14,410.42"
    }

# 4. 상단 레이아웃: 로드맵
st.title("🚀 팍스2000: 130억 로드맵 관리 시스템")
current_rate, last_update = get_exchange_rate()

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    if st.button("🔄 환율 갱신"):
        st.cache_data.clear(); st.rerun()
    ex_rate = st.number_input("현재 환율", value=current_rate, step=0.1)
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
tab1, tab2, tab3 = st.tabs(["📊 자산 통계", "📝 실시간 매매일지", "💸 대출 & 상환"])

with tab2:
    st.subheader("📉 선물 매매 기록")
    uploaded_file = st.file_uploader("파일 업로드 (기존 데이터 복구용)", type=["csv"], label_visibility="collapsed")
    
    if uploaded_file:
        try:
            raw = pd.read_csv(io.StringIO(uploaded_file.getvalue().decode('utf-8-sig')), header=None)
            # 매매일지 파싱 (헤더 기반)
            for i in range(len(raw)):
                if "종목명" in str(raw.iloc[i].values):
                    df = raw.iloc[i:].copy()
                    df.columns = df.iloc[0]
                    df = df[1:].reset_index(drop=True)
                    cols_to_drop = [c for c in df.columns if any(x in str(c).lower() for x in ['no', '비고2', 'unnamed'])]
                    st.session_state.main_df = df.drop(columns=cols_to_drop, errors='ignore').dropna(how='all')
                    break
            # 요약 지표 및 월별 데이터 복구
            st.session_state.summary_data = {
                "잔액_KRW": str(raw.iloc[2, 8]), 
                "본전_USD": str(raw.iloc[2, 10]), 
                "수익_KRW": str(raw.iloc[2, 11]), 
                "투입_KRW": str(raw.iloc[2, 12])
            }
            st.session_state.monthly_df = raw.iloc[5:7, 8:20].copy()
            st.session_state.monthly_df.columns = raw.iloc[4, 8:20].tolist()
            st.session_state.monthly_df.index = ["수익($)", "수익(₩)"]
            
            l_vals = raw.iloc[2, 15:19].tolist()
            st.session_state.loan_df = pd.DataFrame({"대출처": ["KB라이프", "하나생명", "마이너스", "합계"], "대출금액": l_vals, "상환금액": ["₩0"]*4})
            st.success("데이터를 성공적으로 불러왔어, 오빠!")
        except Exception as e: st.error(f"파일 로드 중 실수했어: {e}")

    # 매매일지 에디터 (줄 추가 가능)
    edited_main = st.data_editor(st.session_state.main_df, num_rows="dynamic", use_container_width=True, height=450)
    if st.button("💾 매매일지 임시 저장"):
        st.session_state.main_df = edited_main
        st.success("매매 기록 저장 완료!")

    # 엑셀 다운로드 (오빠의 소중한 히스토리!)
    csv = edited_main.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 현재 일지 엑셀(CSV) 다운로드", data=csv, file_name=f"pax2000_trading_{datetime.now().strftime('%m%d')}.csv", mime="text/csv")

with tab1:
    ca, cb, cc, cd = st.columns(4)
    s = st.session_state.summary_data
    
    def asset_metric(col, label, usd_val, krw_str):
        with col:
            st.caption(label)
            st.subheader(f"${usd_val:,.2f}")
            st.markdown(f"<p class='krw-label'>{krw_str}</p>", unsafe_allow_html=True)

    # 안전하게 데이터를 가져오도록 .get() 사용 (에러 방지 핵심!)
    t_krw = s.get("투입_KRW", "₩40,000,000")
    z_krw = s.get("잔액_KRW", "₩18,012,969")
    s_krw = s.get("수익_KRW", "-₩21,987,031")
    b_usd = s.get("본전_USD", "$14,410.42")

    asset_metric(ca, "총 투입금", parse_money(t_krw)/ex_rate, t_krw)
    asset_metric(cb, "현재 잔액", parse_money(z_krw)/ex_rate, z_krw)
    asset_metric(cc, "누적 수익", parse_money(s_krw)/ex_rate, s_krw)
    asset_metric(cd, "본전 수익목표", parse_money(b_usd), f"₩{parse_money(b_usd)*ex_rate:,.0f}")
    
    st.write("---")
    st.subheader("🗓️ 월별 수익 요약")
    if not st.session_state.monthly_df.empty: st.table(st.session_state.monthly_df)

with tab3:
    st.subheader("💳 대출 내역 및 상환 관리")
    st.info("💡 표 아래의 (+) 버튼을 눌러 새로운 대출이나 상환 내역을 직접 입력해 봐.")
    
    # 대출/상환 에디터 (동적 추가 기능 적용!)
    edited_loan = st.data_editor(st.session_state.loan_df, num_rows="dynamic", use_container_width=True)
    if st.button("💾 대출/상환 정보 임시 저장"):
        st.session_state.loan_df = edited_loan
        st.success("금융 데이터 업데이트 완료!")
    
    # 대출 내역 다운로드
    loan_csv = edited_loan.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 대출 내역 다운로드", data=loan_csv, file_name="pax2000_loans.csv")
