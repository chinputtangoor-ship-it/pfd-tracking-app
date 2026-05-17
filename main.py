import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
from constants import DEFECT_LIST, STATUS_COLORS, LINES

st.set_page_config(
    page_title="POST PRODUCTION",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- [CONNECTION] ---
conn = st.connection("gsheets", type=GSheetsConnection)

# ระบบดักแคชชิ่งระหว่างการอ่านข้อมูล (คงไว้ 10 วินาทีเพื่อลดปริมาณการดึง Google API)
@st.cache_data(ttl=10)
def load_csv(sheet_name):
    try:
        df = conn.read(worksheet=sheet_name)
        return df.dropna(how="all")
    except Exception as e:
        st.error(f"Error loading {sheet_name}: {e}")
        return pd.DataFrame()

def save_to_csv(sheet_name, df_new):
    try:
        df_old = conn.read(worksheet=sheet_name).dropna(how="all")
        df_final = pd.concat([df_old, df_new], ignore_index=True)
        conn.update(worksheet=sheet_name, data=df_final)
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Error saving to {sheet_name}: {e}")

def update_full_sheet(df_all, sheet_name):
    try:
        conn.update(worksheet=sheet_name, data=df_all)
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Error updating {sheet_name}: {e}")

# --- [MODERN UI CSS] ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght=300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; }
    .stButton>button { border-radius: 8px; font-weight: 600; transition: all 0.2s; border: 1px solid #ddd; }
    .main-header { font-size: 28px; font-weight: 700; color: #1E3A8A; text-align: center; margin-bottom: 30px; }
    .footer { position: fixed; right: 20px; bottom: 10px; color: rgba(128, 128, 128, 0.5); font-size: 11px; }
    </style>
    <div class="footer">© 2026 Production Tech | Develop by Phutthangkun | Ver.01.04</div>
    """, unsafe_allow_html=True)

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'page' not in st.session_state: st.session_state.page = "Home"

# --- [LOGIN PAGE] ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>POST PRODUCTION SYSTEM</h1>", unsafe_allow_html=True)
    col_l, col_m, col_r = st.columns([1, 1.2, 1])
    with col_m:
        with st.container(border=True):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")

            if st.button("Login", use_container_width=True, type="primary"):
                acc_df = load_csv("accounts")

                if acc_df.empty:
                    initial_admin = pd.DataFrame([{
                        "fullname": "Administrator", "emp_id": "001", "username": "admin",
                        "password": "Password12", "role": "admin", "first_login": False
                    }])
                    update_full_sheet(initial_admin, "accounts")
                    acc_df = initial_admin

                acc_df['username'] = acc_df['username'].astype(str)
                acc_df['password'] = acc_df['password'].astype(str)
                user_match = acc_df[acc_df['username'] == u.strip()]

                if not user_match.empty and str(user_match.iloc[0]['password']) == p:
                    st.session_state.logged_in = True
                    st.session_state.user_data = user_match.iloc[0].to_dict()
                    st.rerun()
                else:
                    if u == "admin" and p == "Password12":
                        st.session_state.logged_in = True
                        st.session_state.user_data = {
                            "fullname": "Administrator (Offline)", "username": "admin",
                            "role": "admin", "first_login": False
                        }
                        st.rerun()
                    st.error("Username หรือ Password ไม่ถูกต้อง")
    st.stop()

# First Login Check
if st.session_state.user_data.get('first_login') == True or str(st.session_state.user_data.get('first_login')).lower() == 'true':
    st.title("🔒 เปลี่ยนรหัสผ่านใหม่ (ครั้งแรก)")
    new_p = st.text_input("New Password (8 หลัก)", type="password")
    confirm_p = st.text_input("Confirm Password", type="password")
    if st.button("ยืนยัน"):
        if len(new_p) == 8 and sum(1 for c in new_p if c.isalpha()) >= 2 and new_p == confirm_p:
            acc_df = load_csv("accounts")
            acc_df.loc[acc_df['username'].astype(str) == st.session_state.user_data['username'], ['password', 'first_login']] = [new_p, False]
            update_full_sheet(acc_df, "accounts")
            st.session_state.user_data['first_login'] = False
            st.success("สำเร็จ! กรุณารอสักครู่...")
            st.rerun()
        else:
            st.error("รหัสต้องมี 8 หลัก และภาษาอังกฤษ 2 ตัวขึ้นไป")
    st.stop()

# --- [NAVBAR / SIDEBAR] ---
st.sidebar.title(f"👤 {st.session_state.user_data['fullname']}")
st.sidebar.write(f"Level: {st.session_state.user_data['role']}")
if st.sidebar.button("🚪 ออกจากระบบ", use_container_width=True):
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.rerun()
if st.sidebar.button("🏠 กลับหน้าหลัก (Home)", use_container_width=True):
    for k in ['sel_line', 'sel_batch', 'edit_mode', 'last_target', 'sel_line_re', 'sel_batch_re']:
        if k in st.session_state: del st.session_state[k]
    st.session_state.page = "Home"
    st.rerun()

# --- [HOME DASHBOARD] ---
if st.session_state.page == "Home":
    st.markdown("<div class='main-header'>🏠 Production System</div>", unsafe_allow_html=True)
    role = st.session_state.user_data['role']

    c1, c2, c3 = st.columns(3)
    with c1:
        with st.container(border=True):
            st.markdown("### 📦 Production")
            if st.button("📦 Box Status", use_container_width=True): st.session_state.page = "Box_Status"; st.rerun()
            if st.button("🗑️ Rejection Weight", use_container_width=True): st.session_state.page = "Rejection"; st.rerun()
            if st.button("⏳ Backlog Data", use_container_width=True): st.session_state.page = "Backlog"; st.rerun()
            if st.button("🗓️ Plan Management", use_container_width=True): st.session_state.page = "Plan"; st.rerun()
    with c2:
        if role in ["admin", "supervisor", "manager"]:
            with st.container(border=True):
                st.markdown("### 📊 Analysis")
                if st.button("📷 Camera Analysis", use_container_width=True): st.session_state.page = "Camera"; st.rerun()
                if st.button("🔄 Re-pass Tracking", use_container_width=True): st.session_state.page = "Re_pass"; st.rerun()
                if st.button("📈 Dashboard", use_container_width=True): st.session_state.page = "Report"; st.rerun()
    with c3:
        with st.container(border=True):
            st.markdown("### ⚙️ Admin")
            if role == "admin":
                if st.button("👥 Account Management", use_container_width=True): st.session_state.page = "Account"; st.rerun()
            else:
                st.info("🔒 เมนูนี้จำกัดสิทธิ์เฉพาะ Administrator เท่านั้น")

# --- [ROUTING PAGES] ---
if st.session_state.page == "Plan":
    from plan_module import show_plan_page
    show_plan_page(load_csv, save_to_csv, update_full_sheet)

elif st.session_state.page == "Box_Status":
    from box_module import show_box_status_page
    show_box_status_page(load_csv, save_to_csv)

elif st.session_state.page == "Rejection":
    from rejection import show_rejection_page
    show_rejection_page(load_csv, save_to_csv)

elif st.session_state.page == "Backlog":
    from backlog import show_backlog_page
    show_backlog_page(load_csv, save_to_csv)

elif st.session_state.page == "Camera":
    from camera_module import show_camera_page
    show_camera_page(load_csv, save_to_csv)

elif st.session_state.page == "Re_pass":
    from repass_module import show_repass_page
    show_repass_page(load_csv, save_to_csv, conn)

elif st.session_state.page == "Account":
    if st.session_state.user_data.get('role') != "admin":
        st.error("❌ คุณไม่มีสิทธิ์เข้าถึงหน้านี้")
        st.stop()
    from accounts import show_account_page

    show_account_page(load_csv, save_to_csv, update_full_sheet)
