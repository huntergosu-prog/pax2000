import streamlit as st
import pandas as pd
import io
import re
from datetime import datetime, timedelta

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="팍스2000 통합 대시보드", layout="wide")
st.markdown("""
    <style>
    html, body, [class*="css"] { font-size: 13px !important; }
    div[data-testid="stMetricValue"] { font-size: 16px !important; }
    h1 { font-size: 20px !important; margin-bottom: 5px; }
    .krw-label { color: #ff4b4b; font-size: 12px; font-weight: bold; margin-top: -5px; margin-bottom: 5px; }
    .update-time { font-size: 11px; color: #666; margin-top: 5px; }
    .total-row { background-color: #f8f9fa; font-weight: bold; border-top: 2px solid #ff4b4b; padding: 15px; margin-top: 10px; border-radius: 8px; font-size: 14px; }
    .hl-parser { background-color: #f0f7ff; padding: 15px; border-radius: 10px; margin-bottom: 20px; border: 1px dashed #007bff; }
    </style>
    """, unsafe_allow_html=True)

# 2. 유틸리티 함수
def get_kst_time():
    return (datetime.utcnow() + timedelta(hours=9)).strftime("%m/%d %H:%M")

def parse_money(money_str):
    if pd.isna(money_str) or str(money_str).strip() == "" or str(money_str).lower() == "nan": return 0.0
    try:
        clean = re.sub(r'[^\d.-]', '', str(money_str))
        return float(clean) if clean else 0.0
    except: return 0.0

# 3. 데이터 세션 상태 초기화
if 'main_df' not in st.session_state: 
    st.session_state.main_df = pd.DataFrame(columns=["날짜", "종목명", "포지션", "매수가", "매도가", "수익", "비고"])
if 'monthly_data' not in st.session_state: 
    st.session_state.monthly_data = {"2026": pd.DataFrame(0.0, index=["수익($)", "수익(₩)"], columns=[f"{i}월" for i in range(1, 13)])}
if 'loan_df' not in st.session_state: 
    st.session_state.loan_df = pd.DataFrame([
        {"대출처": "KB라이프", "대출금액": 50000000.0, "상환금액": 0.0, "비고": ""},
        {"대출처": "하나생명", "대출금액": 90000000.0, "상환금액": 0.0, "비고": ""},
        {"대출처": "마이너스", "대출금액": 100000000.0, "상환금액": 0.0, "비고": ""}
    ])
if 'summary_data' not in st.session_state: 
    st.session_state.summary_data = {"투입": "₩40,000,000", "잔액": "₩16,818,623", "수익": "-₩21,981,377", "본전": "$14,513.95"}

# 4. 상단 대시보드
st.title("🚀 팍스2000: 130억 로드맵 통합 관리")
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    if st.button("🔄 환율 갱신"): st.cache_data.clear(); st.rerun()
    cur_ex = st.number_input("현재 환율", value=1514.50, step=0.1)
    st.markdown(f"<p class='update-time'>최종 갱신(KST): {get_kst_time()}</p>", unsafe_allow_html=True)

def goal_box(col, label, def_p, def_d):
    with col:
        p_val = st.text_input(f"{label} 목표($)", value=def_p, key=f"p_{label}")
        krw = parse_money(p_val) * cur_ex
        st.markdown(f"<p class='krw-label'>≈ ₩{krw:,.0f}</p>", unsafe_allow_html=True)
        st.text_input(f"{label} 날짜", value=def_d, key=f"d_{label}")

goal_box(c2, "1단계", "$50,000", "2026.03")
goal_box(c3, "2단계", "$200,000", "2026.05")
goal_box(c4, "3단계", "$2,000,000", "2026.07")
goal_box(c5, "4단계", "$10,000,000", "2026.12")

st.divider()

# 5. 탭 구성
tab1, tab2, tab3 = st.tabs(["📊 자산 통계", "📝 실시간 매매일지", "💸 대출 & 상환"])

with tab2:
    # --- [신규] 하이퍼리퀴드 한 줄 정리기 ---
    st.markdown('<div class="hl-parser">', unsafe_allow_html=True)
    st.subheader("🔗 하이퍼리퀴드 이력 한 줄 정리 (엑셀 복붙용)")
    hl_input = st.text_area("HL 거래 이력(Fills)을 복사해서 붙여넣어줘", height=100, placeholder="Time\tAsset\tSide\tPrice...")
    
    if st.button("🪄 엑셀용 한 줄로 만들기"):
        if hl_input:
            lines = hl_input.strip().split('\n')
            results = []
            for line in lines:
                parts = re.split(r'\t|\s{2,}', line.strip())
                if len(parts) >= 6:
                    date = parts[0].split(' ')[0]
                    asset = parts[1]
                    side = "Short" if "Sell" in parts[2] else "Long"
                    price = parts[3]
                    pnl = parts[-1]
                    # 엑셀 양식: 날짜 | 종목 | 포지션 | 매수 | 매도 | 수익 | 비고
                    if side == "Long":
                        row = f"{date}\t{asset}\t{side}\t{price}\t\t{pnl}\tHL 정리"
                    else:
                        row = f"{date}\t{asset}\t{side}\t\t{price}\t{pnl}\tHL 정리"
                    results.append(row)
            
            if results:
                st.write("▼ 아래 내용을 복사해서 엑셀에 붙여넣으세요!")
                for res in results:
                    st.code(res, language="text")
            else:
                st.error("데이터 형식이 맞지 않아. 하이퍼리퀴드 표 내용을 긁어와줘!")
    st.markdown('</div>', unsafe_allow_html=True)

    # 매매일지 본문
    st.subheader("📉 매매 기록 데이터 관리")
    up_file = st.file_uploader("파일 업로드 (CSV)", type=["csv"], label_visibility="collapsed")
    if up_file:
        try:
            try: content = up_file.getvalue().decode('utf-8-sig')
            except: content = up_file.getvalue().decode('cp949')
            raw = pd.read_csv(io.StringIO(content), header=None).fillna("")
            for r in range(len(raw)):
                row_vals = [str(x).strip() for x in raw.iloc[r].tolist()]
                if "현 잔액" in " ".join(row_vals):
                    for c, val in enumerate(row_vals):
                        if "현 잔액" in val and r+1 < len(raw): st.session_state.summary_data["잔액"] = str(raw.iloc[r+1, c])
                if "종목명" in row_vals:
                    df = raw.iloc[r:].copy()
                    df.columns = df.iloc[0]; df = df[1:].reset_index(drop=True)
                    st.session_state.main_df = df.loc[:, ~df.columns.duplicated()].dropna(subset=['종목명'], how='all')
            st.success("데이터 로드 완료!")
        except Exception as e: st.error(f"실패: {e}")
    
    st.session_state.main_df = st.data_editor(st.session_state.main_df, num_rows="dynamic", use_container_width=True, key="main_editor_v27")
    
    c_s1, c_d1 = st.columns(2)
    with c_s1:
        if st.button("💾 매매일지 저장"): st.success("세션에 저장되었습니다.")
    with c_d1:
        st.download_button("📥 매매일지 다운로드", st.session_state.main_df.to_csv(index=False).encode('utf-8-sig'), "trading_log.csv", "text/csv")

with tab1:
    ca, cb, cc, cd = st.columns(4)
    s = st.session_state.summary_data
    def m(col, l, val, krw):
        with col:
            st.caption(l); num = parse_money(val); usd_val = num if "본전" in l else num / cur_ex
            st.subheader(f"${usd_val:,.2f}"); st.markdown(f"<p class='krw-label'>{krw}</p>", unsafe_allow_html=True)
    m(ca, "총 투입금", s.get('투입', '0'), s.get('투입', '₩0'))
    m(cb, "현재 잔액", s.get('잔액', '0'), s.get('잔액', '₩0'))
    m(cc, "누적 수익", s.get('수익', '0'), s.get('수익', '₩0'))
    m(cd, "본전 수익목표", s.get('본전', '0'), f"₩{parse_money(s.get('본전', '0'))*cur_ex:,.0f}")
    st.write("---")
    st.subheader("🗓️ 월별 수익 현황")
    st.table(st.session_state.monthly_data["2026"].applymap(lambda x: f"{x:,.2f}"))

with tab3:
    st.subheader("💸 대출 & 상환 관리")
    st.info("💡 금액을 입력하면 3자리마다 쉼표(,)가 찍히며, 탭(Tab) 이동 시에도 저장됩니다.")
    
    # 대출 에디터 (3자리 쉼표 설정 포함)
    loan_editor_df = st.data_editor(
        st.session_state.loan_df, 
        num_rows="dynamic", 
        use_container_width=True,
        column_config={
            "대출금액": st.column_config.NumberColumn("대출금액(₩)", format="%,d", min_value=0),
            "상환금액": st.column_config.NumberColumn("상환금액(₩)", format="%,d", min_value=0)
        },
        key="loan_editor_v27"
    )
    
    if not loan_editor_df.equals(st.session_state.loan_df):
        st.session_state.loan_df = loan_editor_df
        st.rerun()

    tl = st.session_state.loan_df['대출금액'].apply(parse_money).sum()
    tr = st.session_state.loan_df['상환금액'].apply(parse_money).sum()
    
    st.markdown(f"""
    <div class="total-row">
        💰 총 대출액: ₩{tl:,.0f} &nbsp;&nbsp; | &nbsp;&nbsp; 
        <span style="color: blue;">✅ 총 상환액: ₩{tr:,.0f}</span> &nbsp;&nbsp; | &nbsp;&nbsp; 
        <span style="color: red;">🚨 남은 잔액: ₩{tl-tr:,.0f}</span>
    </div>
    """, unsafe_allow_html=True)
    
    c_s2, c_d2 = st.columns(2)
    with c_s2:
        if st.button("💾 대출 데이터 저장"): st.success("저장되었습니다.")
    with c_d2:
        st.download_button("📥 대출내역 다운로드", st.session_state.loan_df.to_csv(index=False).encode('utf-8-sig'), "loans.csv", "text/csv")
