import streamlit as st
import pandas as pd
import io

# 1. 페이지 설정 및 레이아웃
st.set_page_config(page_title="팍스2000 통합 대시보드", layout="wide")

# 2. 콤팩트한 화면을 위한 CSS
st.markdown("""
    <style>
    html, body, [class*="css"] { font-size: 13px !important; }
    div[data-testid="stMetricValue"] { font-size: 16px !important; }
    h1 { font-size: 20px !important; margin-bottom: 5px; }
    h3 { font-size: 15px !important; margin-top: 10px; margin-bottom: 5px; }
    .stDataFrame { font-size: 12px !important; }
    div[data-testid="stVerticalBlock"] > div { gap: 0.1rem !important; }
    .stNumberInput, .stTextInput { margin-bottom: -15px !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. 타이틀
st.title("🚀 팍스2000: 130억 로드맵 & 매매일지")

# 4. 상단 대시보드: 목표가 및 날짜 (수정 가능)
c1, c2, c3, c4, c5 = st.columns(5)
with c1: ex_rate = st.number_input("현재 환율", value=1442.50, step=0.1)
with c2: 
    g1_p = st.text_input("1단계 목표", value="$50,000")
    g1_d = st.text_input("목표일1", value="2026.03")
with c3: 
    g2_p = st.text_input("2단계 목표", value="$200,000")
    g2_d = st.text_input("목표일2", value="2026.05")
with c4: 
    g3_p = st.text_input("3단계 목표", value="$2,000,000")
    g3_d = st.text_input("목표일3", value="2026.07")
with c5: 
    g4_p = st.text_input("4단계 목표", value="$10,000,000")
    g4_d = st.text_input("목표일4", value="2026.12")

st.divider()

# 5. 자산 요약 현황
col_a, col_b, col_c, col_d = st.columns(4)
col_a.metric("총 투입금", "₩40,000,000")
col_b.metric("현재 잔액", "₩18,012,969")
col_c.metric("누적 수익", "-₩21,987,031", delta_color="inverse")
col_d.metric("본전 목표", "$14,410.42")

st.divider()

# 6. 매매일지 섹션 (입출금 내역 보존 로직)
st.subheader("📝 실시간 매매일지 (입출금 포함)")

uploaded_file = st.file_uploader("CSV 업로드", type=["csv"], label_visibility="collapsed")

if 'main_df' not in st.session_state:
    st.session_state.main_df = pd.DataFrame()

if uploaded_file:
    try:
        content = uploaded_file.getvalue().decode('utf-8-sig')
        lines = content.splitlines()
        # '종목명'이나 '날짜'가 포함된 진짜 헤더 줄 찾기
        header_idx = next((i for i, line in enumerate(lines) if "종목명" in line or "날짜" in line), 0)
        
        # 데이터를 읽어올 때 'NO' 컬럼은 제외하고 모든 행을 가져옴
        df = pd.read_csv(io.StringIO("\n".join(lines[header_idx:])))
        df = df.drop(columns=[col for col in df.columns if col.lower() == 'no'], errors='ignore')
        
        # 완전히 비어있는 행만 삭제 (중간에 내용이 있는 행은 보존)
        df = df.dropna(how='all')
        
        st.session_state.main_df = df
        st.success("데이터 로드 완료! 입출금 내역도 모두 포함됐어.")
    except Exception as e:
        st.error(f"파일 읽기 에러: {e}")

# 에디터 표시
if not st.session_state.main_df.empty:
    # 모든 컬럼을 편집 가능하게 설정 (입출금 메모 작성을 위해)
    edited_df = st.data_editor(
        st.session_state.main_df, 
        num_rows="dynamic", 
        use_container_width=True, 
        height=600 
    )
    
    if st.button("💾 변경사항 화면에 반영하기"):
        st.session_state.main_df = edited_df
        st.success("업데이트 완료!")
else:
    st.info("파일을 올려주면 입출금을 포함한 전체 일지가 뜰 거야.")
