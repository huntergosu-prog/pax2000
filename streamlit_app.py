import streamlit as st
import pandas as pd

st.set_page_config(page_title="교수의 매매일지", layout="wide")

st.title("📊 교수의 하이퍼리퀴드 선물 매매일지")

# 1. 과거 데이터 파일 업로드 기능
st.sidebar.header("📂 데이터 관리")
uploaded_file = st.sidebar.file_uploader("과거 내역(CSV) 올리기", type=["csv"])

if 'df' not in st.session_state:
    # 초기 데이터 (오빠의 양식 기준)
    st.session_state.df = pd.DataFrame(columns=[
        "날짜", "코인명", "포지션", "레버리지", "매수가", "매도가", 
        "수량", "수수료", "투자금", "실 수익금", "수익률(%)", "수익(원화)", "비고"
    ])

# 파일 업로드 시 데이터 합치기
if uploaded_file is not None:
    old_data = pd.read_csv(uploaded_file)
    st.session_state.df = pd.concat([st.session_state.df, old_data]).drop_duplicates()
    st.sidebar.success("과거 내역 로드 완료!")

# 2. 계산 로직 (숏/롱 구분)
def calculate_all(df):
    for i, row in df.iterrows():
        try:
            p = 1 if row["포지션"] == "Long" else -1
            # (매도가 - 매수가) * 수량 * 방향 - 수수료
            net_profit = ((float(row["매도가"]) - float(row["매수가"])) * float(row["수량"]) * p) - float(row["수수료"])
            df.at[i, "실 수익금"] = round(net_profit, 2)
            df.at[i, "수익률(%)"] = round((net_profit / float(row["투자금"])) * 100, 2)
            df.at[i, "수익(원화)"] = int(net_profit * 1400) # 환율 1400원 가정
        except:
            continue
    return df

# 3. 엑셀형 에디터
edited_df = st.data_editor(st.session_state.df, num_rows="dynamic", use_container_width=True)

if st.button("💾 계산하기 및 임시 저장"):
    st.session_state.df = calculate_all(edited_df)
    st.rerun()
