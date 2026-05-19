import streamlit as st
import pandas as pd
from datetime import datetime
from constants import LINES, DEFECT_LIST


def show_camera_page(load_csv, save_to_csv):
    st.markdown("<div class='main-header'>📷 Camera Analysis</div>", unsafe_allow_html=True)

    # ==========================================
    # STEP 1: เลือก Line
    # ==========================================
    if 'sel_line' not in st.session_state:
        st.subheader("📍 เลือก Line ที่ต้องการตรวจสอบ")
        cols = st.columns(4)
        for i, l in enumerate(LINES):
            if cols[i % 4].button(l, key=f"cam_line_{l}", use_container_width=True):
                st.session_state.sel_line = l
                st.rerun()

    # ==========================================
    # STEP 2: เลือก Batch
    # ==========================================
    elif 'sel_batch' not in st.session_state:
        st.subheader(f"📍 Line: {st.session_state.sel_line} ➡️ เลือก Batch ที่กำลังผลิต")
        p_df = load_csv("plan")
        active_b = []

        if not p_df.empty:
            # ✅ case-insensitive detect
            line_col   = next((c for c in p_df.columns if c.strip().lower() == 'line'),         None)
            status_col = next((c for c in p_df.columns if c.strip().lower() == 'batch status'), None)
            batch_col  = next((c for c in p_df.columns if c.strip().lower() == 'batch'),        None)

            if line_col and status_col and batch_col:
                active_b = p_df[
                    (p_df[line_col].astype(str).str.strip()   == str(st.session_state.sel_line)) &
                    (p_df[status_col].astype(str).str.strip().str.lower() != "finished")
                ][batch_col].unique().tolist()
            else:
                missing = [n for n, c in [("line", line_col), ("batch status", status_col), ("batch", batch_col)] if not c]
                st.error(f"⚠️ ไม่พบคอลัมน์: {missing} ใน plan sheet")
                st.caption(f"คอลัมน์ที่มีอยู่: {p_df.columns.tolist()}")

        if active_b:
            cols = st.columns(3)
            for i, b in enumerate(active_b):
                if cols[i % 3].button(f"Batch: {b}", key=f"cam_batch_{b}", use_container_width=True):
                    st.session_state.sel_batch = b
                    st.rerun()
        else:
            st.warning("⚠️ ไม่พบ Batch ที่กำลังเปิดทำงานอยู่ (Running) ใน Line นี้")

        st.write("---")
        if st.button("🔙 เปลี่ยน Line", use_container_width=True):
            del st.session_state.sel_line
            st.rerun()

    # ==========================================
    # STEP 3: บันทึกข้อมูลกล้อง
    # ==========================================
    else:
        line_target  = st.session_state.sel_line
        batch_target = st.session_state.sel_batch

        st.subheader("✅ รายงานสถานะกล้องตรวจจับงาน")
        st.info(f"📹 **Line:** {line_target}  |  🆔 **Batch:** {batch_target}")

        with st.form("camera_full_form"):
            cam_col1, cam_col2 = st.columns(2)

            with cam_col1:
                st.markdown("<h4 style='color:#1E3A8A; border-bottom:2px solid #1E3A8A; padding-bottom:5px;'>📸 Camera 1</h4>",
                            unsafe_allow_html=True)
                c1_pass_rate = st.number_input("Passing Rate (%) - กล้อง 1",
                                               min_value=0.0, max_value=100.0, value=100.0, step=0.1, key="c1_pr")
                st.write("📌 **ข้อมูลของเสีย (Defects)**")
                c1_def_list, c1_qty_list = [], []
                for row in range(4):
                    sub_c1, sub_c2 = st.columns([1.5, 1])
                    d_type = sub_c1.selectbox(f"Defect {row+1}", ["-"] + DEFECT_LIST, key=f"c1_def_type_{row}")
                    d_qty  = sub_c2.number_input("จำนวน (ชิ้น)", min_value=0, step=1, key=f"c1_def_qty_{row}")
                    if d_type != "-":
                        c1_def_list.append(f"{d_type}({d_qty})")
                        c1_qty_list.append(d_qty)

            with cam_col2:
                st.markdown("<h4 style='color:#1E3A8A; border-bottom:2px solid #1E3A8A; padding-bottom:5px;'>📸 Camera 2</h4>",
                            unsafe_allow_html=True)
                c2_pass_rate = st.number_input("Passing Rate (%) - กล้อง 2",
                                               min_value=0.0, max_value=100.0, value=100.0, step=0.1, key="c2_pr")
                st.write("📌 **ข้อมูลของเสีย (Defects)**")
                c2_def_list, c2_qty_list = [], []
                for row in range(4):
                    sub_c3, sub_c4 = st.columns([1.5, 1])
                    d_type = sub_c3.selectbox(f"Defect {row+1}", ["-"] + DEFECT_LIST, key=f"c2_def_type_{row}")
                    d_qty  = sub_c4.number_input("จำนวน (ชิ้น)", min_value=0, step=1, key=f"c2_def_qty_{row}")
                    if d_type != "-":
                        c2_def_list.append(f"{d_type}({d_qty})")
                        c2_qty_list.append(d_qty)

            st.write("---")
            btn_col1, btn_col2 = st.columns(2)

            with btn_col1:
                if st.form_submit_button("💾 บันทึกข้อมูลลง Cloud", use_container_width=True, type="primary"):
                    camera_record = pd.DataFrame([{
                        "Time":           datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Line":           line_target,
                        "Batch":          batch_target,
                        "Cam1_Pass_Rate": c1_pass_rate,
                        "Cam1_Defects":   ",".join(c1_def_list) if c1_def_list else "None",
                        "Cam1_Total_Qty": sum(c1_qty_list),
                        "Cam2_Pass_Rate": c2_pass_rate,
                        "Cam2_Defects":   ",".join(c2_def_list) if c2_def_list else "None",
                        "Cam2_Total_Qty": sum(c2_qty_list),
                    }])
                    save_to_csv("camera", camera_record)
                    st.cache_data.clear()
                    st.success("🎉 บันทึกข้อมูลการวิเคราะห์จากกล้องเรียบร้อยแล้ว!")
                    for key in ['sel_line', 'sel_batch']:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()

            with btn_col2:
                if st.form_submit_button("❌ ยกเลิก/ย้อนกลับ", use_container_width=True):
                    for key in ['sel_line', 'sel_batch']:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()
