import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import random
import string
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

# ==========================================
# 1. การตั้งค่าเบื้องต้นและการเชื่อมต่อ Google Sheets
# ==========================================
st.set_page_config(page_title="Post Production System (Online)", layout="wide")

# สร้างการเชื่อมต่อกับ Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- รายการข้อมูลคงที่ ---
DEFECT_LIST = ["Bubble", "Mashed", "Dent cap", "Dent body", "Loose", "Rough edge", "Ink speck", "Soiled", "Dirty",
               "Skewing", "Machine breakdown"]
STATUS_COLORS = {"AF": "#2ecc71", "Sort": "#3498db", "PS": "#e74c3c", "HP": "#f1c40f", "HUP": "#9b59b6",
                 "Scrap": "#000000"}
LINES = [f"H5{i:02d}" for i in range(1, 14)]

# --- Watermark ---
st.markdown("""
    <style>
    .footer { position: fixed; right: 20px; bottom: 10px; color: rgba(128, 128, 128, 0.5); font-size: 10px; z-index: 1000; pointer-events: none; }
    </style>
    <div class="footer">© 2026 Production Tech | Develop by Phutthangkun</div>
    """, unsafe_allow_html=True)


# --- ฟังก์ชันช่วยจัดการข้อมูลผ่าน Google Sheets (Online Version) ---
def load_csv(sheet_name):
    """โหลดข้อมูลจาก Worksheet ที่ระบุ"""
    try:
        # ดึงข้อมูลจาก Sheet (ระบุชื่อ worksheet)
        df = conn.read(worksheet=sheet_name, ttl="0")  # ttl="0" เพื่อให้ได้ข้อมูลล่าสุดเสมอ
        return df.dropna(how="all")  # ลบแถวที่ว่างเปล่าทั้งหมดออก
    except Exception:
        # ถ้ายังไม่มี Sheet นี้ หรือโหลดไม่ได้ ให้คืนค่า DataFrame ว่าง
        return pd.DataFrame()


def save_to_csv(df_new, sheet_name):
    """บันทึกข้อมูลเพิ่มต่อท้าย (Append) ลงใน Google Sheets"""
    df_old = load_csv(sheet_name)
    if not df_old.empty:
        df_final = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df_final = df_new

    # อัปเดตกลับไปยัง Google Sheets
    conn.update(worksheet=sheet_name, data=df_final)
    st.cache_data.clear()  # ล้าง Cache เพื่อให้การโหลดครั้งต่อไปเห็นข้อมูลใหม่


def validate_inputs(inputs_dict):
    for label, value in inputs_dict.items():
        if value is None or (isinstance(value, str) and "เลือก" in value) or str(value).strip() == "":
            st.error(f"❌ กรุณาระบุข้อมูล: {label}")
            return False
    return True


# ตรวจสอบและสร้างบัญชี Admin เริ่มต้น (ถ้ายังไม่มีใน Sheet)
acc_df = load_csv("accounts")
if acc_df.empty:
    initial_admin = pd.DataFrame([{"fullname": "Administrator", "emp_id": "001", "username": "admin",
                                   "password": "Password12", "role": "admin", "first_login": False}])
    conn.update(worksheet="accounts", data=initial_admin)

# ==========================================
# 2. ระบบ LOGIN & SESSION
# ==========================================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'page' not in st.session_state: st.session_state.page = "Home"

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>POST PRODUCTION SYSTEM (ONLINE)</h1>",
                unsafe_allow_html=True)
    col_l, col_m, col_r = st.columns([1, 1.2, 1])
    with col_m:
        with st.container(border=True):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("Login", use_container_width=True, type="primary"):
                acc_df = load_csv("accounts")
                if not acc_df.empty:
                    # แปลงคอลัมน์ให้เป็น string เพื่อป้องกันปัญหาการเทียบข้อมูล
                    acc_df['username'] = acc_df['username'].astype(str)
                    acc_df['password'] = acc_df['password'].astype(str)

                    user_match = acc_df[acc_df['username'] == u]
                    if not user_match.empty and str(user_match.iloc[0]['password']) == p:
                        st.session_state.logged_in = True
                        st.session_state.user_data = user_match.iloc[0].to_dict()
                        st.rerun()
                    else:
                        st.error("Username หรือ Password ไม่ถูกต้อง")
                else:
                    st.error("ระบบขัดข้อง: ไม่พบฐานข้อมูลผู้ใช้บน Cloud")
    st.stop()

# First Login Check
if st.session_state.user_data.get('first_login') == True or str(
        st.session_state.user_data.get('first_login')).lower() == 'true':
    st.title("🔒 เปลี่ยนรหัสผ่านใหม่ (ครั้งแรก)")
    new_p = st.text_input("New Password (8 หลัก)", type="password")
    confirm_p = st.text_input("Confirm Password", type="password")
    if st.button("ยืนยัน"):
        if len(new_p) == 8 and sum(1 for c in new_p if c.isalpha()) >= 2 and new_p == confirm_p:
            acc_df = load_csv("accounts")
            acc_df.loc[acc_df['username'].astype(str) == st.session_state.user_data['username'], ['password',
                                                                                                  'first_login']] = [
                new_p, False]
            conn.update(worksheet="accounts", data=acc_df)
            st.session_state.user_data['first_login'] = False
            st.success("สำเร็จ! กรุณารอสักครู่...")
            st.rerun()
        else:
            st.error("รหัสต้องมี 8 หลัก และภาษาอังกฤษ 2 ตัวขึ้นไป")
    st.stop()

# ==========================================
# เมนูหลัก (HOME)
# ==========================================
st.sidebar.title(f"👤 {st.session_state.user_data['fullname']}")
st.sidebar.write(f"ID: {st.session_state.user_data['emp_id']}")
if st.sidebar.button("🚪 Logout", use_container_width=True):
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.rerun()

if st.session_state.page == "Home":
    st.title("🏠 Home page")
    st.divider()
    role = st.session_state.user_data['role']
    c1, c2, c3 = st.columns(3)

    with c1:
        st.subheader("📦 Production")
        if st.button("📦 Box Status", use_container_width=True): st.session_state.page = "Box_Status"; st.rerun()
        if st.button("🗑️ Rejection Weight", use_container_width=True): st.session_state.page = "Rejection"; st.rerun()
        if st.button("⏳ Backlog", use_container_width=True): st.session_state.page = "Backlog"; st.rerun()
        if st.button("🗓️ Plan Management", use_container_width=True): st.session_state.page = "Plan"; st.rerun()

    with c2:
        if role != "employee":
            st.subheader("🔄 Camera&Analysis")
            if st.button("📷 Camera Analysis", use_container_width=True): st.session_state.page = "Camera"; st.rerun()
            if st.button("🔄 Re-pass", use_container_width=True): st.session_state.page = "Re_pass"; st.rerun()
            if st.button("📊 Dashboard", use_container_width=True): st.session_state.page = "Report"; st.rerun()

    with c3:
        if role == "admin":
            st.subheader("⚙️ ตั้งค่าระบบ")
            if st.button("👥 จัดการบัญชีผู้ใช้", use_container_width=True): st.session_state.page = "Account"; st.rerun()

# --- หน้าจัดการแผนงาน (PLAN) ---
elif st.session_state.page == "Plan":
    st.title("📅 Production Planning Management")

    plan_df = load_csv("plan")

    tab_v, tab_m, tab_f = st.tabs(["🔍 1. ดูแผนงาน (View)", "⚙️ 2. จัดการ (Manage)", "🔄 3. จบงาน (Finish Batch)"])

    # --- TAB 1: ดูแผนงาน ---
    with tab_v:
        st.subheader("รายการแผนการผลิตทั้งหมด")
        c1, c2 = st.columns([1, 2])
        f_line = c1.selectbox("กรองตาม Line", ["ทั้งหมด"] + LINES, key="filter_line")

        view_df = plan_df.copy()
        if not view_df.empty:
            if f_line != "ทั้งหมด":
                view_df = view_df[view_df['line'] == f_line]
            st.dataframe(view_df, use_container_width=True, hide_index=True)
        else:
            st.info("ยังไม่มีข้อมูลแผนงานในระบบ Cloud")

    # --- TAB 2: จัดการ/เพิ่มแผนใหม่ ---
    with tab_m:
        if st.session_state.user_data['role'] != 'employee':
            st.subheader("➕ เพิ่มแผนการผลิตใหม่")
            with st.form("full_plan_form", clear_on_submit=True):
                r1_c1, r1_c2, r1_c3, r1_c4 = st.columns(4)
                p_line = r1_c1.selectbox("Line", ["เลือก Line"] + LINES)
                p_batch = r1_c2.text_input("Batch Number")
                p_sap = r1_c3.text_input("SAP Batch Number")
                p_order = r1_c4.text_input("Production Order")

                r2_c1, r2_c2, r2_c3, r2_c4 = st.columns(4)
                p_inspec = r2_c1.text_input("Inspection Lot")
                p_so = r2_c2.text_input("Sales Order")
                p_so_item = r2_c3.text_input("SO Item")
                p_fert = r2_c4.text_input("FERT Code")

                r3_c1, r3_c2, r3_c3, r3_c4 = st.columns(4)
                p_semi = r3_c1.text_input("Semifinish Code")
                p_qty = r3_c2.number_input("Item Qty", min_value=0.000, step=0.001, format="%.3f")
                p_af_box = r3_c3.number_input("Need AF Box", min_value=0.000, step=0.001, format="%.3f")
                p_cust = r3_c4.selectbox("Customer Name", [
                    "ACG NORTH AMERCA LLC", "FAME Pharma Pte ltd", "PT.ACG Indonesia",
                    "COMMUNITY PHARMACY PUBLIC", "ERNEST CHEMIST LTD", "Gel strength Co Ltd (Head office)"
                ])

                r4_c1, r4_c2, r4_c3, r4_c4 = st.columns(4)
                p_finish_date = r4_c1.date_input("Planned Finish Date")
                p_desp_date = r4_c2.date_input("To be Desp. on")
                p_metal = r4_c3.selectbox("Metal Detector", ["Normal", "Iron Oxide"])
                p_print = r4_c4.selectbox("Print Type", ["P", "U"])

                r5_c1, r5_c2, r5_c3, r5_c4 = st.columns(4)
                p_country = r5_c1.selectbox("Country",
                                            ["Thailand", "Indonesia", "USA", "Ghana", "Myanma", "Singapore", "Vietnam"])
                p_box = r5_c2.selectbox("Box Packing",
                                        ["Box 660", "Box 675", "Box 705", "Box 705+Liner", "Box 760+EPS Sheet",
                                         "Box Tabsule", "Box Fsample"])

                ink_options = ["None", "RMI010004 Black ACG", "RMI010021 White ACG", "RMI010182 Black ACG/TEK",
                               "RMI010017 Red ACG", "RMI010002 Black TEK", "RMI010057 Green TEK",
                               "RMI010033 Yellow/Gold TEK"]
                p_ink_c = r5_c3.selectbox("Ink Cap", ink_options)
                p_roll_c = r5_c4.text_input("Roller Des. Cap")

                r6_c1, r6_c2, r6_c3, r6_c4 = st.columns(4)
                p_ink_b = r6_c1.selectbox("Ink Body", ink_options)
                p_roll_b = r6_c2.text_input("Roller Des. Body")
                p_status = r6_c3.selectbox("Batch Status", ["Running", "Finished"])

                if st.form_submit_button("➕ บันทึกแผนงานลงระบบ Cloud", use_container_width=True):
                    if validate_inputs({"Line": p_line, "Batch Number": p_batch}):
                        new_data = {
                            "line": p_line, "batch_number": p_batch, "sap_batch": p_sap,
                            "production_order": p_order, "inspection_lot": p_inspec,
                            "sales_order": p_so, "sales_order_item": p_so_item,
                            "fert_code": p_fert, "semifinish_code": p_semi,
                            "item_qty": p_qty, "need_af_box": p_af_box,
                            "customer_name": p_cust, "planned_finish_date": str(p_finish_date),
                            "to_be_desp_on": str(p_desp_date), "metal_detector": p_metal,
                            "print_type": p_print, "country": p_country,
                            "box_packing": p_box, "ink_cap": p_ink_c,
                            "roller_des_cap": p_roll_c, "ink_body": p_ink_b,
                            "roller_des_body": p_roll_b, "batch_status": p_status
                        }
                        save_to_csv(pd.DataFrame([new_data]), "plan")
                        st.success("บันทึกแผนงานใหม่สำเร็จ!")
                        st.rerun()
        else:
            st.warning("🔒 เฉพาะ Supervisor หรือ Admin เท่านั้นที่จัดการแผนงานได้")

    # --- TAB 3: จบงาน (Finish Batch) ---
    with tab_f:
        if st.session_state.user_data['role'] != 'employee':
            st.subheader("📦 รายการ Batch ที่กำลังดำเนินการ (Running)")
            if not plan_df.empty:
                running_df = plan_df[plan_df['batch_status'] == "Running"].copy()
                if not running_df.empty:
                    for idx, row in running_df.iterrows():
                        with st.container():
                            col_info, col_btn = st.columns([4, 1])
                            with col_info:
                                st.markdown(f"📍 **Line:** {row['line']} | **Batch:** `{row['batch_number']}`")
                                st.caption(f"FERT: {row['fert_code']} | Customer: {row['customer_name']}")
                            with col_btn:
                                if st.button(f"🏁 จบงาน", key=f"fin_{row['batch_number']}", use_container_width=True,
                                             type="primary"):
                                    # อัปเดตสถานะใน DataFrame และเขียนทับ Sheet เดิม
                                    plan_df.loc[
                                        plan_df['batch_number'] == row['batch_number'], 'batch_status'] = "Finished"
                                    conn.update(worksheet="plan", data=plan_df)
                                    st.cache_data.clear()
                                    st.success(f"Batch {row['batch_number']} เปลี่ยนสถานะเป็น Finished แล้ว")
                                    st.rerun()
                        st.divider()
                else:
                    st.success("✅ ขณะนี้ไม่มี Batch ที่สถานะ Running")
            else:
                st.info("ยังไม่มีข้อมูลแผนงานในระบบ")
        else:
            st.warning("🔒 เฉพาะ Supervisor หรือ Admin เท่านั้นที่จบงานได้")

    if st.button("🏠 กลับหน้าหลัก"):
        st.session_state.page = "Home"
        st.rerun()

# --- หน้า BOX STATUS (Online Version) ---
elif st.session_state.page == "Box_Status":
    st.title("📦 Box Status Recording")

    if 'sel_line' not in st.session_state:
        st.subheader("📍 เลือก Line")
        cols = st.columns(4)
        for i, l in enumerate(LINES):
            if cols[i % 4].button(l, key=f"btn_l_{l}", use_container_width=True):
                st.session_state.sel_line = l
                st.rerun()
        if st.button("🏠 กลับหน้าหลัก"):
            st.session_state.page = "Home"
            st.rerun()

    elif 'sel_batch' not in st.session_state:
        st.subheader(f"📍 Line: {st.session_state.sel_line} > เลือก Batch")
        p_df = load_csv("plan")
        active_b = []
        if not p_df.empty:
            # กรอง Batch ที่ยังไม่จบใน Google Sheet
            active_b = p_df[(p_df['line'] == st.session_state.sel_line) & (p_df['batch_status'] != "Finished")][
                'batch_number'].tolist()

        if active_b:
            cols = st.columns(3)
            for i, b in enumerate(active_b):
                if cols[i % 3].button(f"Batch: {b}", key=f"batch_{b}", use_container_width=True):
                    st.session_state.sel_batch = b
                    st.rerun()
        else:
            st.warning("ไม่มี Batch ที่กำลัง Running ใน Line นี้")
        if st.button("🔙 เปลี่ยน Line"):
            del st.session_state.sel_line
            st.rerun()

    else:
        st.subheader(f"✅ Line: {st.session_state.sel_line} | Batch: {st.session_state.sel_batch}")
        current_data = load_csv("box_status")

        box_no = st.text_input("Box Number", key="input_box_no")
        selected_stat = st.selectbox("สถานะ", ["เลือก Status", "AF", "HP", "HUP", "Sort", "PS", "Scrap"],
                                     key="input_stat")

        show_defect = selected_stat not in ["เลือก Status", "AF"]

        with st.form("box_form_action"):
            selected_defs = []
            if show_defect:
                selected_defs = st.multiselect("⚠️ เลือก Defects (บังคับระบุ)", DEFECT_LIST)

            c1, c2 = st.columns(2)
            if c1.form_submit_button("💾 บันทึกและกลับ", use_container_width=True):
                clean_box = str(box_no).strip()
                clean_batch = str(st.session_state.sel_batch).strip()

                is_duplicate = False
                if not current_data.empty:
                    # ตรวจสอบเลขซ้ำบน Google Sheet
                    dup_check = current_data[(current_data['Batch'].astype(str).str.strip() == clean_batch) &
                                             (current_data['Box'].astype(str).str.strip() == clean_box)]
                    if not dup_check.empty:
                        is_duplicate = True

                if not clean_box or selected_stat == "เลือก Status":
                    st.error("❌ กรุณากรอกเลขกล่องและเลือกสถานะ")
                elif show_defect and not selected_defs:
                    st.error(f"❌ สถานะ {selected_stat} ต้องระบุสาเหตุ (Defects)")
                elif is_duplicate:
                    st.error(f"❌ กล่องเลขที่ {clean_box} มีข้อมูลอยู่ในระบบแล้ว")
                else:
                    new_record = pd.DataFrame([{
                        "Time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Line": st.session_state.sel_line,
                        "Batch": st.session_state.sel_batch,
                        "Box": clean_box,
                        "Status": selected_stat,
                        "Defects": ",".join(selected_defs) if selected_defs else ""
                    }])
                    save_to_csv(new_record, "box_status")
                    st.success(f"บันทึกกล่อง {clean_box} เรียบร้อย!")
                    del st.session_state.sel_batch
                    st.rerun()

            if c2.form_submit_button("❌ ยกเลิก/กลับ", use_container_width=True):
                del st.session_state.sel_batch
                st.rerun()

# --- หน้า CAMERA (Online Version) ---
elif st.session_state.page == "Camera":
    st.title("📷 Camera Analysis")

    if 'sel_line' not in st.session_state:
        st.subheader("📍 เลือก Line")
        cols = st.columns(4)
        for i, l in enumerate(LINES):
            if cols[i % 4].button(l, key=f"cam_line_{l}", use_container_width=True):
                st.session_state.sel_line = l
                st.rerun()
        if st.button("🏠 กลับหน้าหลัก"):
            st.session_state.page = "Home"
            st.rerun()

    elif 'sel_batch' not in st.session_state:
        st.subheader(f"📍 Line: {st.session_state.sel_line} > เลือก Batch")
        p_df = load_csv("plan")
        active_b = []
        if not p_df.empty:
            active_b = p_df[(p_df['line'] == st.session_state.sel_line) & (p_df['batch_status'] != "Finished")][
                'batch_number'].tolist()

        if active_b:
            cols = st.columns(3)
            for i, b in enumerate(active_b):
                if cols[i % 3].button(f"Batch: {b}", key=f"cam_batch_{b}", use_container_width=True):
                    st.session_state.sel_batch = b
                    st.rerun()
        else:
            st.warning("⚠️ ไม่มี Batch ที่กำลัง Running ใน Line นี้")

        if st.button("🔙 เปลี่ยน Line"):
            del st.session_state.sel_line
            st.rerun()

    else:
        st.subheader(f"✅ Line: {st.session_state.sel_line} | Batch: {st.session_state.sel_batch}")
        with st.form("camera_full_form"):
            col1, col2 = st.columns(2)
            rate1 = col1.number_input("% Passing Rate (Camera 1)", min_value=0.0, max_value=100.0, step=0.01,
                                      format="%.2f")
            rate2 = col2.number_input("% Passing Rate (Camera 2)", min_value=0.0, max_value=100.0, step=0.01,
                                      format="%.2f")
            top_defs = st.multiselect("Top Defects (เลือกได้สูงสุด 4 อย่าง)", DEFECT_LIST, max_selections=4)

            st.divider()
            c1, c2 = st.columns(2)
            if c1.form_submit_button("💾 บันทึกข้อมูลลง Cloud", use_container_width=True):
                new_cam_data = pd.DataFrame([{
                    "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Line": st.session_state.sel_line,
                    "Batch": st.session_state.sel_batch,
                    "Rate_Cam1": rate1,
                    "Rate_Cam2": rate2,
                    "Top_Defects": ",".join(top_defs)
                }])
                save_to_csv(new_cam_data, "camera")
                st.success("บันทึกข้อมูลเรียบร้อยแล้ว!")
                del st.session_state.sel_batch
                st.rerun()

            if c2.form_submit_button("❌ ยกเลิก", use_container_width=True):
                del st.session_state.sel_batch
                st.rerun()

# --- หน้า REJECTION (Online Version) ---
elif st.session_state.page == "Rejection":
    st.title("🗑️ Rejection Recording")

    if 'sel_line' not in st.session_state:
        st.subheader("📍 เลือก Line")
        cols = st.columns(4)
        for i, l in enumerate(LINES):
            if cols[i % 4].button(l, key=f"rej_line_{l}", use_container_width=True):
                st.session_state.sel_line = l
                st.rerun()
        if st.button("🏠 กลับหน้าหลัก"):
            st.session_state.page = "Home"
            st.rerun()

    elif 'sel_batch' not in st.session_state:
        st.subheader(f"📍 Line: {st.session_state.sel_line} > เลือก Batch")
        p_df = load_csv("plan")
        active_b = []
        if not p_df.empty:
            active_b = p_df[(p_df['line'] == st.session_state.sel_line) & (p_df['batch_status'] != "Finished")][
                'batch_number'].tolist()

        if active_b:
            cols = st.columns(3)
            for i, b in enumerate(active_b):
                if cols[i % 3].button(f"Batch: {b}", key=f"rej_batch_{b}", use_container_width=True):
                    st.session_state.sel_batch = b
                    st.rerun()
        else:
            st.warning("⚠️ ไม่มี Batch ที่กำลัง Running ใน Line นี้")

        if st.button("🔙 เปลี่ยน Line"):
            del st.session_state.sel_line
            st.rerun()

    else:
        st.subheader(f"✅ Line: {st.session_state.sel_line} | Batch: {st.session_state.sel_batch}")
        with st.form("rejection_full_form"):
            st.write("### ⚖️ น้ำหนักงานเสียแยกตามจุด (kg)")
            h1, h2, h3 = st.columns(3)
            h1.info("**ATS Machine**")
            h2.info("**Printing Machine**")
            h3.info("**Camera Machine**")

            r1, r2, r3 = st.columns(3)
            w_ats = r1.number_input("ATS Weight", min_value=0.0, step=0.001, format="%.3f",
                                    label_visibility="collapsed")
            w_print = r2.number_input("Print Weight", min_value=0.0, step=0.001, format="%.3f",
                                      label_visibility="collapsed")
            w_cam = r3.number_input("Cam Weight", min_value=0.0, step=0.001, format="%.3f",
                                    label_visibility="collapsed")

            st.divider()
            c1, c2 = st.columns(2)
            if c1.form_submit_button("💾 บันทึกข้อมูลลง Cloud", use_container_width=True):
                new_rej_data = pd.DataFrame([{
                    "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Line": st.session_state.sel_line,
                    "Batch": st.session_state.sel_batch,
                    "ATS_kg": w_ats,
                    "Print_kg": w_print,
                    "Cam_kg": w_cam
                }])
                save_to_csv(new_rej_data, "rejection")
                st.success("บันทึกน้ำหนักงานเสียสำเร็จ!")
                del st.session_state.sel_batch
                st.rerun()

            if c2.form_submit_button("❌ ยกเลิก", use_container_width=True):
                del st.session_state.sel_batch
                st.rerun()

# --- หน้า BACKLOG (Online Version) ---
elif st.session_state.page == "Backlog":
    st.title("⏳ Backlog Management")

    if 'sel_line' not in st.session_state:
        st.subheader("📍 1. เลือก Line เพื่อลงข้อมูล Backlog")
        cols = st.columns(4)
        for i, l in enumerate(LINES):
            if cols[i % 4].button(l, key=f"back_l_{l}", use_container_width=True):
                st.session_state.sel_line = l
                st.rerun()
        st.write("---")
        if st.button("🏠 กลับหน้าหลัก", key="back_home_btn"):
            st.session_state.page = "Home"
            st.rerun()

    elif 'sel_batch' not in st.session_state:
        st.subheader(f"📍 Line: {st.session_state.sel_line} > 2. เลือก Batch")
        p_df = load_csv("plan")
        active_b = []
        if not p_df.empty:
            active_b = p_df[(p_df['line'] == st.session_state.sel_line) & (p_df['batch_status'] != "Finished")][
                'batch_number'].tolist()

        if active_b:
            cols = st.columns(3)
            for i, b in enumerate(active_b):
                if cols[i % 3].button(f"Batch: {b}", key=f"back_b_{b}", use_container_width=True):
                    st.session_state.sel_batch = b
                    st.rerun()
        else:
            st.warning("⚠️ ไม่พบ Batch ที่กำลังดำเนินการ (Running) ใน Line นี้")

        st.write("---")
        if st.button("🔙 เปลี่ยน Line", key="change_line_back"):
            del st.session_state.sel_line
            st.rerun()

    else:
        st.subheader(f"📝 ลงข้อมูล Backlog")
        st.info(f"✅ **Line:** {st.session_state.sel_line}  |  🆔 **Batch:** {st.session_state.sel_batch}")

        with st.form("backlog_form_v2"):
            st.write("📊 **ระบุจำนวนงานค้าง (Capsules)**")
            c1, c2, c3 = st.columns(3)
            qty_ats = c1.number_input("ATS", min_value=0, step=1)
            qty_prt = c2.number_input("Printing", min_value=0, step=1)
            qty_cam = c3.number_input("Camera", min_value=0, step=1)

            st.write("---")
            c_btn1, c_btn2 = st.columns(2)
            if c_btn1.form_submit_button("💾 บันทึกข้อมูลลง Cloud", use_container_width=True):
                new_backlog = pd.DataFrame([{
                    "Time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Line": st.session_state.sel_line,
                    "Batch": st.session_state.sel_batch,
                    "ATS_caps": qty_ats,
                    "Print_caps": qty_prt,
                    "Cam_caps": qty_cam,
                    "Total_caps": qty_ats + qty_prt + qty_cam
                }])
                save_to_csv(new_backlog, "backlog")
                st.success(f"✅ บันทึก Backlog สำเร็จ!")
                del st.session_state.sel_batch
                st.rerun()

            if c_btn2.form_submit_button("❌ ยกเลิก/กลับ", use_container_width=True):
                del st.session_state.sel_batch
                st.rerun()

# --- หน้า RE-PASS (Online Version: เชื่อม Google Sheets) ---
elif st.session_state.page == "Re_pass":
    st.title("🔄 Re-pass Management (Online)")

    df_box = load_csv("box_status").fillna("")

    # --- STEP 1: เลือก Line ---
    if 'sel_line_re' not in st.session_state and 'sel_batch_re' not in st.session_state:
        st.subheader("📍 1. เลือก Line ที่ต้องการจัดการ")
        active_lines = []
        if not df_box.empty:
            active_lines = df_box[df_box['Status'] != 'AF']['Line'].unique().tolist()

        cols = st.columns(3)
        for i, line in enumerate(active_lines):
            if cols[i % 3].button(f"Line: {line}", key=f"btn_line_{line}", use_container_width=True):
                st.session_state.sel_line_re = line
                st.rerun()

        next_idx = len(active_lines)
        if cols[next_idx % 3].button("➕ Other (ระบุเอง)", key="btn_other_re", use_container_width=True):
            st.session_state.sel_line_re = "Other"
            st.session_state.sel_batch_re = "Other"
            st.rerun()

        st.write("---")
        if st.button("🏠 กลับหน้าหลัก"):
            st.session_state.page = "Home"
            st.rerun()

    # --- STEP 2: เลือก Batch ---
    elif 'sel_line_re' in st.session_state and 'sel_batch_re' not in st.session_state:
        line_target = st.session_state.sel_line_re
        st.subheader(f"📍 2. เลือก Batch ใน {line_target} ที่มีงานเสีย")
        active_rej_batches = []
        if not df_box.empty:
            active_rej_batches = df_box[(df_box['Line'] == line_target) & (df_box['Status'] != 'AF')][
                'Batch'].unique().tolist()

        if not active_rej_batches:
            st.warning(f"ไม่พบงานเสียคงค้างใน {line_target}")
            if st.button("⬅️ กลับไปเลือก Line"):
                del st.session_state.sel_line_re
                st.rerun()
        else:
            cols = st.columns(3)
            for i, batch in enumerate(active_rej_batches):
                if cols[i % 3].button(f"Batch: {batch}", key=f"btn_batch_{batch}", use_container_width=True):
                    st.session_state.sel_batch_re = batch
                    st.rerun()
            if st.button("⬅️ กลับไปเลือก Line"):
                del st.session_state.sel_line_re
                st.rerun()

    # --- STEP 3: หน้าฟอร์มบันทึก ---
    else:
        line_target = st.session_state.get('sel_line_re', 'Other')
        batch_target = st.session_state.sel_batch_re
        st.subheader(f"🔄 บันทึกข้อมูล Re-pass ลง Cloud")
        st.caption(f"Line: {line_target} | Batch: {batch_target}")

        if batch_target == "Other":
            f_line = st.selectbox("ระบุ Line", LINES)
            f_batch = st.text_input("ระบุเลข Batch")
            f_box_num = st.text_input("ระบุเลขกล่อง")
            current_stat, old_defect_val = "N/A", "ระบุเอง"
        else:
            f_line = line_target
            f_batch = batch_target
            boxes_to_fix = df_box[(df_box['Batch'] == batch_target) & (df_box['Status'] != 'AF')]
            box_list = boxes_to_fix['Box'].unique().tolist()
            f_box_num = st.selectbox("เลือกเลขกล่อง", box_list)

            if f_box_num:
                match = boxes_to_fix[boxes_to_fix['Box'] == f_box_num].iloc[-1]
                current_stat = match['Status']
                old_defect_val = match['Defects'] if match['Defects'] != "" else "ไม่มี Defect"
            else:
                current_stat, old_defect_val = "N/A", "N/A"

        st.info(f"📌 สถานะเดิม: {current_stat} | Defect เดิม: {old_defect_val}")
        mode = st.radio("ประเภทงาน", ["Online", "Offline"], horizontal=True)
        new_stat = st.selectbox("สถานะหลัง Re-pass", ["AF", "Sort", "Scrap", "PS"], key="repass_stat_select")
        show_def_input = new_stat != "AF"

        with st.form("repass_final_action"):
            new_def = []
            final_reason = ""
            if show_def_input:
                st.warning(f"⚠️ กรุณาระบุรายละเอียดสำหรับสถานะ {new_stat}")
                new_def = st.multiselect("🔴 ระบุ Defect (จำเป็นต้องเลือก)", DEFECT_LIST)
                final_reason = st.text_area("ระบุเหตุผลเพิ่มเติม")

            c1, c2 = st.columns(2)
            if c1.form_submit_button("💾 บันทึกการ Re-pass ลง Cloud", use_container_width=True):
                if not f_batch or not f_box_num:
                    st.error("❌ กรุณาระบุ Batch และเลขกล่อง")
                elif show_def_input and not new_def:
                    st.error(f"❌ สถานะ {new_stat} ต้องระบุ Defect อย่างน้อย 1 อย่าง")
                else:
                    # 1. บันทึกประวัติ Re-pass ลง Sheet "re_pass"
                    new_rp_record = pd.DataFrame([{
                        "Time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Line": f_line, "Batch": f_batch, "Box": f_box_num,
                        "Previous_Status": current_stat, "Result_Status": new_stat,
                        "New_Defects": ",".join(new_def), "Type": mode,
                        "Reason": "Normal Re-pass" if new_stat == "AF" else final_reason
                    }])
                    save_to_csv(new_rp_record, "re_pass")

                    # 2. อัปเดตสถานะกลับไปที่ Sheet "box_status" (ถ้าไม่ใช่เคส Other)
                    if batch_target != "Other":
                        df_box.loc[(df_box['Batch'].astype(str) == str(f_batch)) & (
                                df_box['Box'].astype(str) == str(f_box_num)), ['Status', 'Defects']] = [new_stat,
                                                                                                        ",".join(
                                                                                                            new_def)]
                        conn.update(worksheet="box_status", data=df_box)
                        st.cache_data.clear()

                    st.success("✅ บันทึกสำเร็จ!")
                    for key in ['sel_line_re', 'sel_batch_re']:
                        if key in st.session_state: del st.session_state[key]
                    st.rerun()

            if c2.form_submit_button("❌ ยกเลิก", use_container_width=True):
                for key in ['sel_line_re', 'sel_batch_re']:
                    if key in st.session_state: del st.session_state[key]
                st.rerun()

# --- หน้า REPORT (Online Version) ---
elif st.session_state.page == "Report":
    st.title("📊 Production Analytics Dashboard (Online)")

    df_box = load_csv("box_status").fillna("")
    df_plan = load_csv("plan").fillna("")
    df_rej = load_csv("rejection").fillna("")
    df_cam = load_csv("camera").fillna("")
    df_repass = load_csv("re_pass").fillna("")
    df_backlog_file = load_csv("backlog").fillna(0)

    if df_box.empty:
        st.warning("⚠️ ยังไม่มีข้อมูลสำหรับการวิเคราะห์")
        if st.button("🏠 กลับหน้าหลัก"):
            st.session_state.page = "Home"
            st.rerun()
        st.stop()

    df_box['Time'] = pd.to_datetime(df_box['Time'])

    with st.expander("🔍 ตัวกรองข้อมูล (Filters)", expanded=True):
        c1, c2 = st.columns(2)
        line_options = ["เลือกทั้งหมด"] + LINES
        selected_line_input = c1.multiselect("เลือก Line", line_options, default=["เลือกทั้งหมด"])
        f_line = LINES if "เลือกทั้งหมด" in selected_line_input else selected_line_input
        min_date = df_box['Time'].min().date()
        max_date = df_box['Time'].max().date()
        f_date = c2.date_input("ช่วงวันที่", [min_date, max_date])

    mask = (df_box['Line'].isin(f_line)) & (df_box['Time'].dt.date >= f_date[0]) & (df_box['Time'].dt.date <= f_date[1])
    df_filtered = df_box[mask].copy()
    df_latest = df_filtered.sort_values('Time').drop_duplicates(subset=['Batch', 'Box'], keep='last')

    t1, t2, t3, t_re, t4, t5 = st.tabs(
        ["📦 Total Output", "🎯 Quality Metrics", "📷 Camera Analysis", "🔄 Re-pass Analysis", "📈 Progress & Backlog",
         "📋 Box Detail"])

    with t1:
        st.subheader("ยอดการผลิตรวม")
        out_chart = df_latest.groupby(['Line', 'Status']).size().reset_index(name='Count')
        st.plotly_chart(
            px.bar(out_chart, x='Line', y='Count', color='Status', color_discrete_map=STATUS_COLORS, barmode='group',
                   text_auto=True), use_container_width=True)

    with t2:
        st.subheader("อัตราส่วน % Quality Metrics")
        metrics_data = []
        for line in f_line:
            line_boxes = df_latest[df_latest['Line'] == line]
            if not line_boxes.empty:
                theoretical_w = len(line_boxes) * 12.5
                line_rej = df_rej[df_rej['Line'] == line] if not df_rej.empty else pd.DataFrame()
                total_rej_kg = line_rej[['ATS_kg', 'Print_kg', 'Cam_kg']].sum().sum() if not line_rej.empty else 0
                rej_p = (total_rej_kg / theoretical_w) * 100 if theoretical_w > 0 else 0
                metrics_data.append({"Line": line, "Yield %": 100 - rej_p, "Rejection %": rej_p})
        if metrics_data:
            st.plotly_chart(px.bar(pd.DataFrame(metrics_data), x='Line', y=['Yield %', 'Rejection %'], barmode='stack',
                                   color_discrete_sequence=['#2ecc71', '#e74c3c'], text_auto='.2f'),
                            use_container_width=True)

    with t3:
        st.subheader("📷 Camera Performance")
        if not df_cam.empty:
            cam_table = df_cam[df_cam['Line'].isin(f_line)].copy()
            st.dataframe(cam_table[['Line', 'Rate_Cam1', 'Rate_Cam2']].style.format("{:.2f}%",
                                                                                    subset=['Rate_Cam1', 'Rate_Cam2']),
                         use_container_width=True, hide_index=True)

    with t_re:
        st.subheader("🔄 Re-pass Performance")
        if not df_repass.empty:
            df_rp_f = df_repass[df_repass['Line'].isin(f_line)]
            if not df_rp_f.empty:
                rp_res = df_rp_f['Result_Status'].value_counts().reset_index()
                st.plotly_chart(px.pie(rp_res, values='count', names='Result_Status', color='Result_Status',
                                       color_discrete_map={'AF': '#2ecc71', 'Sort': '#f1c40f', 'Scrap': '#e74c3c'}),
                                use_container_width=True)

    with t4:
        st.subheader("📈 Progress & Backlog")
        if not df_plan.empty:
            actual_af = df_latest[df_latest['Status'] == 'AF'].groupby('Batch').size().reset_index(name='Actual_AF')
            latest_backlog = df_backlog_file.sort_values('Time').drop_duplicates(subset=['Batch'],
                                                                                 keep='last') if not df_backlog_file.empty else pd.DataFrame()
            df_p = pd.merge(df_plan[['batch_number', 'need_af_box']], actual_af, left_on='batch_number',
                            right_on='Batch', how='left').fillna(0)
            st.dataframe(df_p, use_container_width=True, hide_index=True)

    with t5:
        st.subheader("📋 Box Detail")
        st.dataframe(df_filtered.sort_values(by=['Batch', 'Box']), use_container_width=True, hide_index=True)

    st.divider()
    if st.button("🏠 กลับหน้าหลัก"):
        st.session_state.page = "Home"
        st.rerun()

# --- หน้า ACCOUNT (Online Version) ---
elif st.session_state.page == "Account":
    st.title("👥 จัดการบัญชีผู้ใช้ (Online)")
    acc_df = load_csv("accounts")

    tab_add, tab_manage = st.tabs(["➕ เพิ่มผู้ใช้ใหม่", "⚙️ จัดการ/แก้ไขข้อมูล"])

    with tab_add:
        with st.form("add_acc_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            fn = c1.text_input("ชื่อ-นามสกุล")
            eid = c2.text_input("รหัสพนักงาน")
            un = c1.text_input("Username")
            pw = c2.text_input("Password")
            rl = st.selectbox("ตำแหน่ง", ["employee", "supervisor", "admin"])
            if st.form_submit_button("💾 บันทึกและสร้างบัญชี", use_container_width=True):
                if fn and un and pw:
                    if not acc_df.empty and un in acc_df['username'].astype(str).values:
                        st.error("❌ Username นี้มีในระบบแล้ว")
                    else:
                        new_acc = pd.DataFrame([{"fullname": fn, "emp_id": eid, "username": un, "password": pw,
                                                 "role": rl, "first_login": True}])
                        save_to_csv(new_acc, "accounts")
                        st.success(f"✅ เพิ่มผู้ใช้ {fn} เรียบร้อยแล้ว")
                        st.rerun()

    with tab_manage:
        if not acc_df.empty:
            st.dataframe(acc_df[['fullname', 'emp_id', 'username', 'role']], use_container_width=True, hide_index=True)
            target_user = st.selectbox("เลือกบัญชีที่ต้องการจัดการ", acc_df['username'].tolist())
            user_row = acc_df[acc_df['username'] == target_user].iloc[0]
            new_role = st.selectbox("เปลี่ยนตำแหน่งเป็น", ["employee", "supervisor", "admin"],
                                    index=["employee", "supervisor", "admin"].index(user_row['role']))

            c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1.5])
            if c2.button("🔄 อัปเดตตำแหน่ง", use_container_width=True):
                acc_df.loc[acc_df['username'] == target_user, 'role'] = new_role
                conn.update(worksheet="accounts", data=acc_df)
                st.cache_data.clear()
                st.success("อัปเดตเรียบร้อย!")
                st.rerun()

            if c3.button("🗑️ ลบผู้ใช้", use_container_width=True, type="primary"):
                acc_df = acc_df[acc_df['username'] != target_user]
                conn.update(worksheet="accounts", data=acc_df)
                st.cache_data.clear()
                st.success("ลบเรียบร้อย!")
                st.rerun()

    if st.button("🏠 กลับหน้าหลัก"):
        st.session_state.page = "Home"
        st.rerun()
