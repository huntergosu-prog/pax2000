import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="팍스2000 종합 대시보드", layout="wide")

# 1. 상단 대시보드 (환율 및 로드맵)
st.title("🚀 팍스2000: 130억 로드맵 관리 시스템")

# 환율 및 목표 설정 구역
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    exchange_rate = st.number_input("현재 환율(₩)", value=1442.50)
with col2:
    st.metric("1단계 목표", "$50,000", "2026.03")
with col3:
    st.metric("2단계 목표", "$200,000", "2026.05")
with col4:
    st.metric("3단계 목표", "$2,000,000", "2026.07")
with col5:
    st.metric("4단계 목표", "$10,000,000", "2026.12")

st.divider()

# 2. 탭 기능으로 메뉴 분리 (통계, 매매일지, 출금내역)
tab1, tab2, tab3 = st.tabs(["📊 월별 통계 & 자산 현황", "📝 실시간 매매일지", "💸 출금 & 대출 관리"])

with tab1:
    st.subheader("🗓️ 월별 수익 통계")
    # 오빠 엑셀의 월별 데이터를 담을 표 (예시)
    monthly_data = pd.DataFrame({
        "월": ["1월", "2월", "3월", "4월", "5월", "6월"],
        "수익(달러)": [1500, -2000, 3500, 0, 0, 0],
        "수익(원화)": [2163750, -2885000, 5048750, 0, 0, 0]
    })
    st.dataframe(monthly_data, use_container_width=True)
    
    st.subheader("🏠 자산 요약")
    c1, c2, c3 = st.columns(3)
    c1.info("총 투입금: ₩40,000,000")
    c2.warning("현재 잔액: ₩18,012,969")
    c3.error("누적 수익: -₩21,987,031")

with tab2:
    st.subheader("📉 선물 매매 기록")
    # 기존 매매일지 로직 유지
    uploaded_file = st.file_uploader("엑셀(CSV) 업로드", type=["csv"], key="trade_log")
    if 'trade_df' not in st.session_state:
        st.session_state.trade_df = pd.DataFrame()

    if uploaded_file:
        content = uploaded_file.getvalue().decode('utf-8-sig')
        lines = content.splitlines()
        header_idx = next((i for i, line in enumerate(lines) if "종목명" in line or "날짜" in line), 0)
        st.session_state.trade_df = pd.read_csv(io.StringIO("\n".join(lines[header_idx:])))
    
    if not st.session_state.trade_df.empty:
        st.data_editor(st.session_state.trade_df, num_rows="dynamic", use_container_width=True)

with tab3:
    st.subheader("💳 출금 및 대출 현황")
    loan_df = pd.DataFrame({
        "구분": ["KB라이프", "하나생명", "마이너스통장"],
        "금액": ["₩10,000,000", "₩5,000,000", "₩20,000,000"],
        "비고": ["보험약관대출", "신용대출", "생활비"]
    })
    st.table(loan_df)
