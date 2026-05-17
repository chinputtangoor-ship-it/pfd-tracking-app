import streamlit as st
import pandas as pd
from datetime import datetime


def show_repass_page(load_csv, save_to_csv, conn):
    st.markdown("<div class='main-header'>🔄 Re-pass Management</div>", unsafe_allow_html=True)
    df_box = load_csv("box_status").fillna("")
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
        if st.button("🏠 กลับหน้าหลัก", use_container_width=True):
            st.session_state.page = "Home"
            st.rerun()

    # ==========================================
    elif 'sel_line_re' in st.session_state and 'sel_batch_re' not in st.session_state:
        line_target = st.session_state.sel_line_re
        st.subheader(f"📍 2. เลือก Batch ใน {line_target} ที่มีงานเสีย")
        active_rej_batches = []
        if not df_box.empty:
            active_rej_batches = df_box[(df_box['Line'] == line_target) & (df_box['Status'] != 'AF')][
                'Batch'].unique().tolist()

        if not active_rej_batches:
            st.warning(f"❌ ไม่พบงานเสียคงค้างใน Line: {line_target}")
            if st.button("⬅️ กลับไปเลือก Line", use_container_width=True):
                del st.session_state.sel_line_re
                st.rerun()
        else:
            cols = st.columns(3)
            for i, batch in enumerate(active_rej_batches):
                if cols[i % 3].button(f"Batch: {batch}", key=f"btn_batch_{batch}", use_container_width=True):
                    st.session_state.sel_batch_re = batch
                    st.rerun()

            st.write("---")
            if st.button("⬅️ กลับไปเลือก Line", use_container_width=True):
                del st.session_state.sel_line_re
                st.rerun()

    # ==========================================
    else:
        line_target = st.session_state.get('sel_line_re', 'Other')
        batch_target = st.session_state.sel_batch_re
        st.subheader(f"🔄 บันทึกข้อมูล Re-pass ลง Cloud")
        st.info(f"✅ **Line:** {line_target}  |  🆔 **Batch:** {batch_target}")

        from constants import DEFECT_LIST, LINES, BOX_STATUS

        if batch_target == "Other":
            f_line = st.selectbox("ระบุ Line", LINES)
            f_batch = st.text_input("ระบุเลข Batch")
            f_box_num = st.text_input("ระบุเลขกล่อง")
            current_stat, old_defect_val = "N/A", "ระบุเอง"
        else:
            f_line = line_target
            f_batch = batch_target
            boxes_to_fix = df_box[(df_box['Batch'].astype(str) == str(batch_target)) & (df_box['Status'] != 'AF')]
            box_list = boxes_to_fix['Box'].unique().tolist()
            f_box_num = st.selectbox("เลือกเลขกล่อง", box_list)

            if f_box_num:
                match = boxes_to_fix[boxes_to_fix['Box'].astype(str) == str(f_box_num)].iloc[-1]
                current_stat = match['Status']
                old_defect_val = match['Defects'] if match['Defects'] != "" else "ไม่มี Defect"
            else:
                current_stat, old_defect_val = "N/A", "N/A"

        st.warning(f"📌 สถานะเดิมในระบบ: {current_stat} | Defect เดิม: {old_defect_val}")

        mode = st.radio("ประเภทงาน Re-pass", ["Online", "Offline"], horizontal=True)

        # 🎯 [แก้ไขดรอปดาวน์]: ซิงค์ดึงตัวเลือกสถานะกล่องทั้งหมดโดยตรงจาก BOX_STATUS ใน constants.py
        new_stat = st.selectbox("สถานะหลังทำการ Re-pass", BOX_STATUS, key="repass_stat_select")

        show_def_input = new_stat != "AF"
        with st.form("repass_final_action"):
            new_def = []
            final_reason = ""

            if show_def_input:
                st.markdown("<b style='color:red;'>⚠️ จำเป็นต้องระบุข้อมูลรายละเอียด Defect ด้านล่างนี้</b>",
                            unsafe_allow_html=True)
                new_def = st.multiselect("🔴 ระบุ Defect (เลือกได้มากกว่า 1 รายการ)", DEFECT_LIST)
                final_reason = st.text_area("ระบุเหตุผลหรือหมายเหตุเพิ่มเติม")

            st.write("---")
            c1, c2 = st.columns(2)

            if c1.form_submit_button("💾 บันทึกการ Re-pass ลง Cloud", use_container_width=True, type="primary"):
                if not f_batch or not f_box_num:
                    st.error("❌ ไม่สามารถบันทึกได้: กรุณาระบุข้อมูล Batch และเลขกล่องให้ครบถ้วน")
                elif show_def_input and not new_def:
                    st.error(f"❌ ไม่สามารถบันทึกได้: สถานะ [{new_stat}] จำเป็นต้องระบุ Defect อย่างน้อย 1 รายการ")
                else:
                    # 1. จัดการเตรียมข้อมูลเพื่อบันทึกประวัติลงฐานข้อมูลประวัติ Re-pass
                    new_rp_record = pd.DataFrame([{
                        "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Line": f_line,
                        "Batch": f_batch,
                        "Box": f_box_num,
                        "Previous_Status": current_stat,
                        "Result_Status": new_stat,
                        "New_Defects": ",".join(new_def) if show_def_input else "",  # เคลียร์ว่างถ้าเป็น AF
                        "Type": mode,
                        "Reason": "Normal Re-pass" if new_stat == "AF" else final_reason
                    }])

                    # บันทึกข้อมูลลงฐานข้อมูลประวัติ Re-pass
                    save_to_csv("re_pass", new_rp_record)

                    if batch_target != "Other":
                        new_def_str = ",".join(new_def) if show_def_input else ""
                        df_box.loc[(df_box['Batch'].astype(str) == str(f_batch)) &
                                   (df_box['Box'].astype(str) == str(f_box_num)), ['Status', 'Defects']] = [new_stat,
                                                                                                            new_def_str]
                        conn.update(worksheet="box_status", data=df_box)

                    st.cache_data.clear()
                    st.success("🎉 บันทึกข้อมูลและปรับเปลี่ยนสถานะเรียบร้อยแล้ว!")
                    for key in ['sel_line_re', 'sel_batch_re']:
                        if key in st.session_state: del st.session_state[key]
                    st.rerun()

            if c2.form_submit_button("❌ ยกเลิกและกลับ", use_container_width=True):
                for key in ['sel_line_re', 'sel_batch_re']:
                    if key in st.session_state: del st.session_state[key]
                st.rerun()

