import streamlit as st
import pandas as pd
from datetime import datetime


def show_backlog_page(load_csv, save_to_csv):
    st.markdown("<div class='main-header'>⏳ Backlog Management</div>", unsafe_allow_html=True)

    if 'sel_line' not in st.session_state:
        st.subheader("📍 1. เลือก Line เพื่อลงข้อมูล Backlog")
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
                    if cols[col_idx].button(line_name, key=f"back_l_{line_name}", use_container_width=True):
                        st.session_state.sel_line = line_name
                        st.rerun()

    # ==========================================
    elif 'sel_batch' not in st.session_state:
        st.subheader(f"📍 Line: {st.session_state.sel_line} > 2. เลือก Batch")
        p_df = load_csv("plan")
        active_b = []

        if not p_df.empty:
            # ✅ case-insensitive detect
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
                st.error(f"⚠️ ไม่พบคอลัมน์: {missing} ใน plan sheet")
                st.caption(f"คอลัมน์ที่มีอยู่: {p_df.columns.tolist()}")

        if active_b:
            cols = st.columns(3)
            for i, b in enumerate(active_b):
                if cols[i % 3].button(f"Batch: {b}", key=f"back_b_{b}", use_container_width=True):
                    st.session_state.sel_batch = b
                    st.rerun()
        else:
            st.warning("⚠️ ไม่พบ Batch ที่กำลังดำเนินการ (Running) ใน Line นี้")

        st.write("---")
        if st.button("🔙 เปลี่ยน Line", key="change_line_back", use_container_width=True):
            del st.session_state.sel_line
            st.rerun()

    # ==========================================
    else:
        st.subheader("📝 จัดการข้อมูล Backlog")
        st.info(f"✅ **Line:** {st.session_state.sel_line}  |  🆔 **Batch:** {st.session_state.sel_batch}")
        b_df = load_csv("backlog")

        old_ats, old_print, old_cam = 0, 0, 0

        if not b_df.empty:
            # ✅ case-insensitive detect backlog columns
            line_col_b  = next((c for c in b_df.columns if c.strip().lower() == 'line'),       None)
            batch_col_b = next((c for c in b_df.columns if c.strip().lower() == 'batch'),      None)
            ats_col     = next((c for c in b_df.columns if c.strip().lower() == 'ats_caps'),   None)
            print_col   = next((c for c in b_df.columns if c.strip().lower() == 'print_caps'), None)
            cam_col     = next((c for c in b_df.columns if c.strip().lower() == 'cam_caps'),   None)

            if line_col_b and batch_col_b:
                match_rows = b_df[
                    (b_df[line_col_b].astype(str).str.strip()  == st.session_state.sel_line) &
                    (b_df[batch_col_b].astype(str).str.strip() == str(st.session_state.sel_batch))
                ]
                if not match_rows.empty:
                    last_record = match_rows.iloc[-1]
                    old_ats   = int(pd.to_numeric(last_record.get(ats_col,   0), errors='coerce') or 0) if ats_col   else 0
                    old_print = int(pd.to_numeric(last_record.get(print_col, 0), errors='coerce') or 0) if print_col else 0
                    old_cam   = int(pd.to_numeric(last_record.get(cam_col,   0), errors='coerce') or 0) if cam_col   else 0

        with st.form("backlog_form_v3"):
            st.markdown("### 📊 1. ยอดค้างสะสมในระบบปัจจุบัน (Current Backlog)")
            m1, m2, m3 = st.columns(3)
            m1.metric(label="📌 ATS คงค้างเดิม",      value=f"{old_ats:,} caps")
            m2.metric(label="📌 Printing คงค้างเดิม", value=f"{old_print:,} caps")
            m3.metric(label="📌 Camera คงค้างเดิม",   value=f"{old_cam:,} caps")

            st.markdown("---")
            st.markdown("### ⚙️ 2. ระบุจำนวนเพื่อคำนวณยอด")

            col_ats, col_prt, col_cam = st.columns(3)
            with col_ats:
                st.markdown("<b style='color:#1E3A8A;'>[ เครื่อง ATS ]</b>", unsafe_allow_html=True)
                add_ats   = st.number_input("📥 พบงานค้างเพิ่ม",      min_value=0, step=1, key="add_ats")
                clear_ats = st.number_input("📤 เคลียร์งานสำเร็จ (-)", min_value=0, step=1, key="clear_ats")

            with col_prt:
                st.markdown("<b style='color:#1E3A8A;'>[ เครื่อง Printing ]</b>", unsafe_allow_html=True)
                add_prt   = st.number_input("📥 พบงานค้างเพิ่ม",      min_value=0, step=1, key="add_prt")
                clear_prt = st.number_input("📤 เคลียร์งานสำเร็จ (-)", min_value=0, step=1, key="clear_prt")

            with col_cam:
                st.markdown("<b style='color:#1E3A8A;'>[ เครื่อง Camera ]</b>", unsafe_allow_html=True)
                add_cam   = st.number_input("📥 พบงานค้างเพิ่ม",      min_value=0, step=1, key="add_cam")
                clear_cam = st.number_input("📤 เคลียร์งานสำเร็จ (-)", min_value=0, step=1, key="clear_cam")

            st.write("---")
            c_btn1, c_btn2 = st.columns(2)

            if c_btn1.form_submit_button("💾 คำนวณและบันทึกข้อมูลลง Cloud", use_container_width=True, type="primary"):
                final_ats   = (old_ats   + add_ats)   - clear_ats
                final_print = (old_print + add_prt)   - clear_prt
                final_cam   = (old_cam   + add_cam)   - clear_cam

                if final_ats < 0 or final_print < 0 or final_cam < 0:
                    st.error("❌ ไม่สามารถบันทึกได้ เนื่องจากจำนวนที่เคลียร์สูงเกินยอดคงค้าง (ยอดติดลบไม่ได้)")
                else:
                    new_backlog = pd.DataFrame([{
                        "Time":       datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Line":       st.session_state.sel_line,
                        "Batch":      st.session_state.sel_batch,
                        "ATS_caps":   final_ats,
                        "Print_caps": final_print,
                        "Cam_caps":   final_cam,
                        "Total_caps": final_ats + final_print + final_cam
                    }])
                    save_to_csv("backlog", new_backlog)
                    st.cache_data.clear()
                    st.success("🎉 อัปเดตและคำนวณยอด Backlog สำเร็จ!")
                    del st.session_state.sel_batch
                    st.rerun()

            if c_btn2.form_submit_button("❌ ยกเลิก/กลับ", use_container_width=True):
                del st.session_state.sel_batch
                st.rerun()
