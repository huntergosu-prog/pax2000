import streamlit as st
import pandas as pd
import io

# 1. 페이지 설정 및 레이아웃
st.set_page_config(page_title="팍스2000 통합 대시보드", layout="wide")

# 2. 콤팩트한 화면을 위한 CSS (글자 크기 축소)
st.markdown("""
    <style>
    html, body, [class*="css"] { font-size: 13px !important; }
    div[data-testid="stMetricValue"] { font-size: 16px !important; }
    div[data-testid="stMetricLabel"] { font-size: 11px !important; }
    h1 { font-size: 20px !important; margin-bottom: 5px; }
    h3 { font-size: 15px !important; margin-top: 10px; margin-bottom: 5px; }
    .stDataFrame { font-size: 12px !important; }
    /* 입력창 간격 및 크기 조절 */
    div[data-testid="stVerticalBlock"] > div { gap: 0.1rem !important; }
    .stNumberInput, .stTextInput { margin-bottom: -15px !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. 타이틀
st.title("🚀 팍스2000: 130억 로드맵 & 매매일지")

# 4. 상단 대시보드: 환율 및 로드맵 목표 (수정 가능)
c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    ex_rate = st.number_input("현재 적용 환율", value=1442.50, step=0.1)
with c2:
    g1_p = st.text_input("1단계 목표가", value="$50,000")
    g1_d = st.text_input("1단계 목표일", value="2026.03")
with c3:
    g2_p = st.text_input("2단계 목표가", value="$200,000")
    g2_d = st.text_input("2단계 목표일", value="2026.05")
with c4:
    g3_p = st.text_input("3단계 목표가", value="$2,000,000")
    g3_d = st.text_input("3단계 목표일", value="2026.07")
with c5:
    g4_p = st.text_input("4단계 목표가", value="$10,000,000")
    g4_d = st.text_input("4단계 목표일", value="2026.12")

st.divider()

# 5. 자산 요약 현황 (오빠 엑셀 기준 데이터)
col_a, col_b, col_c, col_d = st.columns(4)
col_a.metric("총 투입금", "₩40,000,000")
col_b.metric("현재 잔액", "₩18,012,969")
col_c.metric("누적 수익", "-₩21,987,031", delta_color="inverse")
col_d.metric("본전 수익목표", "$14,410.42")

st.divider()

# 6. 매매일지 섹션
st.subheader("📝 실시간 매매일지")

# 파일 업로드 (라벨 숨김으로 깔끔하게)
uploaded_file = st.file_uploader("CSV 업로드", type=["csv"], label_visibility="collapsed")

# 세션 상태에 데이터 프레임 저장
if 'main_df' not in st.session_state:
    st.session_state.main_df = pd.DataFrame()

# 파일 업로드 시 처리 로직
if uploaded_file:
    try:
        content = uploaded_file.getvalue().decode('utf-8-sig')
        lines = content.splitlines()
        # '종목명'이나 '날짜'가 포함된 줄을 헤더로 인식
        header_idx = next((i for i, line in enumerate(lines) if "종목명" in line or "날짜" in line), 0)
        df = pd.read_csv(io.StringIO("\n".join(lines[header_idx:])))
        
        # 'NO' 또는 'no' 컬럼은 오빠 요청대로 삭제
        df = df.drop(columns=[col for col in df.columns if col.lower() == 'no'], errors='ignore')
        
        # 불필요한 빈 행이나 빈 열 정리
        df = df.dropna(how='all', axis=0).dropna(how='all', axis=1)
        
        st.session_state.main_df = df
    except Exception as e:
        st.error(f"파일을 읽는 중 에러가 발생했어: {e}")

# 에디터 표시
if not st.session_state.main_df.empty:
    edited_df = st.data_editor(
        st.session_state.main_df, 
        num_rows="dynamic", 
        use_container_width=True, 
        height=500  # 일지를 더 많이 볼 수 있게 높이 조절
    )
    
    if st.button("💾 변경사항 화면에 반영하기"):
        st.session_state.main_df = edited_df
        st.success("화면 데이터가 업데이트됐어, 오빠!")
else:
    st.info("왼쪽 상단의 'Browse files' 버튼을 눌러 오빠의 매매일지(CSV)를 올려줘.")

# 7. 하단 대출 및 기타 현황 (선택 사항)
with st.expander("💳 대출 현황 및 월별 통계 보기"):
    st.write("대출처: KB라이프(₩10M), 하나생명(₩5M), 마통(₩20M)")
    st.write("3월 말 목표까지 파이팅이야!")
