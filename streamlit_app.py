import streamlit as st
import pandas as pd
import io

# 페이지 설정
st.set_page_config(page_title="팍스2000 통합 대시보드", layout="wide")

# 글자 크기 및 입력창 콤팩트하게 조절하는 CSS
st.markdown("""
    <style>
    html, body, [class*="css"]  { font-size: 13px !important; }
    div[data-testid="stMetricValue"] { font-size: 16px !important; }
    h1 { font-size: 20px !important; margin-bottom: 5px; }
    h3 { font-size: 15px !important; margin-top: 5px; }
    .stDataFrame { font-size: 12px !important; }
    /* 입력창 간격 줄이기 */
    div[data-testid="stVerticalBlock"] > div { gap: 0.1rem !important; }
    </style>
    """, unsafe_allow_html=True)

# 1. 최상단: 로드맵 및 환율 설정 (수정 가능)
st.title("🚀 팍스2000: 130억 로드맵 & 매매일지")

# 5개 컬럼으로 구성
c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    ex_rate = st.number_input("현재 환율", value=1442.50, step=0.1)
with c2:
    g1_p = st.text_input("1단계 목표", value="$50,000")
    g1_d = st.text_input("1단계 날짜", value="2026.03")
with c3:
    g2_p = st.text_input("2단계 목표", value="$200,000")
    g2_d = st.text_input("2단계 날짜", value="2026.05")
with c4:
    g3_p = st.text_input("3단계 목표", value="$2,000,000")
    g3_d = st.text_input("3단계 날짜", value="2026.07")
with c5:
    g4_p = st.text_input("4단계 목표", value="$10,000,000")
    g4_d = st.text_input("4단계 날짜", value="2026.12")

st.divider()

# 2. 자산 요약 현황
c1, c2, c3, c4 = st.columns(4)
c1.metric("총 투입금", "₩40,000,000")
c2.metric("현재 잔액", "₩18,012,969")
c3.metric("누적 수익", "-₩21,987,031", delta_color="inverse")
c4.metric("본전 수익목표", "$14,410.42")

st.divider()

# 3. 매매일지 (CSV 업로드 및 에디터)
st.subheader("📝 실시간 매매일지")
uploaded_file = st.file_uploader("CSV 불러오기", type=["csv"], label_visibility="collapsed")

if 'main_df' not in st.session_state:
    st.session_state.main_df = pd.DataFrame()

if uploaded_file:
    try:
        content = uploaded_file.getvalue().decode('utf-8-sig')
        lines = content.splitlines()
        header_idx = next((i for i, line in enumerate(lines) if "종목명" in line or "날짜" in line), 0)
        df = pd.read_csv(io.StringIO("\n".join(lines[header_idx:])))
        
        # 'NO' 또는 'no' 컬럼 삭제
        df = df.drop(columns=[col for col in df.columns if col.lower() == 'no'], errors='ignore')
        st.session_state.main_df = df
    except Exception as e:
        st.error(f"에러: {e}")

if not st.session_state.main_df.empty:
    edited_df = st.data_editor(st.session_state.main_df, num_rows="dynamic", use_container_width=True, height=450)
    if st.
