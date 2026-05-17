import streamlit as st
import pandas as pd
from datetime import datetime
from constants import LINES, DEFECT_LIST, BOX_STATUS


def show_box_status_page(load_csv, save_to_csv):
    st.markdown("<div class='main-header'>📦 Box Status Recording</div>", unsafe_allow_html=True)

    # 1. ขั้นตอนการเลือก Line (คงเดิม)
    if 'sel_line' not in st.session_state:
        st.subheader("📍 เลือก Line")
        cols = st.columns(4)
        for i, l in enumerate(LINES):
            if cols[i % 4].button(l, key=f"btn_l_{l}", use_container_width=True):
                st.session_state.sel_line = l
                st.rerun()

    # 2. ขั้นตอนการเลือก Batch (คงเดิม)
    elif 'sel_batch' not in st.session_state:
        st.subheader(f"📍 Line: {st.session_state.sel_line} > เลือก Batch")
        p_df = load_csv("plan")
        active_b = p_df[(p_df['line'] == st.session_state.sel_line) &
                        (p_df['batch_status'] != "Finished")]['batch_number'].tolist() if not p_df.empty else []

        if active_b:
            cols = st.columns(3)
            for i, b in enumerate(active_b):
                if cols[i % 3].button(f"Batch: {b}", key=f"batch_{b}", use_container_width=True):
                    st.session_state.sel_batch = b
                    st.rerun()
        else:
            st.warning("ไม่มี Batch ที่กำลัง Running ใน Line นี้")

        if st.button("🔙 เปลี่ยน Line", use_container_width=False):
            del st.session_state.sel_line
            st.rerun()

    # 3. ขั้นตอนการบันทึกข้อมูลกล่อง
    else:
        st.subheader(f"✅ {st.session_state.sel_line} | Batch: {st.session_state.sel_batch}")

        # --- จุดสำคัญ: ล้าง Cache ก่อนดึงข้อมูลมาเช็คซ้ำ เพื่อให้ได้ค่าล่าสุดจริงๆ ---
        st.cache_data.clear()
        current_data = load_csv("box_status")

        box_no = st.text_input("Box Number (เลขกล่อง)", key="input_box_no")
        selected_stat = st.selectbox("สถานะ", BOX_STATUS, key="input_stat")

        show_defect = selected_stat not in ["เลือก Status", "AF"]

        with st.form("box_form_action"):
            selected_defs = []
            if show_defect:
                selected_defs = st.multiselect("⚠️ เลือก Defects (บังคับระบุ)", DEFECT_LIST)

            c1, c2 = st.columns(2)

            if c1.form_submit_button("💾 บันทึกข้อมูล", use_container_width=True, type="primary"):
                clean_box = str(box_no).strip()
                clean_batch = str(st.session_state.sel_batch).strip()

                # --- ตรรกะการเช็คซ้ำที่เข้มงวดขึ้น ---
                is_duplicate = False
                if not current_data.empty:
                    temp_df = current_data.copy()
                    temp_df.columns = [str(c).strip().lower() for c in temp_df.columns]

                    if 'batch' in temp_df.columns and 'box' in temp_df.columns:
                        # เช็คทั้ง Batch และ Box พร้อมกัน
                        mask = (temp_df['batch'].astype(str).str.strip() == clean_batch) & \
                               (temp_df['box'].astype(str).str.strip() == clean_box)
                        if mask.any():
                            is_duplicate = True

                # --- ส่วนแจ้งเตือนและการบันทึก ---
                if not clean_box or selected_stat == "เลือก Status":
                    st.error("❌ กรุณากรอกเลขกล่องและเลือกสถานะ")

                elif show_defect and not selected_defs:
                    st.error(f"❌ สถานะ {selected_stat} ต้องระบุสาเหตุ (Defects)")

                elif is_duplicate:
                    # แจ้งเตือนว่าซ้ำด้วย warning เพื่อให้เด่นชัด
                    st.warning(f"⚠️ เลขกล่องซ้ำ! กล่องที่ {clean_box} ของ Batch {clean_batch} มีในระบบแล้ว")
                    st.info("กรุณาตรวจสอบเลขกล่องอีกครั้ง หรือเปลี่ยนเลขกล่องก่อนบันทึก")

                else:
                    new_entry = pd.DataFrame([{
                        "Time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Line": st.session_state.sel_line,
                        "Batch": st.session_state.sel_batch,
                        "Box": clean_box,
                        "Status": selected_stat,
                        "Defects": ",".join(selected_defs) if selected_defs else ""
                    }])

                    save_to_csv("box_status", new_entry)
                    st.success(f"✅ บันทึกกล่อง {clean_box} สำเร็จ!")

                    # กลับไปหน้าเลือก Batch (ตามโครงสร้างเดิม)
                    del st.session_state.sel_batch
                    st.rerun()

            if c2.form_submit_button("🔙 กลับ/ยกเลิก", use_container_width=True):
                del st.session_state.sel_batch
                st.rerun()
