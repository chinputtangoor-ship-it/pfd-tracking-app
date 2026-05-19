import streamlit as st
import pandas as pd
from datetime import datetime
from constants import DEFECT_LIST, BOX_STATUS


def show_box_status_page(load_csv, save_to_csv):
    st.markdown("<div class='main-header'>📦 Box Status Recording</div>", unsafe_allow_html=True)

    # ==========================================
    # STEP 1: เลือก Line
    # ==========================================
    if 'sel_line' not in st.session_state:
        st.subheader("📍 เลือก Line")
        cols = st.columns(4)
        matrix = [
            ["H501", "H502", "H503", "H504"],
            ["H505", "H506", "H507", "H508"],
            ["H509", "H510", "H511", "H512"],
            ["H513", "",     "",     ""    ]
        ]
        for row in matrix:
            for col_idx, line_name in enumerate(row):
                if line_name != "":
                    if cols[col_idx].button(line_name, key=f"btn_l_{line_name}", use_container_width=True):
                        st.session_state.sel_line = line_name
                        st.rerun()

    # ==========================================
    # STEP 2: เลือก Batch
    # ==========================================
    elif 'sel_batch' not in st.session_state:
        st.subheader(f"📍 Line: {st.session_state.sel_line} > เลือก Batch")
        p_df = load_csv("plan")

        active_b = []
        if not p_df.empty:
            line_col   = next((c for c in p_df.columns if c.strip().lower() == 'line'),         None)
            status_col = next((c for c in p_df.columns if c.strip().lower() == 'batch status'), None)
            batch_col  = next((c for c in p_df.columns if c.strip().lower() == 'batch'),        None)

            if line_col and status_col and batch_col:
                active_b = p_df[
                    (p_df[line_col].astype(str).str.strip()   == st.session_state.sel_line) &
                    (p_df[status_col].astype(str).str.strip().str.lower() != "finished")
                ][batch_col].tolist()
            else:
                missing = [n for n, c in [("line", line_col), ("batch status", status_col), ("batch", batch_col)] if not c]
                st.error(f"⚠️ ไม่พบคอลัมน์: {', '.join(missing)} ใน plan sheet")
                st.caption(f"คอลัมน์ที่มีอยู่: {p_df.columns.tolist()}")

        if active_b:
            cols = st.columns(3)
            for i, b in enumerate(active_b):
                if cols[i % 3].button(f"Batch: {b}", key=f"batch_{b}", use_container_width=True):
                    st.session_state.sel_batch = b
                    st.rerun()
        else:
            st.warning("ไม่มี Batch ที่กำลัง Running ใน Line นี้")

        if st.button("🔙 เปลี่ยน Line", use_container_width=True):
            del st.session_state.sel_line
            st.rerun()

    # ==========================================
    # STEP 3: บันทึก Box Status
    # ==========================================
    else:
        st.subheader(f"✅ {st.session_state.sel_line} | Batch: {st.session_state.sel_batch}")
        current_data = load_csv("box_status")

        clean_batch = str(st.session_state.sel_batch).strip()

        # ✅ คำนวณเลขกล่องถัดไปอัตโนมัติ
        next_box_no = 1
        if not current_data.empty:
            temp_df = current_data.copy()
            temp_df.columns = [str(c).strip().lower() for c in temp_df.columns]
            batch_c = next((c for c in temp_df.columns if c == 'batch'), None)
            box_c   = next((c for c in temp_df.columns if c == 'box'),   None)

            if batch_c and box_c:
                batch_boxes = temp_df[temp_df[batch_c].astype(str).str.strip() == clean_batch][box_c]
                existing_nos = pd.to_numeric(batch_boxes, errors='coerce').dropna()
                if not existing_nos.empty:
                    next_box_no = int(existing_nos.max()) + 1

        st.info(f"📦 เลขกล่องถัดไปที่จะบันทึก: **{next_box_no}**")

        selected_stat = st.selectbox("สถานะ", BOX_STATUS, key="input_stat")
        show_defect   = selected_stat not in ["เลือก Status", "AF"]

        with st.form("box_form_action"):
            selected_defs = []
            if show_defect:
                selected_defs = st.multiselect("⚠️ เลือก Defects (บังคับระบุ)", DEFECT_LIST)

            c1, c2 = st.columns(2)

            if c1.form_submit_button("💾 บันทึกข้อมูล", use_container_width=True, type="primary"):

                if selected_stat == "เลือก Status":
                    st.error("❌ กรุณาเลือกสถานะ")

                elif show_defect and not selected_defs:
                    st.error(f"❌ Status '{selected_stat}' จำเป็นต้องระบุสาเหตุเสีย (Defects)")

                else:
                    new_entry = pd.DataFrame([{
                        "Time":    datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Line":    st.session_state.sel_line,
                        "Batch":   st.session_state.sel_batch,
                        "Box":     next_box_no,
                        "Status":  selected_stat,
                        "Defects": ",".join(selected_defs) if selected_defs else ""
                    }])
                    save_to_csv("box_status", new_entry)
                    st.cache_data.clear()
                    st.success(f"✅ บันทึกกล่อง {next_box_no} | Batch: {clean_batch} สำเร็จ!")
                    st.rerun()  # rerun เพื่ออัปเดตเลขกล่องถัดไป (ไม่ del sel_batch)

            if c2.form_submit_button("🔙 กลับ/ยกเลิก", use_container_width=True):
                del st.session_state.sel_batch
                st.rerun()
