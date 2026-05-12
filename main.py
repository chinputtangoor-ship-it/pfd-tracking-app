import streamlit as st
import pandas as pd
import os
import random
import string
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

# ==========================================
# 1. การตั้งค่าเบื้องต้นและการจัดการไฟล์
# ==========================================
st.set_page_config(page_title="Post Production System", layout="wide")

if not os.path.exists('data'):
    os.makedirs('data')

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


# --- ฟังก์ชันช่วยจัดการข้อมูล (Robust Functions) ---
def load_csv(filename):
    path = f"data/{filename}.csv"
    if os.path.exists(path):
        try:
            df = pd.read_csv(path)
            if df.empty: return pd.DataFrame()
            return df
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

def save_to_csv(df_new, filename):
    path = f"data/{filename}.csv"
    if os.path.exists(path):
        try:
            df_old = pd.read_csv(path)
            df_final = pd.concat([df_old, df_new], ignore_index=True)
        except:
            df_final = df_new
    else:
        df_final = df_new
    df_final.to_csv(path, index=False)


def validate_inputs(inputs_dict):
    for label, value in inputs_dict.items():
        if value is None or (isinstance(value, str) and "เลือก" in value) or str(value).strip() == "":
            st.error(f"❌ กรุณาระบุข้อมูล: {label}")
            return False
    return True


# สร้างบัญชีเริ่มต้น
if not os.path.exists("data/accounts.csv"):
    pd.DataFrame([{"fullname": "Administrator", "emp_id": "001", "username": "admin", "password": "Password12",
                   "role": "admin", "first_login": False}]).to_csv("data/accounts.csv", index=False)

# ==========================================
# 2. ระบบ LOGIN & SESSION
# ==========================================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'page' not in st.session_state: st.session_state.page = "Home"

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>POST PRODUCTION SYSTEM</h1>", unsafe_allow_html=True)
    col_l, col_m, col_r = st.columns([1, 1.2, 1])
    with col_m:
        with st.container(border=True):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("Login", use_container_width=True, type="primary"):
                acc_df = load_csv("accounts")
                if not acc_df.empty:
                    user_match = acc_df[acc_df['username'] == u]
                    if not user_match.empty and str(user_match.iloc[0]['password']) == p:
                        st.session_state.logged_in = True
                        st.session_state.user_data = user_match.iloc[0].to_dict()
                        st.rerun()
                    else:
                        st.error("Username หรือ Password ไม่ถูกต้อง")
                else:
                    st.error("ระบบขัดข้อง: ไม่พบฐานข้อมูลผู้ใช้")
    st.stop()

# First Login Check
if st.session_state.user_data.get('first_login', True):
    st.title("🔒 เปลี่ยนรหัสผ่านใหม่ (ครั้งแรก)")
    new_p = st.text_input("New Password (8 หลัก)", type="password")
    confirm_p = st.text_input("Confirm Password", type="password")
    if st.button("ยืนยัน"):
        if len(new_p) == 8 and sum(1 for c in new_p if c.isalpha()) >= 2 and new_p == confirm_p:
            acc_df = load_csv("accounts")
            acc_df.loc[acc_df['username'] == st.session_state.user_data['username'], ['password', 'first_login']] = [
                new_p, False]
            acc_df.to_csv("data/accounts.csv", index=False)
            st.session_state.user_data['first_login'] = False
            st.success("สำเร็จ! กรุณารอสักครู่...");
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

# --- หน้าจัดการแผนงาน (PLAN) - ฉบับสมบูรณ์ (3 Tabs) ---
# ==========================================
elif st.session_state.page == "Plan":
    st.title("📅 Production Planning Management")

    # ดึงข้อมูลแผนงาน
    plan_df = load_csv("plan")

    # รายชื่อคอลัมน์ทั้งหมด (23 คอลัมน์)
    PLAN_COLUMNS = [
        "line", "batch_number", "sap_batch", "production_order", "inspection_lot",
        "sales_order", "sales_order_item", "fert_code", "semifinish_code",
        "item_qty", "need_af_box", "customer_name", "planned_finish_date",
        "to_be_desp_on", "metal_detector", "print_type", "country",
        "box_packing", "ink_cap", "roller_des_cap", "ink_body",
        "roller_des_body", "batch_status"
    ]

    # สร้าง 3 Tabs ตามตำแหน่งในรูปภาพที่คุณวงไว้
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
            st.info("ยังไม่มีข้อมูลแผนงานในระบบ")

    # --- TAB 2: จัดการ/เพิ่มแผนใหม่ ---
    with tab_m:
        if st.session_state.user_data['role'] != 'employee':
            st.subheader("➕ เพิ่มแผนการผลิตใหม่")
            with st.form("full_plan_form", clear_on_submit=True):
                # แถวที่ 1
                r1_c1, r1_c2, r1_c3, r1_c4 = st.columns(4)
                p_line = r1_c1.selectbox("Line", ["เลือก Line"] + LINES)
                p_batch = r1_c2.text_input("Batch Number")
                p_sap = r1_c3.text_input("SAP Batch Number")
                p_order = r1_c4.text_input("Production Order")

                # แถวที่ 2
                r2_c1, r2_c2, r2_c3, r2_c4 = st.columns(4)
                p_inspec = r2_c1.text_input("Inspection Lot")
                p_so = r2_c2.text_input("Sales Order")
                p_so_item = r2_c3.text_input("SO Item")
                p_fert = r2_c4.text_input("FERT Code")

                # แถวที่ 3
                r3_c1, r3_c2, r3_c3, r3_c4 = st.columns(4)
                p_semi = r3_c1.text_input("Semifinish Code")
                p_qty = r3_c2.number_input("Item Qty", min_value=0.000, step=0.001, format="%.3f")
                p_af_box = r3_c3.number_input("Need AF Box", min_value=0.000, step=0.001, format="%.3f")
                p_cust = r3_c4.selectbox("Customer Name", [
                    "ACG NORTH AMERCA LLC", "FAME Pharma Pte ltd", "PT.ACG Indonesia",
                    "COMMUNITY PHARMACY PUBLIC", "ERNEST CHEMIST LTD", "Gel strength Co Ltd (Head office)"
                ])

                # แถวที่ 4
                r4_c1, r4_c2, r4_c3, r4_c4 = st.columns(4)
                p_finish_date = r4_c1.date_input("Planned Finish Date")
                p_desp_date = r4_c2.date_input("To be Desp. on")
                p_metal = r4_c3.selectbox("Metal Detector", ["Normal", "Iron Oxide"])
                p_print = r4_c4.selectbox("Print Type", ["P", "U"])

                # แถวที่ 5
                r5_c1, r5_c2, r5_c3, r5_c4 = st.columns(4)
                p_country = r5_c1.selectbox("Country",
                                            ["Thailand", "Indonesia", "USA", "Ghana", "Myanma", "Singapore", "Vietnam"])
                p_box = r5_c2.selectbox("Box Packing", [
                    "Box 660", "Box 675", "Box 705",
                    "Box 705+Liner", "Box 760+EPS Sheet",
                    "Box Tabsule", "Box Fsample"
                ])

                ink_options = [
                    "None", "RMI010004 Black ACG", "RMI010021 White ACG", "RMI010182 Black ACG/TEK",
                    "RMI010017 Red ACG", "RMI010002 Black TEK", "RMI010057 Green TEK", "RMI010033 Yellow/Gold TEK"
                ]

                p_ink_c = r5_c3.selectbox("Ink Cap", ink_options)
                p_roll_c = r5_c4.text_input("Roller Des. Cap")

                # แถวที่ 6
                r6_c1, r6_c2, r6_c3, r6_c4 = st.columns(4)
                p_ink_b = r6_c1.selectbox("Ink Body", ink_options)
                p_roll_b = r6_c2.text_input("Roller Des. Body")
                p_status = r6_c3.selectbox("Batch Status", ["Running", "Finished"])

                if st.form_submit_button("➕ บันทึกแผนงานลงระบบ", use_container_width=True):
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
                # กรองเฉพาะงานที่ยังไม่จบ (Running)
                running_df = plan_df[plan_df['batch_status'] == "Running"].copy()

                if not running_df.empty:
                    # แสดงข้อมูลเป็นแถว พร้อมปุ่มจบงาน
                    for idx, row in running_df.iterrows():
                        with st.container():
                            col_info, col_btn = st.columns([4, 1])
                            with col_info:
                                st.markdown(f"📍 **Line:** {row['line']} | **Batch:** `{row['batch_number']}`")
                                st.caption(f"FERT: {row['fert_code']} | Customer: {row['customer_name']}")
                            with col_btn:
                                if st.button(f"🏁 จบงาน", key=f"fin_{row['batch_number']}", use_container_width=True,
                                             type="primary"):
                                    # อัปเดตสถานะใน DataFrame และบันทึกลง CSV
                                    plan_df.loc[
                                        plan_df['batch_number'] == row['batch_number'], 'batch_status'] = "Finished"
                                    plan_df.to_csv("data/plan.csv", index=False)
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

# --- หน้า BOX STATUS (แก้ไขให้แสดง Defect ทันทีและบันทึกได้ทุกสถานะ) ---
elif st.session_state.page == "Box_Status":
    st.title("📦 Box Status Recording")

    if 'sel_line' not in st.session_state:
        # (ส่วนเลือก Line เหมือนเดิม)
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
        # (ส่วนเลือก Batch เหมือนเดิม)
        st.subheader(f"📍 Line: {st.session_state.sel_line} > เลือก Batch")
        p_df = load_csv("plan")
        active_b = p_df[(p_df['line'] == st.session_state.sel_line) & (p_df['batch_status'] != "Finished")][
            'batch_number'].tolist() if not p_df.empty else []

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

        # --- ส่วนสำคัญ: ใช้ container เพื่อให้สถานะอัปเดต Defect ทันทีโดยไม่ต้องรอส่งฟอร์ม ---
        # เราย้าย selectbox ออกมาคุมข้างนอกฟอร์มเล็กน้อยเพื่อให้เกิดการ rerun เมื่อเปลี่ยนค่า
        box_no = st.text_input("Box Number", key="input_box_no")
        selected_stat = st.selectbox("สถานะ", ["เลือก Status", "AF", "HP", "HUP", "Sort", "PS", "Scrap"],
                                     key="input_stat")

        # เช็คเงื่อนไขแสดงช่อง Defect ทันที
        show_defect = selected_stat not in ["เลือก Status", "AF"]

        with st.form("box_form_action"):
            # ถ้าเป็นงานเสีย ให้แสดงช่อง multiselect ทันที
            selected_defs = []
            if show_defect:
                selected_defs = st.multiselect("⚠️ เลือก Defects (บังคับระบุ)", DEFECT_LIST)

            c1, c2 = st.columns(2)
            if c1.form_submit_button("💾 บันทึกและกลับ", use_container_width=True):
                # Clean Data
                clean_box = str(box_no).strip()
                clean_batch = str(st.session_state.sel_batch).strip()

                # ตรวจสอบเลขซ้ำ
                is_duplicate = False
                if not current_data.empty:
                    dup_check = current_data[
                        (current_data['Batch'].astype(str).str.strip() == clean_batch) &
                        (current_data['Box'].astype(str).str.strip() == clean_box)
                        ]
                    if not dup_check.empty:
                        is_duplicate = True

                # --- Validation Logic ---
                if not clean_box or selected_stat == "เลือก Status":
                    st.error("❌ กรุณากรอกเลขกล่องและเลือกสถานะ")

                # ถ้าไม่ใช่ AF ต้องมี Defect อย่างน้อย 1 อย่าง
                elif show_defect and not selected_defs:
                    st.error(f"❌ สถานะ {selected_stat} ต้องระบุสาเหตุ (Defects)")

                elif is_duplicate:
                    st.error(f"❌ กล่องเลขที่ {clean_box} มีข้อมูลอยู่ในระบบแล้ว")

                else:
                    # บันทึกข้อมูล
                    new_data = pd.DataFrame([{
                        "Time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Line": st.session_state.sel_line,
                        "Batch": st.session_state.sel_batch,
                        "Box": clean_box,
                        "Status": selected_stat,
                        "Defects": ",".join(selected_defs) if selected_defs else ""
                    }])
                    save_to_csv(new_data, "box_status")

                    st.success(f"บันทึกกล่อง {clean_box} เรียบร้อย!")
                    del st.session_state.sel_batch
                    st.rerun()

            if c2.form_submit_button("❌ ยกเลิก/กลับ", use_container_width=True):
                del st.session_state.sel_batch
                st.rerun()

# --- หน้า CAMERA (Full Version) ---
elif st.session_state.page == "Camera":
    st.title("📷 Camera Analysis")

    # ขั้นตอนที่ 1: เลือก Line
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

    # ขั้นตอนที่ 2: เลือก Batch (แบบ List)
    elif 'sel_batch' not in st.session_state:
        st.subheader(f"📍 Line: {st.session_state.sel_line} > เลือก Batch")
        p_df = load_csv("plan")
        active_b = []
        if not p_df.empty and 'batch_status' in p_df.columns:
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

    # ขั้นตอนที่ 3: ลงข้อมูล
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
            if c1.form_submit_button("💾 บันทึกข้อมูล", use_container_width=True, type="primary"):
                new_data = pd.DataFrame([{
                    "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Line": st.session_state.sel_line,
                    "Batch": st.session_state.sel_batch,
                    "Rate_Cam1": rate1,
                    "Rate_Cam2": rate2,
                    "Top_Defects": ",".join(top_defs)
                }])
                save_to_csv(new_data, "camera")
                st.success("บันทึกข้อมูลเรียบร้อยแล้ว!")
                del st.session_state.sel_batch  # บันทึกแล้วให้กลับไปเลือก Batch ใหม่
                st.rerun()

            if c2.form_submit_button("❌ ยกเลิก", use_container_width=True):
                del st.session_state.sel_batch
                st.rerun()

# --- หน้า REJECTION (Full Version) ---
elif st.session_state.page == "Rejection":
    st.title("🗑️ Rejection Recording")

    # ขั้นตอนที่ 1: เลือก Line
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

    # ขั้นตอนที่ 2: เลือก Batch (แบบ List)
    elif 'sel_batch' not in st.session_state:
        st.subheader(f"📍 Line: {st.session_state.sel_line} > เลือก Batch")
        p_df = load_csv("plan")
        active_b = []
        if not p_df.empty and 'batch_status' in p_df.columns:
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

    # ขั้นตอนที่ 3: ลงข้อมูล
    else:
        st.subheader(f"✅ Line: {st.session_state.sel_line} | Batch: {st.session_state.sel_batch}")
        with st.form("rejection_full_form"):
            st.write("### ⚖️ น้ำหนักงานเสียแยกตามจุด (kg)")

            # ส่วนหัวคอลัมน์
            h1, h2, h3 = st.columns(3)
            h1.info("**ATS Machine**")
            h2.info("**Printing Machine**")
            h3.info("**Camera Machine**")

            # ส่วนช่องกรอกข้อมูล
            r1, r2, r3 = st.columns(3)
            w_ats = r1.number_input("ATS Weight", min_value=0.0, step=0.001, format="%.3f",
                                    label_visibility="collapsed")
            w_print = r2.number_input("Print Weight", min_value=0.0, step=0.001, format="%.3f",
                                      label_visibility="collapsed")
            w_cam = r3.number_input("Cam Weight", min_value=0.0, step=0.001, format="%.3f",
                                    label_visibility="collapsed")

            st.divider()
            c1, c2 = st.columns(2)
            if c1.form_submit_button("💾 บันทึกข้อมูล", use_container_width=True, type="primary"):
                new_data = pd.DataFrame([{
                    "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Line": st.session_state.sel_line,
                    "Batch": st.session_state.sel_batch,
                    "ATS_kg": w_ats,
                    "Print_kg": w_print,
                    "Cam_kg": w_cam
                }])
                save_to_csv(new_data, "rejection")
                st.success("บันทึกน้ำหนักงานเสียสำเร็จ!")
                del st.session_state.sel_batch
                st.rerun()

            if c2.form_submit_button("❌ ยกเลิก", use_container_width=True):
                del st.session_state.sel_batch
                st.rerun()

# --- หน้า BACKLOG (ปรับปรุงใหม่: บันทึกแล้วเด้งไปเลือก Batch) ---
elif st.session_state.page == "Backlog":
    st.title("⏳ Backlog Management")

    # --- STEP 1: เลือก Line ---
    if 'sel_line' not in st.session_state:
        st.subheader("📍 1. เลือก Line เพื่อลงข้อมูล Backlog")
        cols = st.columns(4)
        for i, l in enumerate(LINES):
            if cols[i % 4].button(l, key=f"back_l_{l}", use_container_width=True):
                st.session_state.sel_line = l
                st.rerun()

        st.divider()
        if st.button("🏠 กลับหน้าหลัก", use_container_width=True):
            st.session_state.page = "Home"
            st.rerun()

    # --- STEP 2: เลือก Batch ---
    elif 'sel_batch' not in st.session_state:
        st.subheader(f"📍 Line: {st.session_state.sel_line} > 2. เลือก Batch")
        p_df = load_csv("plan").fillna("")

        # กรองเฉพาะ Batch ที่ยังไม่จบ (Finished) ใน Line ที่เลือก
        if not p_df.empty:
            active_b = p_df[(p_df['line'] == st.session_state.sel_line) & (p_df['batch_status'] != "Finished")][
                'batch_number'].tolist()
        else:
            active_b = []

        if active_b:
            cols = st.columns(3)
            for i, b in enumerate(active_b):
                if cols[i % 3].button(f"Batch: {b}", key=f"back_b_{b}", use_container_width=True):
                    st.session_state.sel_batch = b
                    st.rerun()
        else:
            st.warning("⚠️ ไม่พบ Batch ที่กำลังดำเนินการ (Running) ใน Line นี้")
            st.info("กรุณาไปเพิ่มแผนการผลิตที่หน้า Plan ก่อน")

        st.divider()
        if st.button("🔙 เปลี่ยน Line", use_container_width=True):
            del st.session_state.sel_line
            st.rerun()

    # --- STEP 3: ฟอร์มกรอกข้อมูล Backlog ---
    else:
        st.subheader(f"📝 ลงข้อมูล Backlog")
        st.info(f"**Line:** {st.session_state.sel_line} | **Batch:** {st.session_state.sel_batch}")

        with st.form("backlog_form_v2"):
            st.write("ระบุจำนวนงานค้าง (Capsules)")
            c1, c2, c3 = st.columns(3)
            qty_ats = c1.number_input("ATS", min_value=0, step=1, help="จำนวนงานค้างที่แผนก ATS")
            qty_prt = c2.number_input("Printing", min_value=0, step=1, help="จำนวนงานค้างที่แผนก Printing")
            qty_cam = c3.number_input("Camera", min_value=0, step=1, help="จำนวนงานค้างที่แผนก Camera")

            st.write("---")
            c_btn1, c_btn2 = st.columns(2)

            if c_btn1.form_submit_button("💾 บันทึกข้อมูล"):
                # เตรียมข้อมูลบันทึก
                new_backlog = pd.DataFrame([{
                    "Time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Line": st.session_state.sel_line,
                    "Batch": st.session_state.sel_batch,
                    "ATS_caps": qty_ats,
                    "Print_caps": qty_prt,
                    "Cam_caps": qty_cam,
                    "Total_caps": qty_ats + qty_prt + qty_cam
                }])

                # บันทึกลงไฟล์ backlog.csv
                save_to_csv(new_backlog, "backlog")

                st.success(f"✅ บันทึก Backlog ของ Batch {st.session_state.sel_batch} สำเร็จ!")

                # --- แก้ไขตามสั่ง: เด้งกลับไปหน้าเลือก Batch ---
                del st.session_state.sel_batch
                st.rerun()

            if c_btn2.form_submit_button("❌ ยกเลิก/กลับ"):
                del st.session_state.sel_batch
                st.rerun()

# --- หน้า RE-PASS ฉบับบังคับเลือก Defect หากไม่ผ่าน AF ---
elif st.session_state.page == "Re_pass":
    st.title("🔄 Re-pass Management")

    df_box = load_csv("box_status").fillna("")

    # --- STEP 1: เลือก Line ---
    if 'sel_line_re' not in st.session_state and 'sel_batch_re' not in st.session_state:
        st.subheader("📍 1. เลือก Line ที่ต้องการจัดการ")

        if not df_box.empty:
            active_lines = df_box[df_box['Status'] != 'AF']['Line'].unique().tolist()
        else:
            active_lines = []

        cols = st.columns(3)
        for i, line in enumerate(active_lines):
            if cols[i % 3].button(f"Line: {line}", key=f"btn_line_{line}", use_container_width=True):
                st.session_state.sel_line_re = line
                st.rerun()

        if st.button("➕ Other (ระบุข้อมูลเอง)", use_container_width=True):
            st.session_state.sel_line_re = "Other"
            st.session_state.sel_batch_re = "Other"
            st.rerun()

        if st.button("🏠 กลับหน้าหลัก"):
            st.session_state.page = "Home"
            st.rerun()

    # --- STEP 2: เลือก Batch ---
    elif 'sel_line_re' in st.session_state and 'sel_batch_re' not in st.session_state:
        line_target = st.session_state.sel_line_re
        st.subheader(f"📍 2. เลือก Batch ใน {line_target} ที่มีงานเสีย")

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

    # --- STEP 3: หน้าฟอร์มบันทึก (เพิ่ม Logic บังคับ Defect) ---
    else:
        line_target = st.session_state.get('sel_line_re', 'Other')
        batch_target = st.session_state.sel_batch_re
        st.subheader(f"🔄 บันทึกข้อมูล Re-pass")
        st.write(f"**Line:** {line_target} | **Batch:** {batch_target}")

        with st.form("repass_form_final"):
            if batch_target == "Other":
                f_line = st.selectbox("ระบุ Line", LINES)
                f_batch = st.text_input("ระบุเลข Batch")
                f_box_num = st.text_input("ระบุเลขกล่อง")
                current_stat = "N/A"
                old_defect_val = "ระบุเอง"
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
            new_stat = st.selectbox("สถานะหลัง Re-pass", ["AF", "Sort", "Scrap", "PS"])

            # ส่วนระบุ Defect
            new_def = []
            final_reason = ""
            if new_stat != "AF":
                # ใส่เครื่องหมาย * เพื่อบอกว่าจำเป็นต้องกรอก
                new_def = st.multiselect("🔴 ระบุ Defect ใหม่ (จำเป็นต้องเลือก)", DEFECT_LIST)
                final_reason = st.text_area("ระบุเหตุผลเพิ่มเติม")

            c1, c2 = st.columns(2)
            if c1.form_submit_button("💾 บันทึกการ Re-pass"):
                # --- Logic การตรวจสอบข้อมูล (Validation) ---
                if not f_batch or not f_box_num:
                    st.error("❌ กรุณาระบุ Batch และเลขกล่องให้ครบถ้วน")

                # ตรวจสอบว่าถ้าไม่ใช่ AF ต้องมี Defect อย่างน้อย 1 อย่าง
                elif new_stat != "AF" and not new_def:
                    st.error(f"❌ งานสถานะ {new_stat} จำเป็นต้องเลือกอย่างน้อย 1 Defect")

                else:
                    # บันทึกลง re_pass.csv
                    save_to_csv(pd.DataFrame([{
                        "Time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Line": f_line,
                        "Batch": f_batch,
                        "Box": f_box_num,
                        "Previous_Status": current_stat,
                        "Result_Status": new_stat,
                        "New_Defects": ",".join(new_def),
                        "Type": mode,
                        "Reason": "Normal Re-pass" if new_stat == "AF" else final_reason
                    }]), "re_pass")

                    # อัปเดตกลับไปที่ box_status.csv
                    if batch_target != "Other":
                        df_box.loc[(df_box['Batch'] == f_batch) & (df_box['Box'] == f_box_num), 'Status'] = new_stat
                        df_box.loc[(df_box['Batch'] == f_batch) & (df_box['Box'] == f_batch), 'Defects'] = ",".join(
                            new_def)
                        df_box.to_csv("data/box_status.csv", index=False)

                    st.success(f"✅ บันทึก Re-pass สำเร็จ!")
                    if 'sel_line_re' in st.session_state: del st.session_state.sel_line_re
                    if 'sel_batch_re' in st.session_state: del st.session_state.sel_batch_re
                    st.rerun()

            if c2.form_submit_button("❌ ยกเลิก"):
                if 'sel_line_re' in st.session_state: del st.session_state.sel_line_re
                if 'sel_batch_re' in st.session_state: del st.session_state.sel_batch_re
                st.rerun()

# --- หน้า REPORT (DASHBOARD) ฉบับสมบูรณ์: เพิ่ม Backlog ใน Progress ---
elif st.session_state.page == "Report":
    st.title("📊 Production Analytics Dashboard")

    # 1. โหลดข้อมูล
    df_box = load_csv("box_status").fillna("")
    df_plan = load_csv("plan").fillna("")
    df_rej = load_csv("rejection").fillna("")
    df_cam = load_csv("camera").fillna("")
    df_repass = load_csv("re_pass").fillna("")
    df_backlog_file = load_csv("backlog").fillna(0)  # โหลดข้อมูลจากหน้า Backlog

    # จัดการ Data Type
    if not df_box.empty:
        df_box['Time'] = pd.to_datetime(df_box['Time'])
        df_box['Defects'] = df_box['Defects'].astype(str)
        df_box['Box'] = pd.to_numeric(df_box['Box'], errors='coerce').fillna(0).astype(int)

    if df_box.empty:
        st.warning("⚠️ ยังไม่มีข้อมูลสำหรับการวิเคราะห์")
        if st.button("🏠 กลับหน้าหลัก"):
            st.session_state.page = "Home"
            st.rerun()
        st.stop()

    # --- ส่วนตัวกรอง (Filters) ---
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

    # --- ส่วนหัวข้อเลือก (Tabs) ---
    t1, t2, t3, t_re, t4, t5 = st.tabs([
        "📦 Total Output", "🎯 Quality Metrics", "📷 Camera Analysis",
        "🔄 Re-pass Analysis", "📈 Progress & Backlog", "📋 Box Detail"
    ])

    # --- TAB 1: TOTAL OUTPUT (Logic Defect สะสม) ---
    with t1:
        st.subheader("ยอดการผลิตรวมและสาเหตุงานเสียหลัก")
        out_chart = df_latest.groupby(['Line', 'Status']).size().reset_index(name='Count')
        st.plotly_chart(
            px.bar(out_chart, x='Line', y='Count', color='Status', color_discrete_map=STATUS_COLORS, barmode='group',
                   text_auto=True), use_container_width=True)

        st.divider()
        st.subheader("⚠️ Top 3 Defects (สถิติจากงานที่เคยเสียทั้งหมด)")
        df_history_defects = df_filtered[df_filtered['Defects'].str.strip() != ""].copy()
        all_defs = df_history_defects['Defects'].str.split(',').explode()

        if not all_defs.empty:
            top_3 = all_defs.value_counts().reset_index()
            top_3.columns = ['Defect_Name', 'Defect_Count']
            st.plotly_chart(
                px.bar(top_3.head(3), x='Defect_Name', y='Defect_Count', color='Defect_Name', text_auto=True),
                use_container_width=True)
        else:
            st.info("ไม่พบประวัติงานเสีย")

    # --- TAB 2: QUALITY METRICS ---
    with t2:
        st.subheader("อัตราส่วน % Rejection และ % Yield")
        metrics_data = []
        for line in f_line:
            line_boxes = df_latest[df_latest['Line'] == line]
            if not line_boxes.empty:
                theoretical_w = len(line_boxes) * 12.5
                line_rej = df_rej[df_rej['Line'] == line] if 'Line' in df_rej.columns else pd.DataFrame()
                total_rej_kg = line_rej['ATS_kg'].sum() + line_rej['Print_kg'].sum() + line_rej[
                    'Cam_kg'].sum() if not line_rej.empty else 0
                if theoretical_w > 0:
                    rej_p = (total_rej_kg / theoretical_w) * 100
                    metrics_data.append({"Line": line, "Yield %": max(0, 100 - rej_p), "Rejection %": min(100, rej_p)})
        if metrics_data:
            st.plotly_chart(px.bar(pd.DataFrame(metrics_data), x='Line', y=['Yield %', 'Rejection %'], barmode='stack',
                                   color_discrete_sequence=['#2ecc71', '#e74c3c'], text_auto='.2f'),
                            use_container_width=True)

    # --- TAB 3: CAMERA ANALYSIS ---
    with t3:
        st.subheader("📷 Camera Performance Comparison")
        if not df_cam.empty:
            cam_table = df_cam[df_cam['Line'].isin(f_line)].copy()
            if not cam_table.empty:
                st.dataframe(
                    cam_table[['Line', 'Rate_Cam1', 'Rate_Cam2']].style.format(
                        {"Rate_Cam1": "{:.2f}%", "Rate_Cam2": "{:.2f}%"}).background_gradient(cmap="RdYlGn",
                                                                                              subset=['Rate_Cam1',
                                                                                                      'Rate_Cam2']),
                    use_container_width=True, hide_index=True
                )
                st.divider()
                st.subheader("🔍 Camera Detect Defects (By Line)")
                selected_cam_line = st.selectbox("เลือก Line เพื่อดูรายละเอียด Defect", f_line, key="cam_line_sel")
                line_cam_data = cam_table[cam_table['Line'] == selected_cam_line]
                if not line_cam_data.empty and line_cam_data['Top_Defects'].iloc[0] != "":
                    c_line_defs = line_cam_data['Top_Defects'].str.split(',').explode().value_counts().reset_index()
                    c_line_defs.columns = ['Defect', 'Count']
                    st.plotly_chart(
                        px.bar(c_line_defs, x='Count', y='Defect', orientation='h', text_auto=True, color='Defect'),
                        use_container_width=True)

    # --- TAB 4: RE-PASS ANALYSIS ---
    with t_re:
        st.subheader("🔄 Re-pass Performance")
        if not df_repass.empty:
            df_rp_f = df_repass[df_repass['Line'].isin(f_line)]
            if not df_rp_f.empty:
                c_rp1, c_rp2 = st.columns(2)
                with c_rp1:
                    rp_res = df_rp_f['Result_Status'].value_counts().reset_index()
                    rp_res.columns = ['Status', 'Count']
                    st.plotly_chart(px.pie(rp_res, values='Count', names='Status', color='Status',
                                           color_discrete_map={'AF': '#2ecc71', 'Sort': '#f1c40f', 'Scrap': '#e74c3c'}),
                                    use_container_width=True)
                with c_rp2:
                    rp_line = df_rp_f['Line'].value_counts().reset_index().head(5)
                    rp_line.columns = ['Line', 'Count']
                    st.plotly_chart(px.bar(rp_line, x='Line', y='Count', text_auto=True), use_container_width=True)

    # --- TAB 5: PROGRESS & BACKLOG (ไฮไลท์ที่ขอเพิ่ม) ---
    with t4:
        st.subheader("📈 Production Progress & Backlog Analysis")
        if not df_plan.empty:
            # 1. ยอด Actual AF จากการผลิตจริง
            actual_af = df_latest[df_latest['Status'] == 'AF'].groupby('Batch').size().reset_index(name='Actual_AF')

            # 2. ยอด Backlog จากการคีย์ข้อมูลหน้า Backlog (ดึงข้อมูลล่าสุดของแต่ละ Batch)
            if not df_backlog_file.empty:
                latest_backlog = df_backlog_file.sort_values('Time').drop_duplicates(subset=['Batch'], keep='last')
            else:
                latest_backlog = pd.DataFrame(columns=['Batch', 'ATS_caps', 'Print_caps', 'Cam_caps'])

            # รวมข้อมูล Plan + Actual + Backlog
            df_p = pd.merge(df_plan[['batch_number', 'need_af_box']], actual_af, left_on='batch_number',
                            right_on='Batch', how='left').fillna(0)
            df_p = pd.merge(df_p, latest_backlog[['Batch', 'ATS_caps', 'Print_caps', 'Cam_caps']],
                            left_on='batch_number', right_on='Batch', how='left').fillna(0)

            df_p['Progress %'] = (df_p['Actual_AF'] / df_p['need_af_box']) * 100

            # จัดชื่อคอลัมน์ให้อ่านง่าย
            df_p_display = df_p[
                ['batch_number', 'need_af_box', 'Actual_AF', 'ATS_caps', 'Print_caps', 'Cam_caps', 'Progress %']].copy()
            df_p_display.columns = ['Batch', 'Plan (Boxes)', 'Actual AF', 'Backlog ATS', 'Backlog Print', 'Backlog Cam',
                                    'Progress %']

            st.write("**ตารางเปรียบเทียบงานเสร็จและงานค้างสะสม**")
            st.dataframe(
                df_p_display.style.format({"Progress %": "{:.2f}%"})
                .background_gradient(cmap="Greens", subset=['Actual AF'])
                .background_gradient(cmap="Reds", subset=['Backlog ATS', 'Backlog Print', 'Backlog Cam']),
                use_container_width=True, hide_index=True
            )

            st.plotly_chart(
                px.bar(df_p, x='batch_number', y='Progress %', range_y=[0, 110], text_auto='.1f', color='Progress %',
                       color_continuous_scale='RdYlGn'), use_container_width=True)
        else:
            st.info("กรุณาระบุข้อมูลในหน้า Plan ก่อน")

    # --- TAB 6: BOX DETAIL ---
    with t5:
        st.subheader("📋 รายละเอียดสถานะกล่อง (เรียงตามเลขกล่อง)")
        col_s1, col_s2 = st.columns([1, 3])
        with col_s1:
            sum_tab = df_latest['Status'].value_counts().reset_index()
            sum_tab.columns = ['Status', 'Total']
            st.table(sum_tab)
        with col_s2:
            # เรียงลำดับจากน้อยไปมากเสมอ
            df_sorted = df_filtered.sort_values(by=['Batch', 'Box'], ascending=[True, True])
            st.dataframe(df_sorted[['Time', 'Line', 'Batch', 'Box', 'Status', 'Defects']], use_container_width=True,
                         hide_index=True)

    # --- ย้ายปุ่มกลับหน้าหลักกลับมาไว้ที่เดิม (ด้านล่างสุด) ---
    st.divider()
    if st.button("🏠 กลับหน้าหลัก", use_container_width=True):
        st.session_state.page = "Home"
        st.rerun()

# --- หน้าจัดการบัญชี (ACCOUNT) - ปรับปรุงใหม่แบบมีตารางและการยืนยัน ---
elif st.session_state.page == "Account":
    st.title("👥 จัดการบัญชีผู้ใช้")
    acc_df = load_csv("accounts")

    tab_add, tab_manage = st.tabs(["➕ เพิ่มผู้ใช้ใหม่", "⚙️ จัดการ/แก้ไขข้อมูล"])

    # --- ส่วนที่ 1: เพิ่มผู้ใช้ใหม่ ---
    with tab_add:
        with st.form("add_acc_form", clear_on_submit=True):
            st.subheader("ระบุรายละเอียดผู้ใช้งานใหม่")
            c1, c2 = st.columns(2)
            fn = c1.text_input("ชื่อ-นามสกุล")
            eid = c2.text_input("รหัสพนักงาน")
            un = c1.text_input("Username")
            pw = c2.text_input("Password (ชั่วคราว)")
            rl = st.selectbox("ตำแหน่ง/สิทธิ์การใช้งาน", ["employee", "supervisor", "admin"])

            if st.form_submit_button("💾 บันทึกและสร้างบัญชี", use_container_width=True):
                if fn and eid and un and pw:
                    # ตรวจสอบ Username ซ้ำ
                    if un in acc_df['username'].values:
                        st.error("❌ Username นี้มีในระบบแล้ว")
                    else:
                        # เซ็ต first_login เป็น True เพื่อบังคับเปลี่ยนรหัสผ่าน
                        new_acc = pd.DataFrame([{
                            "fullname": fn, "emp_id": eid, "username": un,
                            "password": pw, "role": rl, "first_login": True
                        }])
                        save_to_csv(new_acc, "accounts")
                        st.success(f"✅ เพิ่มผู้ใช้ {fn} เรียบร้อยแล้ว")
                        st.rerun()
                else:
                    st.error("❌ กรุณากรอกข้อมูลให้ครบถ้วน")

    # --- ส่วนที่ 2: ตารางจัดการและแก้ไข ---
    with tab_manage:
        if not acc_df.empty:
            st.subheader("📋 รายชื่อผู้ใช้งานทั้งหมด")
            # แสดงตารางเพื่อให้แอดมินดูภาพรวม
            st.dataframe(acc_df[['fullname', 'emp_id', 'username', 'role']], use_container_width=True, hide_index=True)

            st.divider()

            # --- กล่องเครื่องมือจัดการ (Centered Layout) ---
            st.subheader("🛠️ แก้ไขข้อมูลหรือลบสมาชิก")

            # เลือก User ที่ต้องการจัดการ
            target_user = st.selectbox("เลือกบัญชีที่ต้องการจัดการ", acc_df['username'].tolist(),
                                       key="user_select_manage")
            user_row = acc_df[acc_df['username'] == target_user].iloc[0]

            # เลือกตำแหน่งใหม่ (วางเดี่ยวๆ ด้านบน)
            new_role = st.selectbox("เปลี่ยนตำแหน่งเป็น", ["employee", "supervisor", "admin"],
                                    index=["employee", "supervisor", "admin"].index(user_row['role']))

            # --- ส่วนปุ่มคำสั่ง (จัดวางตามรอยขีดสีดำของคุณ: เรียงกันด้านล่าง) ---
            # ใช้ columns เพื่อจัดปุ่มให้อยู่ตรงกลาง (Centered Buttons)
            # col1, col4 เป็นพื้นที่ว่างเพื่อดัน col2, col3 ให้อยู่กลาง
            col1, col2, col3, col4 = st.columns([1.5, 1, 1, 1.5])

            # 1. ปุ่มอัปเดตตำแหน่ง (ใน col2)
            if col2.button("🔄 อัปเดตตำแหน่ง", use_container_width=True):
                acc_df.loc[acc_df['username'] == target_user, 'role'] = new_role
                acc_df.to_csv("data/accounts.csv", index=False)
                st.success(f"อัปเดตสิทธิ์ {target_user} เรียบร้อย!")
                st.rerun()

            # 2. ปุ่มลบผู้ใช้ (ใน col3)
            if col3.button("🗑️ ลบผู้ใช้", use_container_width=True, type="primary"):
                st.session_state.confirm_delete = target_user

            # --- หน้าต่างยืนยันการลบ (เล็กๆ แสดงใต้ปุ่ม) ---
            if 'confirm_delete' in st.session_state and st.session_state.confirm_delete == target_user:
                st.write("")  # เว้นระยะช่องว่าง
                # วางกล่องยืนยันไว้ใน columns กลางเพื่อให้ขนาดไม่กว้างเกินไป
                _, conf_col, _ = st.columns([1, 2, 1])
                with conf_col:
                    with st.container(border=True):
                        st.warning(f"⚠️ ยืนยันการลบคุณ **{user_row['fullname']}**?")
                        st.write("การกระทำนี้ไม่สามารถย้อนกลับได้")
                        c1, c2 = st.columns(2)
                        if c1.button("✅ ใช่, ยืนยัน", use_container_width=True, type="primary"):
                            acc_df = acc_df[acc_df['username'] != target_user]
                            acc_df.to_csv("data/accounts.csv", index=False)
                            del st.session_state.confirm_delete
                            st.success("ลบข้อมูลเรียบร้อยแล้ว")
                            st.rerun()
                        if c2.button("🚫 ยกเลิก", use_container_width=True):
                            del st.session_state.confirm_delete
                            st.rerun()
        else:
            st.info("ยังไม่มีข้อมูลผู้ใช้ในระบบ")

    if st.button("🏠 กลับหน้าหลัก"):
        st.session_state.page = "Home"
        st.rerun()
