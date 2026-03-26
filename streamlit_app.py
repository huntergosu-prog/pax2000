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
    .total-row { background-color: #f8f9fa; font-weight: bold; border-top: 2px solid #ff4b4b; padding: 15px; margin-top: 10px; border-radius: 8px; }
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
    if pd.isna(money_str) or str(money_str).strip() == "" or str(money_str).lower() == "nan": return 0.0
    try:
        clean = re.sub(r'[^\d.-]', '', str(money_str))
        return float(clean) if clean else 0.0
    except: return 0.0

# 3. 데이터 세션 상태 초기화 (데이터 보존 핵심)
if 'main_df' not in st.session_state: 
    st.session_state.main_df = pd.DataFrame(columns=["날짜", "종목명", "포지션", "매수가", "매도가", "수익", "비고"])
if 'monthly_data' not in st.session_state: 
    # 연도별로 데이터를 관리할 수 있도록 구조화
    st.session_state.monthly_data = {
        "2026": pd.DataFrame(0.0, index=["수익($)", "수익(₩)"], columns=[f"{i}월" for i in range(1, 13)])
    }
if 'loan_df' not in st.session_state: 
    st.session_state.loan_df = pd.DataFrame([
        {"대출처": "KB라이프", "대출금액": 50000000.0, "상환금액": 0.0, "비고": ""},
        {"대출처": "하나생명", "대출금액": 90000000.0, "상환금액": 0.0, "비고": ""},
        {"대출처": "마이너스", "대출금액": 100000000.0, "상환금액": 0.0, "비고": ""}
    ])
if 'summary_data' not in st.session_state: 
    st.session_state.summary_data = {"투입": "₩40,000,000", "잔액": "₩18,012,969", "수익": "-₩21,987,031", "본전": "$14,410.42"}

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
        krw = parse_money(p_val) * (cur_ex if cur_ex else 1442.5)
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
    up_file = st.file_uploader("파일 업로드 (CSV)", type=["csv"], label_visibility="collapsed")
    
    if up_file:
        try:
            raw = pd.read_csv(io.StringIO(up_file.getvalue().decode('utf-8-sig')), header=None).fillna("")
            for r in range(len(raw)):
                for c in range(raw.shape[1]):
                    cell = str(raw.iloc[r, c]).strip()
                    if "현 잔액" in cell and r + 1 < len(raw): st.session_state.summary_data["잔액"] = str(raw.iloc[r+1, c])
                    if "본전" in cell and "$" in cell and r + 1 < len(raw): st.session_state.summary_data["본전"] = str(raw.iloc[r+1, c])
                    if "수익" in cell and "누적" in cell and r + 1 < len(raw): st.session_state.summary_data["수익"] = str(raw.iloc[r+1, c])
                    if "총 투입금" in cell and r + 1 < len(raw): st.session_state.summary_data["투입"] = str(raw.iloc[r+1, c])
                    
                    if "1월" in cell and r + 2 < len(raw):
                        # 동적 열 처리: 데이터가 12개가 안 되더라도 에러 없이 가져옴
                        m_usd = [parse_money(x) for x in raw.iloc[r+1, c:c+12].tolist()]
                        m_krw = [parse_money(x) for x in raw.iloc[r+2, c:c+12].tolist()]
                        
                        # 부족한 달은 0.0으로 채워줌 (127 에러 방지 핵심)
                        m_usd += [0.0] * (12 - len(m_usd))
                        m_krw += [0.0] * (12 - len(m_krw))
                        
                        st.session_state.monthly_data["2026"] = pd.DataFrame(
                            [m_usd[:12], m_krw[:12]], 
                            columns=[f"{i}월" for i in range(1, 13)], index=["수익($)", "수익(₩)"]
                        )
                    
                    if cell == "종목명":
                        df = raw.iloc[r:].copy()
                        df.columns = df.iloc[0]; df = df[1:].reset_index(drop=True)
                        cols_to_drop = [x for x in df.columns if any(y in str(x).lower() for y in ['no', '비고2', 'unnamed'])]
                        st.session_state.main_df = df.drop(columns=cols_to_drop, errors='ignore').dropna(how='all')
            st.success("데이터 로드 완료!")
        except Exception as e: st.error(f"파일 로드 중 오류 발생: {e}")

    st.session_state.main_df = st.data_editor(st.session_state.main_df, num_rows="dynamic", use_container_width=True)
    csv_log = st.session_state.main_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 매매일지 다운로드", csv_log, "trading_log.csv", "text/csv")

with tab1:
    ca, cb, cc, cd = st.columns(4)
    s = st.session_state.summary_data
    safe_ex = cur_ex if cur_ex and cur_ex > 0 else 1442.5
    
    def m(col, l, val, krw):
        with col:
            st.caption(l)
            num = parse_money(val)
            usd_val = num if "본전" in l else num / safe_ex
            st.subheader(f"${usd_val:,.2f}")
            st.markdown(f"<p class='krw-label'>{krw}</p>", unsafe_allow_html=True)
    
    m(ca, "총 투입금", s.get('투입', '0'), s.get('투입', '₩0'))
    m(cb, "현재 잔액", s.get('잔액', '0'), s.get('잔액', '₩0'))
    m(cc, "누적 수익", s.get('수익', '0'), s.get('수익', '₩0'))
    m(cd, "본전 수익목표", s.get('본전', '0'), f"₩{parse_money(s.get('본전', '0'))*safe_ex:,.0f}")
    
    st.write("---")
    st.subheader("🗓️ 연도별 수익 현황 (두 줄 표기)")
    # 연도 선택 기능
    selected_year = st.selectbox("조회 연도", sorted(list(st.session_state.monthly_data.keys()), reverse=True))
    
    if selected_year in st.session_state.monthly_data:
        # 달러/원화 두 줄 표기 테이블
        st.table(st.session_state.monthly_data[selected_year].style.format("{:,.2f}"))
    
    if st.button("➕ 다음 연도 추가"):
        next_year = str(int(max(st.session_state.monthly_data.keys())) + 1)
        st.session_state.monthly_data[next_year] = pd.DataFrame(0.0, index=["수익($)", "수익(₩)"], columns=[f"{i}월" for i in range(1, 13)])
        st.rerun()

with tab3:
    st.subheader("💳 대출 & 상환 관리 (자동 합계)")
    st.info("💡 3자리마다 쉼표(,)가 표시되며 줄을 추가해도 데이터가 유지돼!")
    
    # 3자리 쉼표 표시 및 입력값 유지 설정
    st.session_state.loan_df = st.data_editor(
        st.session_state.loan_df, 
        num_rows="dynamic", 
        use_container_width=True,
        column_config={
            "대출금액": st.column_config.NumberColumn("대출금액", format="#,###"),
            "상환금액": st.column_config.NumberColumn("상환금액", format="#,###")
        },
        key="loan_editor_final_v11" # 고유 키를 사용해 상태 보존
    )
    
    t_l = st.session_state.loan_df['대출금액'].apply(parse_money).sum()
    t_r = st.session_state.loan_df['상환금액'].apply(parse_money).sum()
    
    st.markdown(f"""
    <div class="total-row">
        <div style="display: flex; justify-content: space-between;">
            <span>💰 총 대출액: ₩{t_l:,.0f}</span>
            <span style="color: blue;">✅ 총 상환액: ₩{t_r:,.0f}</span>
            <span style="color: #ff4b4b;">🚨 남은 잔액: ₩{t_l - t_r:,.0f}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    loan_csv = st.session_state.loan_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 대출내역 다운로드", loan_csv, "loan_history.csv", "text/csv")
