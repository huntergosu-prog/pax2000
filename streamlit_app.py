import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="팍스2000 통합 대시보드", layout="wide")

# 1. 최상단: 로드맵 및 환율 설정 (오빠의 엑셀 상단 양식)
st.title("🚀 팍스2000: 130억 로드맵 & 매매일지")

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    ex_rate = st.number_input("현재 환율(₩)", value=1442.50)
with col2:
    st.metric("1단계 ($50,000)", "2026.03")
with col3:
    st.metric("2단계 ($200,000)", "2026.05")
with col4:
    st.metric("3단계 ($2,000,000)", "2026.07")
with col5:
    st.metric("4단계 ($10,000,000)", "2026.12")

st.divider()

# 2. 중간: 자산 요약 현황
c1, c2, c3, c4 = st.columns(4)
c1.metric("총 투입금", "₩40,000,000")
c2.metric("현재 잔액", "₩18,012,969")
c3.metric("누적 수익", "-₩21,987,031", delta_color="inverse")
c4.metric("본전 수익목표", "$14,410.42")

st.divider()

# 3. 하단: 매매일지 (CSV 업로드 및 에디터)
st.subheader("📝 실시간 매매일지 기록")

# 파일 업로드 기능을 일지 바로 위에 배치
uploaded_file = st.file_uploader("과거 매매일지(CSV) 불러오기", type=["csv"])

if 'main_df' not in st.session_state:
    st.session_state.main_df = pd.DataFrame()

if uploaded_file:
    try:
        content = uploaded_file.getvalue().decode('utf-8-sig')
        lines = content.splitlines()
        # '종목명'이 있는 줄부터 데이터로 인식하는 지능형 로직
        header_idx = next((i for i, line in enumerate(lines) if "종목명" in line or "날짜" in line), 0)
        st.session_state.main_df = pd.read_csv(io.StringIO("\n".join(lines[header_idx:])))
        st.success("데이터 로드 완료!")
    except Exception as e:
        st.error(f"에러 발생: {e}")

# 에디터 띄우기 (데이터가 없어도 빈 양식 출력)
if not st.session_state.main_df.empty:
    edited_df = st.data_editor(st.session_state.main_df, num_rows="dynamic", use_container_width=True)
    if st.button("💾 변경사항 저장하기 (임시)"):
        st.session_state.main_df = edited_df
        st.success("화면 데이터가 업데이트됐어!")
else:
    st.info("아직 데이터가 없어. 왼쪽이나 위에서 CSV 파일을 올려주면 여기에 일지가 뜰 거야!")

# 4. 맨 아래: 출금 및 대출 간단 요약
with st.expander("💳 대출 및 출금 현황 상세보기"):
    st.table(pd.DataFrame({
        "대출처": ["KB라이프", "하나생명", "마이너스통장"],
        "금액": ["₩10,000,000", "₩5,000,000", "₩20,000,000"]
    }))
