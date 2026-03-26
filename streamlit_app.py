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
        rate = round(data['Close'].iloc[-1], 2)
        return rate, datetime.now().strftime("%m/%d %H:%M")
    except: return 1442.50, "연결에러"

def parse_money(money_str):
    if pd.isna(money_str) or str(money_str).strip() == "": return 0.0
    try:
        # 숫자, 소수점, 마이너스 기호만 남김
        clean = re.sub(r'[^\d.-]', '', str(money_str))
        return float(clean) if clean else 0.0
    except: return 0.0

# 3. 데이터 세션 상태 초기화
if 'main_df' not in st.session_state: 
    st.session_state.main_df = pd.DataFrame(columns=["날짜", "종목명", "포지션", "매수가", "매도가", "수량", "수수료", "비고"])
if 'monthly_df' not in st.session_state: 
    st.session_state.monthly_df = pd.DataFrame(index=["수익($)", "수익(₩)"])
if 'loan_df' not in st.session_state: 
    st.session_state.loan_df = pd.DataFrame(columns=["대출처", "대출금액", "상환금액", "비고"])
if 'summary_data' not in st.session_state: 
    st.session_state.summary_data = {"투입": "₩0", "잔액": "₩0", "수익": "₩0", "본전": "$0"}

# 4. 상단 대시보드
st.title("🚀 팍스2000: 통합 자산 관리 시스템")
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
    up_file = st.file_uploader("CSV 업로드", type=["csv"], label_visibility="collapsed")
    
    if up_file:
        try:
            raw = pd.read_csv(io.StringIO(up_file.getvalue().decode('utf-8-sig')), header=None)
            
            # 검색 및 파싱 강화
            for r in range(len(raw)):
                row_list = raw.iloc[r].astype(str).tolist()
                row_str = " ".join(row_list)
                
                # 요약 데이터 추출
                if "잔액" in row_str or "본전" in row_str:
                    for c, val in enumerate(row_list):
                        if "잔액" in val: st.session_state.summary_data["잔액"] = str(raw.iloc[r+1, c])
                        if "본전" in val: st.session_state.summary_data["본전"] = str(raw.iloc[r+1, c])
                        if "수익" in val: st.session_state.summary_data["수익"] = str(raw.iloc[r+1, c])
                        if "투입" in val: st.session_state.summary_data["투입"] = str(raw.iloc[r+1, c])
                
                # 월별 데이터 추출
                if "1월" in row_str:
                    try:
                        m_idx = next(i for i, v in enumerate(row_list) if "1월" in v)
                        st.session_state.monthly_df = pd.DataFrame(
                            [raw.iloc[r+1, m_idx:m_idx+12].tolist(), raw.iloc[r+2, m_idx:m_idx+12].tolist()],
                            columns=[f"{i}월" for i in range(1, 13)],
                            index=["수익($)", "수익(₩)"]
                        )
                    except: pass

                # 매매일지 추출
                if "종목명" in row_str:
                    df = raw.iloc[r:].copy()
                    df.columns = df.iloc[0]
                    df = df[1:].reset_index(drop=True)
                    cols_to_drop = [c for c in df.columns if any(x in str(c).lower() for x in ['no', '비고2', 'unnamed'])]
                    st.session_state.main_df = df.drop(columns=cols_to_drop, errors='ignore').dropna(how='all')
            
            st.success("데이터 로드 완료!")
        except Exception as e: st.error(f"파일 처리 중 오류: {e}")

    # 데이터 편집 및 저장
    st.session_state.main_df = st.data_editor(st.session_state.main_df, num_rows="dynamic", use_container_width=True)
    if st.button("💾 매매일지 저장"): st.success("저장 완료!")
    
    csv_log = st.session_state.main_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 매매일지 다운로드", csv_log, "trading_log.csv", "text/csv")

with tab1:
    s = st.session_state.summary_data
    ca, cb, cc, cd = st.columns(4)
    
    def display_metric(col, label, usd_val, krw_str):
        with col:
            st.caption(label)
            try:
                st.subheader(f"${float(usd_val):,.2f}")
            except:
                st.subheader("$0.00")
