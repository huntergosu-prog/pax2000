import streamlit as st
import pandas as pd

st.set_page_config(page_title=" 매미일지", layout="wide")
st.title("📊 선물 매매일지")

# 1. 사이트에서 기본으로 쓸 컬럼 목록
expected_cols = ["날짜", "코인명", "포지션", "레버리지", "매수가", "매도가", "수량", "수수료", "투자금", "실 수익금", "수익률(%)", "수익(원화)", "비고"]

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=expected_cols)

# 2. 업로드 기능 개선 (에러 방지용)
uploaded_file = st.sidebar.file_uploader("과거 내역(CSV) 올리기", type=["csv"])

if uploaded_file:
    try:
        new_data = pd.read_csv(uploaded_file)
        # 엑셀에 없는 칸은 빈칸으로 채워서 합치기
        for col in expected_cols:
            if col not in new_data.columns:
                new_data[col] = None
        
        st.session_state.df = pd.concat([st.session_state.df, new_data[expected_cols]]).reset_index(drop=True)
        st.sidebar.success("성공적으로 불러왔어!")
    except Exception as e:
        st.sidebar.error(f"에러 발생: {e}")

# 3. 계산 함수 (수식 보강)
def run_calc(df):
    for i, row in df.iterrows():
        try:
            # 필수 값들이 있는지 확인
            if pd.isna(row["매수가"]) or pd.isna(row["매도가"]): continue
            
            p = 1 if row["포지션"] == "Long" else -1
            net_profit = ((float(row["매도가"]) - float(row["매수가"])) * float(row["수량"]) * p) - float(row.get("수수료", 0))
            
            df.at[i, "실 수익금"] = round(net_profit, 2)
            if float(row["투자금"]) > 0:
                df.at[i, "수익률(%)"] = round((net_profit / float(row["투자금"])) * 100, 2)
            df.at[i, "수익(원화)"] = int(net_profit * 1400)
        except: continue
    return df

edited_df = st.data_editor(st.session_state.df, num_rows="dynamic", use_container_width=True)

if st.button("💾 전체 계산 및 저장"):
    st.session_state.df = run_calc(edited_df)
    st.rerun()
