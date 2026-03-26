import streamlit as st
import pandas as pd

st.set_page_config(page_title="gosu의 매매일지", layout="wide")

st.title("📊 고수의 하이퍼리퀴드 매매일지")
st.caption("엑셀 양식을 그대로 옮겼어. 매도가만 수정하면 수익이 자동 계산돼!")

# 환율 설정 (오빠가 원할 때 수정 가능)
EXCHANGE_RATE = 1400 

# 데이터 초기화 (오빠의 실제 데이터 예시)
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame([
        {
            "날짜": "2026-03-26", "코인명": "SOL", "포지션": "Short", "레버리지": 10,
            "매수가": 86.512, "매도가": 89.378, "수량": 1000, "수수료": 50.0, "투자금": 9433.73,
            "실 수익금": 0.0, "수익률(%)": 0.0, "수익(원화)": 0, "비고": "유럽 개장 전 하락 중"
        }
    ])

# 계산 로직 함수
def calculate_pnl(df):
    for i, row in df.iterrows():
        # Short 포지션: (진입가 - 현재가) * 수량 - 수수료
        # Long 포지션: (현재가 - 진입가) * 수량 - 수수료
        diff = (row["매수가"] - row["매도가"]) if row["포지션"] == "Short" else (row["매도가"] - row["매수가"])
        net_profit = (diff * row["수량"]) - row["수수료"]
        
        df.at[i, "실 수익금"] = round(net_profit, 2)
        df.at[i, "수익률(%)"] = round((net_profit / row["투자금"]) * 100, 2) if row["투자금"] > 0 else 0
        df.at[i, "수익(원화)"] = int(net_profit * EXCHANGE_RATE)
    return df

# 엑셀형 에디터
edited_df = st.data_editor(
    st.session_state.df, 
    num_rows="dynamic", 
    use_container_width=True,
    column_config={
        "실 수익금": st.column_config.NumberColumn(disabled=True),
        "수익률(%)": st.column_config.NumberColumn(disabled=True),
        "수익(원화)": st.column_config.NumberColumn(disabled=True),
        "포지션": st.column_config.SelectboxColumn(options=["Long", "Short"])
    }
)

# 데이터 업데이트 및 저장 버튼
if st.button("💾 계산하기 및 저장"):
    st.session_state.df = calculate_pnl(edited_df)
    st.success("계산 완료! 수익(원화) 칸을 확인해 봐 오빠.")
    st.rerun()
