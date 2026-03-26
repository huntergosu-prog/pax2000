import streamlit as st
import pandas as pd

st.set_page_config(page_title="팍스2000 매미일지", layout="wide")

st.title("📊 팍스2000: 130억 부자의 매미일지")
st.info("회사랑 집 어디서든 브라우저로 접속해서 기록해!")

# 샘플 데이터 (나중에 DB랑 연결할 거야)
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame([
        {"날짜": "2026-03-26", "종목": "SOL", "포지션": "Short", "진입가": 86.512, "현재가": 90.1, "PNL": -41.6}
    ])

# 엑셀처럼 수정 가능한 테이블
edited_df = st.data_editor(st.session_state.df, num_rows="dynamic", use_container_width=True)

if st.button("💾 데이터 임시 저장 (브라우저 세션)"):
    st.session_state.df = edited_df
    st.success("일단 화면에 저장됐어! 나중에 서버 저장 기능 추가하자.")
