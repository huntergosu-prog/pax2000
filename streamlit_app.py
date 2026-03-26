import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="팍스2000 종합 대시보드", layout="wide")

# 1. 상단 타이틀 및 로드맵 정보
st.title("🚀 팍스2000: 130억 로드맵 관리 시스템")

# 환율은 오빠가 직접 입력하거나 나중에 자동화 가능
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    ex_rate = st.number_input("현재 적용 환율(₩)", value=1442.50)
with col2:
    st.metric("1단계 목표 (26.03)", "$50,000")
with col3:
    st.metric("2단계 목표 (26.05)", "$200,000")
with col4:
    st.metric("3단계 목표 (26.07)", "$2,000,000")
with col5:
    st.metric("4단계 목표 (26.12)", "$10,000,000")

st.divider()

# 2. 메뉴 구성 (통계, 매매일지, 대출/출금)
tab1, tab2, tab3 = st.tabs(["📊 자산 현황 & 통계", "📝 실시간 매매일지", "💳 대출 및 출금 관리"])

with tab1:
    st.subheader("🗓️ 월별 수익 및 자산 요약")
    # 오빠 엑셀에 있던 요약 정보를 화면에 배치
    c1, c2, c3 = st.columns(3)
    c1.metric("총 투입금", "₩40,000,000")
    c2.metric("현재 잔액", "₩18,012,969", "-₩21,987,031", delta_color="inverse")
    c3.metric("본전 수익목표($)", "$14,410.42")
    
    st.write("---")
    st.subheader("📈 월별 수익 통계 (예시 데이터)")
    # 나중에 이 부분도 DB랑 연결하면 자동으로 그려져
    monthly_summary = pd.DataFrame({
        "구분": ["1월", "2월", "3월", "합계"],
        "수익(달러)": ["$1,908", "-$6,694", "$0", "-$4,786"],
        "수익(원화)": ["₩2,752,527", "-₩9,656,989", "₩0", "-₩6,904,462"]
    })
    st.table(monthly_summary)

with tab2:
    st.subheader("📉 선물 매매 기록 (CSV 업로드)")
    uploaded_file = st.file_uploader("오빠의 원본 CSV 파일 선택", type=["csv"])
    
    if 'trade_df' not in st.session_state:
        st.session_state.trade_df = pd.DataFrame()

    if uploaded_file:
        content = uploaded_file.getvalue().decode('utf-8-sig')
        lines = content.splitlines()
        # '종목명'이 있는 줄부터 데이터로 인식
        header_idx = next((i for i, line in enumerate(lines) if "종목명" in line), 0)
        st.session_state.trade_df = pd.read_csv(io.StringIO("\n".join(lines[header_idx:])))
        st.success("데이터를 성공적으로 불러왔어!")

    if not st.session_state.trade_df.empty:
        st.data_editor(st.session_state.trade_df, num_rows="dynamic", use_container_width=True)

with tab3:
    st.subheader("💸 출금 내역 및 대출 현황")
    loan_data = pd.DataFrame({
        "대출처": ["KB라이프", "하나생명", "마이너스통장"],
        "금액": ["₩10,000,000", "₩5,000,000", "₩20,000,000"],
        "이율": ["4.5%", "5.2%", "6.0%"],
        "비고": ["보험약관대출", "신용대출", "생활비"]
    })
    st.table(loan_data)
