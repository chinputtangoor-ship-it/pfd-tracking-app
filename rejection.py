import streamlit as st
import pandas as pd
from datetime import datetime


def show_rejection_page(load_csv, save_to_csv):
    st.markdown("<div class='main-header'>🗑️ Rejection Weight Recording</div>", unsafe_allow_html=True)

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
                    if cols[col_idx].button(line_name, key=f"rej_line_btn_{line_name}", use_container_width=True):
                        st.session_state.sel_line = line_name
                        st.rerun()

    elif 'sel_batch' not in st.session_state:
        st.subheader(f"📍 Line: {st.session_state.sel_line} > เลือก Batch")
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
                if cols[i % 3].button(f"Batch: {b}", key=f"rej_batch_{b}", use_container_width=True):
                    st.session_state.sel_batch = b
                    st.rerun()
        else:
            st.warning("⚠️ ไม่มี Batch ที่กำลัง Running ใน Line นี้")

        if st.button("🔙 เปลี่ยน Line", use_container_width=True):
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
            w_ats   = r1.number_input("ATS Weight",   min_value=0.0, step=0.001, format="%.3f", label_visibility="collapsed")
            w_print = r2.number_input("Print Weight",  min_value=0.0, step=0.001, format="%.3f", label_visibility="collapsed")
            w_cam   = r3.number_input("Cam Weight",    min_value=0.0, step=0.001, format="%.3f", label_visibility="collapsed")

            st.divider()
            c1, c2 = st.columns(2)

            if c1.form_submit_button("💾 บันทึกข้อมูล", use_container_width=True, type="primary"):
                new_rej_data = pd.DataFrame([{
                    "Time":     datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Line":     st.session_state.sel_line,
                    "Batch":    st.session_state.sel_batch,
                    "ATS_kg":   w_ats,
                    "Print_kg": w_print,
                    "Cam_kg":   w_cam
                }])
                save_to_csv("rejection", new_rej_data)
                st.cache_data.clear()
                st.success("🎉 บันทึกน้ำหนักงานเสีย สำเร็จ!")
                del st.session_state.sel_batch
                st.rerun()

            if c2.form_submit_button("❌ ยกเลิก", use_container_width=True):
                del st.session_state.sel_batch
                st.rerun()
