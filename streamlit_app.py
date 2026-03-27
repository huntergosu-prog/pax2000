import streamlit as st
import pandas as pd
import io
import re
from datetime import datetime, timedelta

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="팍스2000 통합 대시보드", layout="wide")
st.markdown("""
    <style>
    html, body, [class*="css"] { font-size: 13px !important; }
    div[data-testid="stMetricValue"] { font-size: 18px !important; font-weight: bold; }
    .krw-label { color: #ff4b4b; font-size: 12px; font-weight: bold; margin-top: -5px; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { height: 40px; white-space: pre-wrap; background-color: #f0f2f6; border-radius: 5px; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. 유틸리티 함수
def parse_money(val):
    if pd.isna(val) or str(val).strip() == "": return 0.0
    try: return float(re.sub(r'[^\d.-]', '', str(val)))
    except: return 0.0

# 3. 데이터 세션 초기화 (데이터 증발 방지 로직)
if 'main_df' not in st.session_state:
    st.session_state.main_df = pd.DataFrame(columns=["날짜", "종목명", "포지션", "매수가", "매도가", "수익", "비고"])
if 'loan_df' not in st.session_state:
    st.session_state.loan_df = pd.DataFrame([{"대출처": "KB라이프", "대출금액": 50000000, "상환금액": 0, "비고": ""}, {"대출처": "하나생명", "대출금액": 90000000, "상환금액": 0, "비고": ""}, {"대출처": "마이너스", "대출금액": 100000000, "상환금액": 0, "비고": ""}])

# 4. 상단 사이드바 (설정)
with st.sidebar:
    st.title("⚙️ 설정")
    cur_ex = st.number_input("현재 환율 (₩/$)", value=1514.50, step=0.1)
    st.divider()
    st.info("💡 데이터 저장 안내\n배포 환경에서는 새로고침 시 데이터가 초기화됩니다. 수정한 후에는 반드시 '매매일지' 탭 하단에서 CSV로 다운로드해두세요!")

# 5. 핵심: 실시간 통계 계산 로직 (데이터가 있든 없든 매번 계산)
def calculate_metrics():
    df = st.session_state.main_df
    # 수익 컬럼의 숫자를 모두 합산
    total_pnl_usd = df['수익'].apply(parse_money).sum()
    invested_krw = 40000000.0 # 무창 오빠의 원금
    
    current_pnl_krw = total_pnl_usd * cur_ex
    balance_krw = invested_krw + current_pnl_krw
    
    return invested_krw, balance_krw, current_pnl_krw, total_pnl_usd

# 데이터 계산 실행
inv_k, bal_k, pnl_k, pnl_u = calculate_metrics()

# 6. 메인 화면 구성
st.title("🚀 팍스2000: 130억 로드맵 통합 대시보드")

tab1, tab2, tab3 = st.tabs(["📊 자산 통계", "📝 실시간 매매일지", "💸 대출 & 상환"])

with tab1:
    c1, c2, c3, c4 = st.columns(4)
    with c1: 
        st.metric("총 투입금", f"₩{inv_k:,.0f}")
        st.caption(f"${inv_k/cur_ex:,.2f}")
    with c2: 
        st.metric("현재 잔액", f"₩{bal_k:,.0f}")
        st.caption(f"${bal_k/cur_ex:,.2f}")
    with c3: 
        delta_label = "Profit" if pnl_k >= 0 else "Loss"
        st.metric("누적 수익", f"₩{pnl_k:,.0f}", delta=f"${pnl_u:,.2f} ({delta_label})")
    with c4: 
        st.metric("로드맵 1단계 목표", "$50,000")
        st.markdown(f"<p class='krw-label'>남은 목표: ₩{(50000*cur_ex)-bal_k:,.0f}</p>", unsafe_allow_html=True)
    
    st.divider()
    st.subheader("🗓️ 월별 수익 통계 (자동 요약)")
    if not st.session_state.main_df.empty:
        # 월별 요약 로직 추가 가능
        st.info("매매일지에 데이터를 입력하면 실시간으로 합산됩니다.")

with tab2:
    st.subheader("📝 매매 기록 관리")
    
    # [업로드 로직]
    up_file = st.file_uploader("파일 로드 (trading_log.csv)", type=["csv"], label_visibility="collapsed")
    if up_file:
        try:
            content = up_file.getvalue().decode('utf-8-sig')
            st.session_state.main_df = pd.read_csv(io.StringIO(content)).fillna("")
            st.rerun()
        except Exception as e: st.error(f"파일 로드 에러: {e}")

    # [에디터] - 수정한 내용이 즉시 session_state에 저장됨
    edited_df = st.data_editor(
        st.session_state.main_df, 
        num_rows="dynamic", 
        use_container_width=True, 
        key="main_editor_v34"
    )
    
    # 에디터 내용이 바뀌면 즉시 업데이트
    if not edited_df.equals(st.session_state.main_df):
        st.session_state.main_df = edited_df
        st.rerun() # 즉시 재실행해서 통계에 반영

    st.divider()
    # [다운로드] - 클라우드에서는 이게 오빠의 '저장' 버튼이야!
    csv = st.session_state.main_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("💾 현재 데이터 PC에 저장 (CSV 다운로드)", csv, "trading_log.csv", "text/csv")

with tab3:
    st.subheader("💸 대출 & 상환 관리")
    edited_loan = st.data_editor(
        st.session_state.loan_df, 
        num_rows="dynamic", 
        use_container_width=True,
        column_config={
            "대출금액": st.column_config.NumberColumn("대출금액(₩)", format="%,d"),
            "상환금액": st.column_config.NumberColumn("상환금액(₩)", format="%,d")
        },
        key="loan_editor_v34"
    )
    if not edited_loan.equals(st.session_state.loan_df):
        st.session_state.loan_df = edited_loan
        st.rerun()
    
    tl = st.session_state.loan_df['대출금액'].apply(parse_money).sum()
    tr = st.session_state.loan_df['상환금액'].apply(parse_money).sum()
    st.info(f"💰 총 대출액: ₩{tl:,.0f} | ✅ 총 상환액: ₩{tr:,.0f} | 🚨 남은 잔액: ₩{tl-tr:,.0f}")
