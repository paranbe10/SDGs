import os
import sqlite3
import pandas as pd
from datetime import datetime
import streamlit as st

DB_FILE = "global_app.db"
CURRENT_USER = "user1"  # 가상 로그인 유저 고정

# --- [1. 데이터베이스 초기화 및 CSV 임포트 로직] ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 4개 테이블 생성 (제공된 스키마 준수)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS User_Table (
            P_ID TEXT PRIMARY KEY,
            P_PW TEXT,
            name TEXT,
            language TEXT,
            country TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Diary_Table (
            D_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            S_ID TEXT,
            R_ID TEXT,
            date TEXT,
            O TEXT,
            O_language TEXT,
            translated TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Community_Table (
            T_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            random TEXT,
            title TEXT,
            text TEXT,
            wr_date TEXT,
            s_category TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Culture_Info_Table (
            I_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            targeted TEXT,
            subject TEXT,
            I_text TEXT,
            cautions TEXT
        )
    """)
    conn.commit()

    # [스프레드시트에서 내려받은 CSV 파일이 주변에 있다면 자동으로 DB에 밀어넣는 로직]
    # 파일명 매핑 (가지고 계신 파일명에 맞게 조정 가능)
    csv_mappings = {
        "User_Table": "지구촌 협력 앱 DB.xlsx - User_Table.csv",
        "Diary_Table": "지구촌 협력 앱 DB.xlsx - Diary_Table.csv",
        "Community_Table": "지구촌 협력 앱 DB.xlsx - Community_Table.csv",
        "Culture_Info_Table": "지구촌 협력 앱 DB.xlsx - Culture_Info_Table.csv"
    }

    for table_name, csv_file in csv_mappings.items():
        # DB가 비어있고 CSV 파일이 존재할 때만 임포트 진행
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        if cursor.fetchone()[0] == 0 and os.path.exists(csv_file):
            try:
                df = pd.read_csv(csv_file)
                # 데이터프레임을 SQLite 테이블에 밀어넣기
                df.to_sql(table_name, conn, if_exists='append', index=False)
                st.info(f"💡 {csv_file} 데이터를 성공적으로 DB에 로드했습니다.")
            except Exception as e:
                st.error(f"❌ {csv_file} 로드 중 오류 발생: {e}")

    # 기본 테스트 더미 데이터 (CSV 파일이 없을 경우 대비 예외처리용)
    cursor.execute("SELECT COUNT(*) FROM User_Table")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT OR IGNORE INTO User_Table VALUES ('user1', 'pwd1', '지구인A', 'KO', 'South Korea')")
        cursor.execute("INSERT OR IGNORE INTO User_Table VALUES ('user2', 'pwd2', 'Smith', 'EN', 'USA')")
        cursor.execute("INSERT OR IGNORE INTO Diary_Table (S_ID, R_ID, date, O, O_language, translated) VALUES ('user2', NULL, '2026-06-10', 'Hello! This is a letter floating from USA.', 'EN', NULL)")
        cursor.execute("INSERT OR IGNORE INTO Community_Table (random, title, text, wr_date, s_category) VALUES ('rand', '반갑습니다', '소통광장에 오신 것을 환영합니다.', '2026-06-10 12:30', '자유')")
        conn.commit()

    conn.close()

# 앱 기동 시 DB 초기화 실행
init_db()


# --- [2. Streamlit UI 구성] ---
st.set_page_config(page_title="지구촌 협력 애플리케이션", page_icon="🌍", layout="centered")
st.title("🌍 지구촌 협력 애플리케이션")

# 상단 탭 구성 (바다 vs 광장)
tab_ocean, tab_plaza = st.tabs(["🌊 표류하는 일기바다", "🕊️ 익명 소통광장"])

# --- [3. 🌊 표류하는 일기바다 탭 구현] ---
with tab_ocean:
    st.subheader("🌊 표류하는 일기바다")
    st.caption("지구촌 어딘가에서 떠도는 비밀 일기를 건지거나, 당신의 이야기를 바다에 띄워보세요.")
    
    # 기능 분할 (글 쓰기 / 글 건지기)
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### ✉️ 내 일기 바다에 던지기")
        diary_text = st.text_area("이야기 작성", placeholder="지구촌 누군가에게 닿을 이야기를 적어보세요...", key="diary_input", label_visibility="collapsed")
        if st.button("바다에 던지기", use_container_width=True):
            if diary_text.strip():
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                date_str = datetime.now().strftime("%Y-%m-%d")
                
                # ★ 자동번역 삭제 요구사항 반영: translated 컬럼에는 None(NULL) 삽입
                cursor.execute("""
                    INSERT INTO Diary_Table (S_ID, R_ID, date, O, O_language, translated)
                    VALUES (?, NULL, ?, ?, 'KO', NULL)
                """, (CURRENT_USER, date_str, diary_text))
                conn.commit()
                conn.close()
                st.success("편지를 성공적으로 바다에 던졌습니다! 🌊")
            else:
                st.warning("내용을 입력해주세요.")

    with col2:
        st.write("### 🛟 타인의 일기 건지기")
        st.write("바다 속에 표류 중인 익명의 편지를 무작위로 하나 건져올립니다.")
        
        if st.button("🎣 편지 건져올리기", use_container_width=True):
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # 내가 쓰지 않았고, 아직 아무도 건지지 않은(R_ID IS NULL) 랜덤 편지 검색
            cursor.execute("""
                SELECT D_ID, S_ID, date, O, O_language FROM Diary_Table
                WHERE S_ID != ? AND R_ID IS NULL
                ORDER BY RANDOM() LIMIT 1
            """, (CURRENT_USER,))
            row = cursor.fetchone()
            
            if row:
                d_id, s_id, date, o_text, o_lang = row
                # 소유권 이전 (R_ID를 현재 유저로 업데이트)
                cursor.execute("UPDATE Diary_Table SET R_ID = ? WHERE D_ID = ?", (CURRENT_USER, d_id))
                conn.commit()
                
                # 세션 상태에 저장하여 화면에 고정 표시
                st.session_state['fished_diary'] = {
                    "sender": s_id,
                    "date": date,
                    "content": o_text,
                    "lang": o_lang
                }
                st.toast("새로운 편지를 건졌습니다!")
            else:
                st.session_state['fished_diary'] = None
                st.info("바다에 떠도는 새로운 편지가 더 이상 없습니다. 🌊")
            conn.close()
            
        # 건진 편지가 세션에 존재할 때 UI 출력
        if st.session_state.get('fished_diary'):
            fd = st.session_state['fished_diary']
            st.info(f"""
            **📩 건져 올린 편지 원문** ({fd['lang']})  
            *발신인: {fd['sender']} / 날짜: {fd['date']}* ---
            "{fd['content']}"
            
            ---
            *이 편지는 당신이 소유권을 획득하여 보관함에 안전하게 저장되었습니다. 🗂️*
            """)

    # 히스토리 보관함 역역
    st.write("---")
    st.write("### 🗂️ 내 편지 보관함 (히스토리)")
    
    hist_tab1, hist_tab2 = st.tabs(["내가 띄운 편지 ✉️", "내가 건진 편지 🛟"])
    
    conn = sqlite3.connect(DB_FILE)
    df_all = pd.read_sql_query("SELECT * FROM Diary_Table", conn)
    conn.close()
    
    with hist_tab1:
        df_floated = df_all[df_all['S_ID'] == CURRENT_USER].sort_values(by="D_ID", ascending=False)
        if not df_floated.empty:
            for _, item in df_floated.iterrows():
                status = f"➔ 수신자: {item['R_ID']}" if item['R_ID'] else "➔ 바다 표류 중 🌊"
                with st.expander(f"📅 {item['date']} | {status}"):
                    st.write(item['O'])
        else:
            st.caption("바다에 띄운 편지가 없습니다.")
            
    with hist_tab2:
        df_fished = df_all[df_all['R_ID'] == CURRENT_USER].sort_values(by="D_ID", ascending=False)
        if not df_fished.empty:
            for _, item in df_fished.iterrows():
                with st.expander(f"📅 {item['date']} | 보낸사람: {item['S_ID']}"):
                    st.write(f"**원문 ({item['O_language']}):**")
                    st.write(item['O'])
        else:
            st.caption("건져 올린 편지가 없습니다.")


# --- [4. 🕊️ 익명 소통광장 탭 구현] ---
with tab_plaza:
    st.subheader("🕊️ 익명 소통광장")
    st.caption("전 세계 사람들과 익명으로 트위터/스레드 스타일의 자유로운 이야기를 나눠보세요.")
    
    # 1. 새 글 작성 영역
    with st.expander("✒️ 새로운 생각 나누기 (글쓰기)", expanded=False):
        col_cat, col_title = st.columns([1, 2])
        with col_cat:
            p_category = st.selectbox("카테고리", ["자유", "문화", "질문"])
        with col_title:
            p_title = st.text_input("제목 (선택)", placeholder="무제")
            
        p_text = st.text_area("내용", placeholder="무슨 일이 일어나고 있나요? 자유롭게 적어보세요.")
        
        if st.button("광장에 올리기", use_container_width=True):
            if p_text.strip():
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                wr_date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                final_title = p_title if p_title.strip() else "무제"
                
                cursor.execute("""
                    INSERT INTO Community_Table (random, title, text, wr_date, s_category)
                    VALUES ('rand_user', ?, ?, ?, ?)
                """, (final_title, p_text, wr_date_str, p_category))
                conn.commit()
                conn.close()
                st.success("글이 소통광장에 즉시 등록되었습니다!")
                st.rerun()  # 등록 즉시 피드 새로고침
            else:
                st.warning("내용을 입력해주세요.")
                
    st.write("---")
    
    # 2. 카테고리 필터링 조회 영역
    selected_filter = st.radio("카테고리 필터", ["전체", "자유", "문화", "질문"], horizontal=True)
    
    conn = sqlite3.connect(DB_FILE)
    if selected_filter == "전체":
        df_posts = pd.read_sql_query("SELECT * FROM Community_Table ORDER BY T_ID DESC", conn)
    else:
        df_posts = pd.read_sql_query("SELECT * FROM Community_Table WHERE s_category = ? ORDER BY T_ID DESC", conn, params=(selected_filter,))
    conn.close()
    
    # 피드 레이아웃 스타일 렌더링
    if not df_posts.empty:
        for _, post in df_posts.iterrows():
            st.markdown(f"""
            <div style="background-color: #f9f9f9; padding: 15px; border-radius: 12px; margin-bottom: 12px; border: 1px solid #eee;">
                <span style="font-size: 11px; background-color: #e3f2fd; color: #0d47a1; padding: 2px 8px; border-radius: 10px; font-weight: bold; float: right;">
                    {post['s_category']}
                </span>
                <span style="font-weight: bold; font-size: 14px; color: #333;">👤 익명의 누군가</span> 
                <span style="font-size: 11px; color: #aaa; margin-left: 5px;">@anonymous · {post['wr_date']}</span>
                <h4 style="margin: 8px 0 4px 0; color: #111; font-size: 15px;">{post['title']}</h4>
                <p style="font-size: 13px; color: #444; line-height: 1.5; margin: 0;">{post['text']}</p>
                <div style="margin-top: 10px; font-size: 12px; color: #888;">
                    ❤️ 12 &nbsp;&nbsp; 💬 4 &nbsp;&nbsp; 🔁 공유
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.caption("광장에 등록된 이야기가 아직 없습니다.")
