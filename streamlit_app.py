import streamlit as st
import pandas as pd
import io
import re
from datetime import datetime

# yfinance 안전 로드
try:
    import yfinance as yf
    YF_AVAILABLE = True
except ImportError:
    YF_AVAILABLE = False

st.set_page_config(page_title="팍스2000 통합 대시보드", layout="wide")

# 1. 콤팩트 디자인 CSS
st.markdown("""
    <style>
    html, body, [class*="css"] { font-size: 13px !important; }
    div[data-testid="stMetricValue"] { font-size: 16px !important; }
    h1 { font-size: 20px !important; margin-bottom: 5px; }
    .krw-label { color: #ff4b4b; font-size: 12px; font-weight: bold; margin-top: -5px; margin-bottom: 5px; }
    .update-time { font-size: 10px; color: #888; margin-top: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 2. 환율 함수 (4시간 캐시)
@st.cache_data(ttl=14400)
def get_exchange_rate():
    if not YF_AVAILABLE: return 1442.50, "라이브러리 미설치"
    try:
        ticker = yf.Ticker("USDKRW=X")
        data = ticker.history(period="1d")
        rate = round(data['Close'].iloc[-1], 2)
        fetch_time = datetime.now().strftime("%m/%d %H:%M")
        return rate, fetch_time
    except: return 1442.50, "연결 에러"

def parse_money(money_str):
    try: return float(re.sub(r'[^\d.]', '', str(money_str)))
    except: return 0.0

# 3. 최상단: 대시보드
st.title("🚀 팍스2000: 130억 로드맵 관리 시스템")

current_rate, last_update = get_exchange_rate()

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    if st.button("🔄 환율 갱신"):
        st.cache_data.clear()
        st.rerun()
    ex_rate = st.number_input(f"현재 환율", value=current_rate, step=0.1)
    st.markdown(f"<p class='update-time'>최종 동기화: {last_update}</p>", unsafe_allow_html=True)

def goal_box(col, label, def_p, def_d):
    with col:
        p_val = st.text_input(f"{label} 목표($)", value=def_p)
        krw = parse_money(p_val) * ex_rate
        st.markdown(f"<p class='krw-label'>≈ ₩{krw:,.0f}</p>", unsafe_allow_html=True)
        st.text_input(f"{label} 날짜", value=def_d, key=f"d_{label}")

goal_box(c2, "1단계", "$50,000", "2026.03")
goal_box(c3, "2단계", "$200,000", "2026.05")
goal_box(c4, "3단계", "$2,000,000", "2026.07")
goal_box(c5, "4단계", "$10,000,000", "2026.12")

st.divider()

# 자산 요약 (고정 데이터)
ca, cb, cc, cd = st.columns(4)
def asset_metric(col, label, usd_val):
    with col:
        st.caption(label)
        st.subheader(f"${usd_val:,.2f}")
        st.markdown(f"<p class='krw-label'>₩{usd_val * ex_rate:,.0f}</p>", unsafe_allow_html=True)

asset_metric(ca, "총 투입금", 40000000 / ex_rate)
asset_metric(cb, "현재 잔액", 18012969 / ex_rate)
asset_metric(cc, "누적 수익", -21987031 / ex_rate)
asset_metric(cd, "본전 수익목표", 14410.42)

st.divider()

# 4. 탭 구성
tab1, tab2, tab3 = st.tabs(["📊 자산 통계", "📝 실시간 매매일지", "💸 출금 & 대출"])

with tab2:
    st.subheader("📉 선물 매매 기록")
    uploaded_file = st.file_uploader("CSV 업로드", type=["csv"], label_visibility="collapsed")
    
    if 'main_df' not in st.session_state: st.session_state.main_df = pd.DataFrame()

    if uploaded_file:
        try:
            content = uploaded_file.getvalue().decode('utf-8-sig')
            lines = content.splitlines()
            
            # 진짜 헤더 찾기: '종목명'이 포함된 줄을 찾음 (상단 요약과 겹치지 않게)
            header_idx = -1
            for i, line in enumerate(lines):
                # '종목명'이 있고, 그 줄에 '매수가'나 '매도가'가 같이 있으면 진짜 일지 헤더임
                if "종목명" in line and ("매수가" in line or "매도가" in line):
                    header_idx = i
                    break
            
            if header_idx != -1:
                df = pd.read_csv(io.StringIO("\n".join(lines[header_idx:])))
                # 불필요한 컬럼 삭제
                cols_to_drop = [c for c in df.columns if any(x in c.lower() for x in ['no', '비고2', 'unnamed'])]
                df = df.drop(columns=cols_to_drop, errors='ignore')
                # 데이터가 없는 빈 행 삭제
                st.session_state.main_df = df.dropna(how='all')
                st.success("일지만 쏙 골라왔어!")
            else:
                st.error("매매일지 양식을 찾을 수 없어. '종목명' 헤더가 있는지 확인해 줘!")
        except Exception as e:
            st.error(f"에러 발생: {e}")

    if not st.session_state.main_df.empty:
        # 탭(Tab) 구분자 데이터를 바로 붙여넣기 좋게 에디터 설정
        edited_df = st.data_editor(st.session_state.main_df, num_rows="dynamic", use_container_width=True, height=550)
        if st.button("💾 데이터 저장"):
            st.session_state.main_df = edited_df
            st.success("업데이트 완료!")
