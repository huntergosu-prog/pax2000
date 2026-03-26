import streamlit as st
import pandas as pd
import io
import re

# 1. 페이지 설정
st.set_page_config(page_title="팍스2000 통합 대시보드", layout="wide")

# 2. 콤팩트 CSS (글자 크기 축소 및 간격 조절)
st.markdown("""
    <style>
    html, body, [class*="css"] { font-size: 13px !important; }
    div[data-testid="stMetricValue"] { font-size: 16px !important; }
    h1 { font-size: 20px !important; margin-bottom: 5px; }
    h3 { font-size: 15px !important; margin-top: 10px; }
    .stDataFrame { font-size: 12px !important; }
    .krw-text { color: #ff4b4b; font-size: 11px; font-weight: bold; margin-top: -10px; }
    </style>
    """, unsafe_allow_html=True)

# 금액 문자열에서 숫자만 추출하는 함수
def parse_money(money_str):
    try:
        return float(re.sub(r'[^\d.]', '', money_str))
    except:
        return 0.0

# 3. 최상단: 공통 설정
st.title("🚀 팍스2000: 130억 로드맵 관리 시스템")

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    ex_rate = st.number_input("현재 환율(₩)", value=1442.50, step=0.1)

# 목표 설정 및 원화 자동 계산
def goal_col(col, label, default_p, default_d):
    with col:
        p = st.text_input(f"{label} 목표($)", value=default_p)
        d = st.text_input(f"{label} 날짜", value=default_d)
        krw_val = parse_money(p) * ex_rate
        st.markdown(f"<p class='krw-text'>≈ ₩{krw_val:,.0f}</p>", unsafe_allow_html=True)
    return p, d

g1_p, g1_d = goal_col(c2, "1단계", "$50,000", "2026.03")
g2_p, g2_d = goal_col(c3, "2단계", "$200,000", "2026.05")
g3_p, g3_d = goal_col(c4, "3단계", "$2,000,000", "2026.07")
g4_p, g4_d = goal_col(c5, "4단계", "$10,000,000", "2026.12")

st.divider()

# 4. 탭 구성
tab1, tab2, tab3 = st.tabs(["📊 자산 현황 & 통계", "📝 실시간 매매일지", "💸 출금 & 대출 관리"])

with tab1:
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("총 투입금", "₩40,000,000")
    col_b.metric("현재 잔액", "₩18,012,969")
    col_c.metric("누적 수익", "-₩21,987,031", delta_color="inverse")
    col_d.metric("본전 목표", "$14,410.42")
    
    st.write("---")
    st.subheader("🗓️ 월별 수익 요약")
    monthly_summary = pd.DataFrame({
        "구분": ["1월", "2월", "3월", "합계"],
        "수익(달러)": ["$1,908", "-$6,694", "$0", "-$4,786"],
        "수익(원화)": ["₩2,752,527", "-₩9,656,989", "₩0", "-₩6,904,462"]
    })
    st.table(monthly_summary)

with tab2:
    st.subheader("📉 선물 매매 기록 (입출금 포함)")
    uploaded_file = st.file_uploader("CSV 업로드", type=["csv"], label_visibility="collapsed")
    
    if 'main_df' not in st.session_state:
        st.session_state.main_df = pd.DataFrame()

    if uploaded_file:
        try:
            content = uploaded_file.getvalue().decode('utf-8-sig')
            lines = content.splitlines()
            header_idx = next((i for i, line in enumerate(lines) if "종목명" in line or "날짜" in line), 0)
            df = pd.read_csv(io.StringIO("\n".join(lines[header_idx:])))
            
            # NO, 비고2 컬럼 삭제
            cols_to_drop = [c for c in df.columns if c.lower() in ['no', '비고2']]
            df = df.drop(columns=cols_to_drop, errors='ignore')
            
            st.session_state.main_df = df.dropna(how='all')
            st.success("데이터 로드 완료!")
        except Exception as e:
            st.error(f"파일 에러: {e}")

    if not st.session_state.main_df.empty:
        edited_df = st.data_editor(st.session_state.main_df, num_rows="dynamic", use_container_width=True, height=550)
        if st.button("💾 변경사항 저장"):
            st.session_state.main_df = edited_df
            st.success("업데이트 성공!")

with tab3:
    st.subheader("💳 대출 및 출금 현황")
    loan_data = pd.DataFrame({
        "대출처": ["KB라이프", "하나생명", "마이너스통장"],
        "금액": ["₩10,000,000", "₩5,000,000", "₩20,000,000"],
        "비고": ["보험약관대출", "신용대출", "생활비"]
    })
    st.table(loan_data)
