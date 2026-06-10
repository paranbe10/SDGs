import os
import sqlite3
import pandas as pd
from datetime import datetime
import streamlit as st
import base64

# DB 파일명
DB_FILE = "global_app.db"

# --- [데이터베이스 초기화 및 스키마 업데이트] ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 1. User_Table (수발신 날짜 컬럼 추가)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS User_Table (
            P_ID TEXT PRIMARY KEY,
            P_PW TEXT,
            name TEXT,
            language TEXT,
            country TEXT,
            last_sent_date TEXT,
            last_received_date TEXT
        )
    """)
    
    # 2. Diary_Table
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
    
    # 3. Community_Table
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

    # 4. Community_Like_Table (좋아요)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Community_Like_Table (
            L_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            T_ID INTEGER,
            P_ID TEXT
        )
    """)

    # 5. Community_Comment_Table (댓글)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Community_Comment_Table (
            C_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            T_ID INTEGER,
            P_ID TEXT,
            comment_text TEXT,
            wr_date TEXT
        )
    """)
    
    conn.commit()
    conn.close()

init_db()

# --- [유틸리티 함수] ---
def get_db_connection():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def encode_pw(pw):
    return base64.b64encode(pw.encode('utf-8')).decode('utf-8')

# --- [세션 초기화] ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_info" not in st.session_state:
    st.session_state.user_info = None

# ==========================================
# [로그인 / 회원가입 화면]
# ==========================================
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🌍 지구촌 일기 우체통</h1>", unsafe_allow_html=True)
    
    auth_tabs = st.tabs(["로그인", "회원가입"])
    
    with auth_tabs[0]:
        with st.form("login_form"):
            st.write("### 서랍 열기")
            col1, col2 = st.columns([3, 1])
            with col1:
                login_id_prefix = st.text_input("아이디", placeholder="아이디 입력", label_visibility="collapsed")
            with col2:
                st.markdown("<div style='margin-top: 10px; font-weight: bold;'>@gmail.com</div>", unsafe_allow_html=True)
            
            login_pw = st.text_input("비밀번호", type="password", placeholder="비밀번호")
            submit_login = st.form_submit_button("로그인", use_container_width=True)
            
            if submit_login:
                if not login_id_prefix or not login_pw:
                    st.error("항목을 모두 입력하세요.")
                else:
                    full_id = f"{login_id_prefix}@gmail.com"
                    conn = get_db_connection()
                    user = pd.read_sql_query("SELECT * FROM User_Table WHERE P_ID=? AND P_PW=?", conn, params=(full_id, encode_pw(login_pw)))
                    conn.close()
                    
                    if not user.empty:
                        st.session_state.logged_in = True
                        st.session_state.user_info = user.iloc[0].to_dict()
                        st.rerun()
                    else:
                        st.error("정보가 일치하지 않습니다.")

    with auth_tabs[1]:
        with st.form("register_form"):
            st.write("### 동행인 정보 등록")
            col1, col2 = st.columns([3, 1])
            with col1:
                reg_id_prefix = st.text_input("사용할 아이디", placeholder="아이디 입력", label_visibility="collapsed")
            with col2:
                st.markdown("<div style='margin-top: 10px; font-weight: bold;'>@gmail.com</div>", unsafe_allow_html=True)
                
            reg_pw = st.text_input("비밀번호 (8자 이상)", type="password")
            reg_name = st.text_input("닉네임")
            reg_lang = st.selectbox("사용 언어", ["KO", "EN", "JA", "ZH", "FR"])
            reg_country = st.selectbox("국가", ['Korea', 'USA', 'Japan', 'China', 'United Kingdom', 'France', 'Germany', 'Vietnam'])
            
            submit_reg = st.form_submit_button("가입하기", use_container_width=True)
            
            if submit_reg:
                if not reg_id_prefix or not reg_pw or not reg_name:
                    st.error("빈칸을 모두 채워주세요.")
                elif len(reg_pw) < 8:
                    st.error("비밀번호는 8자 이상이어야 합니다.")
                else:
                    full_id = f"{reg_id_prefix}@gmail.com"
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM User_Table WHERE P_ID=?", (full_id,))
                    if cursor.fetchone():
                        st.error("이미 존재하는 아이디입니다.")
                    else:
                        cursor.execute("INSERT INTO User_Table VALUES (?, ?, ?, ?, ?, '', '')", 
                                       (full_id, encode_pw(reg_pw), reg_name, reg_lang, reg_country))
                        conn.commit()
                        st.success("가입 완료! 로그인 탭에서 접속해주세요.")
                    conn.close()

else:
    # ==========================================
    # [메인 앱 화면 (로그인 성공 후)]
    # ==========================================
    user = st.session_state.user_info
    
    st.sidebar.markdown(f"**👤 {user['name']}** ({user['country']})")
    if st.sidebar.button("로그아웃"):
        st.session_state.logged_in = False
        st.session_state.user_info = None
        st.rerun()

    tab_ocean, tab_plaza = st.tabs(["🌊 표류하는 일기바다", "🕊️ 익명 소통광장"])

    # ------------------------------------------
    # 1. 🌊 표류하는 일기바다
    # ------------------------------------------
    with tab_ocean:
        # 바다 테마 CSS 적용 및 이모티콘 애니메이션
        st.markdown("""
        <style>
        .ocean-bg {
            background: linear-gradient(180deg, #87CEEB 0%, #1E90FF 100%);
            border-radius: 15px;
            padding: 40px;
            text-align: center;
            min-height: 250px;
            position: relative;
            overflow: hidden;
            box-shadow: inset 0 0 20px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .emoji-float {
            font-size: 2.5rem;
            display: inline-block;
            margin: 0 15px;
            animation: float 3s ease-in-out infinite;
        }
        @keyframes float {
            0% { transform: translateY(0px) rotate(0deg); }
            50% { transform: translateY(-15px) rotate(10deg); }
            100% { transform: translateY(0px) rotate(0deg); }
        }
        </style>
        <div class="ocean-bg">
            <h3 style="color: white; text-shadow: 1px 1px 2px rgba(0,0,0,0.5);">밀려오는 일기 바다</h3>
            <p style="color: #f0f0f0;">바다에 떠도는 편지를 건져보세요.</p>
            <div style="margin-top: 30px;">
                <span class="emoji-float">🛟</span>
                <span class="emoji-float" style="animation-delay: 0.5s;">🐠</span>
                <span class="emoji-float" style="animation-delay: 1s;">📜</span>
                <span class="emoji-float" style="animation-delay: 1.5s;">🦑</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_action1, col_action2 = st.columns(2)
        
        # 글 건지기 기능
        with col_action1:
            if st.button("🎣 바다에서 편지 건지기", use_container_width=True):
                today_str = datetime.now().strftime("%Y-%m-%d")
                conn = get_db_connection()
                cursor = conn.cursor()
                
                # 수신 제한 체크
                if user['last_received_date'] == today_str:
                    st.warning("오늘은 이미 편지를 건졌습니다. 내일 다시 시도해주세요!")
                else:
                    cursor.execute("""
                        SELECT D_ID, S_ID, date, O, O_language FROM Diary_Table
                        WHERE S_ID != ? AND (R_ID IS NULL OR R_ID = '')
                        ORDER BY RANDOM() LIMIT 1
                    """, (user['P_ID'],))
                    row = cursor.fetchone()
                    
                    if row:
                        d_id, s_id, d_date, o_text, o_lang = row
                        cursor.execute("UPDATE Diary_Table SET R_ID = ? WHERE D_ID = ?", (user['P_ID'], d_id))
                        cursor.execute("UPDATE User_Table SET last_received_date = ? WHERE P_ID = ?", (today_str, user['P_ID']))
                        conn.commit()
                        st.session_state.user_info['last_received_date'] = today_str
                        
                        st.success("🎉 새로운 편지를 건져 소유권을 획득했습니다! (보관함 확인)")
                        st.info(f"**원문 ({o_lang})**\n\n{o_text}")
                    else:
                        st.info("바다에 건질 편지가 없습니다. (누군가 띄워주길 기다리세요 🌊)")
                conn.close()

        # 하단 메뉴 (편지 띄우기 & 보관함)을 Popover(버튼 안으로 숨기기)로 구현
        with col_action2:
            with st.popover("✉️ 새 편지 띄우기", use_container_width=True):
                st.write("**바다에 내 이야기 던지기 (최대 500자)**")
                diary_content = st.text_area("내용", max_chars=500, label_visibility="collapsed")
                
                if st.button("✈️ 비행기 날려보내기", use_container_width=True):
                    today_str = datetime.now().strftime("%Y-%m-%d")
                    if not diary_content.strip():
                        st.error("내용을 작성해주세요.")
                    elif user['last_sent_date'] == today_str:
                        st.error("일기는 하루에 1개만 발송할 수 있습니다.")
                    else:
                        conn = get
