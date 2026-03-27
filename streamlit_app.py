import streamlit as st
import pandas as pd
import sqlite3
import re
from datetime import datetime, timedelta

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="팍스2000 통합 대시보드", layout="wide")
st.markdown("""
    <style>
    html, body, [class*="css"] { font-size: 13px !important; }
    div[data-testid="stMetricValue"] { font-size: 16px !important; }
    .total-row { background-color: #f8f9fa; font-weight: bold; border-top: 2px solid #ff4b4b; padding: 15px; border-radius: 8px; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터베이스 연동 (SQLite)
DB_FILE = 'trading_data.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # 매매일지 테이블
    c.execute('''CREATE TABLE IF NOT EXISTS trades 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, asset TEXT, position TEXT, buy_price TEXT, sell_price TEXT, pnl TEXT, note TEXT)''')
    # 대출 관리 테이블
    c.execute('''CREATE TABLE IF NOT EXISTS loans 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, lender TEXT, loan_amt REAL, repay_amt REAL, note TEXT)''')
    conn.commit()
    conn.close()

def load_trades():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT date, asset, position, buy_price, sell_price, pnl, note FROM trades", conn)
    conn.close()
    if df.empty:
        return pd.DataFrame(columns=["날짜", "종목명", "포지션", "매수가", "매도가", "수익", "비고"])
    df.columns = ["날짜", "종목명", "포지션", "매수가", "매도가", "수익", "비고"]
    return df

def save_trades(df):
    conn = sqlite3.connect(DB_FILE)
    df.to_sql('trades', conn, if_exists='replace', index=False)
    conn.close()

def load_loans():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT lender, loan_amt, repay_amt, note FROM loans", conn)
    conn.close()
    if df.empty:
        return pd.DataFrame([{"대출처": "KB라이프", "대출금액": 50000000.0, "상환금액": 0.0, "비고": ""}, {"대출처": "하나생명", "대출금액": 90000000.0, "상환금액": 0.0, "비고": ""}, {"대출처": "마이너스", "대출금액": 100000000.0, "상환금액": 0.0, "비고": ""}])
    df.columns = ["대출처", "대출금액", "상환금액", "비고"]
    return df

def save_loans(df):
    conn = sqlite3.connect(DB_FILE)
    df.to_sql('loans', conn, if_exists='replace', index=False)
    conn.close()

# 3. 초기화 및 세션 로드
init_db()
if 'main_df' not in st.session_state: st.session_state.main_df = load_trades()
if 'loan_df' not in st.session_state: st.session_state.loan_df = load_loans()

# 4. 유틸리티 함수
def parse_money(val):
    if pd.isna(val) or str(val).strip() == "": return 0.0
    try: return float(re.sub(r'[^\d.-]', '', str(val)))
    except: return 0.0

# 5. 메인 로직
cur_ex = st.sidebar.number_input("현재 환율", value=1514.50, step=0.1)

tab1, tab2, tab3 = st.tabs(["📊 자산 통계", "📝 실시간 매매일지", "💸 대출 & 상환"])

with tab2:
    st.subheader("📝 매매 기록 (자동 저장 중)")
    # 데이터 에디터 - 수정 즉시 DB 저장
    edited_trades = st.data_editor(st.session_state.main_df, num_rows="dynamic", use_container_width=True, key="trade_editor")
    
    if not edited_trades.equals(st.session_state.main_df):
        save_trades(edited_trades)
        st.session_state.main_df = edited_trades
        st.rerun()

with tab1:
    df = st.session_state.main_df
    total_pnl_usd = df['수익'].apply(parse_money).sum()
    invested_krw = 40000000.0 # 고정값 또는 필요시 DB화
    
    current_pnl_krw = total_pnl_usd * cur_ex
    balance_krw = invested_krw + current_pnl_krw
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("총 투입금", f"₩{invested_krw:,.0f}")
    with c2: st.metric("현재 잔액", f"₩{balance_krw:,.0f}")
    with c3: st.metric("누적 수익", f"₩{current_pnl_krw:,.0f}", delta=f"${total_pnl_usd:,.2f}")
    with c4: st.metric("로드맵 목표", "$50,000")

with tab3:
    st.subheader("💸 대출 & 상환 관리 (자동 저장 중)")
    edited_loans = st.data_editor(st.session_state.loan_df, num_rows="dynamic", use_container_width=True,
                                  column_config={"대출금액": st.column_config.NumberColumn(format="%,d"),
                                                 "상환금액": st.column_config.NumberColumn(format="%,d")}, key="loan_editor")
    
    if not edited_loans.equals(st.session_state.loan_df):
        save_loans(edited_loans)
        st.session_state.loan_df = edited_loans
        st.rerun()
