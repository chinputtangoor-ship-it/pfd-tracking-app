import streamlit as st
import pandas as pd
from datetime import datetime, timedelta


def show_repass_page(load_csv, save_to_csv, conn):
    st.markdown("<div class='main-header'>🔄 Re-pass Management</div>", unsafe_allow_html=True)
    df_box = load_csv("box_status").fillna("")

    # detect columns ของ box_status
    line_col_box   = next((c for c in df_box.columns if c.strip().lower() == 'line'),    None)
    status_col_box = next((c for c in df_box.columns if c.strip().lower() == 'status'),  None)
    batch_col_box  = next((c for c in df_box.columns if c.strip().lower() == 'batch'),   None)
    box_col_box    = next((c for c in df_box.columns if c.strip().lower() == 'box'),     None)
    defect_col_box = next((c for c in df_box.columns if c.strip().lower() == 'defects'), None)

    # ==========================================
    # STEP 1: เลือก Line
    # ==========================================
    if 'sel_line_re' not in st.session_state and 'sel_batch_re' not in st.session_state:

        # ปุ่มดูข้อมูล Re-pass
        if st.button("📋 ดูข้อมูล Re-pass", use_container_width=True):
            st.session_state['view_repass'] = True
            st.rerun()

        # โหมดดูข้อมูล Re-pass
        if st.session_state.get('view_repass', False):
            st.markdown("### 📋 ข้อมูล Re-pass")
            df_rp = load_csv("re_pass").fillna("")

            if not df_rp.empty:
                time_col_rp = next((c for c in df_rp.columns if c.strip().lower() == 'time'), None)
                if time_col_rp:
                    df_rp[time_col_rp] = pd.to_datetime(df_rp[time_col_rp], errors='coerce')

                fc1, fc2 = st.columns([1, 2])
                with fc1:
                    period_opt = ["ทั้งหมด", "รายสัปดาห์ (7 วันล่าสุด)", "เลือกช่วงวันที่เอง"]
                    sel_period = st.selectbox("📅 ช่วงเวลา", period_opt, key="rp_view_period")
                with fc2:
                    sel_dates = None
                    if sel_period == "เลือกช่วงวันที่เอง" and time_col_rp:
                        min_d = df_rp[time_col_rp].dropna().min().date() if not df_rp[time_col_rp].dropna().empty else datetime.now().date() - timedelta(days=30)
                        max_d = df_rp[time_col_rp].dropna().max().date() if not df_rp[time_col_rp].dropna().empty else datetime.now().date()
                        sel_dates = st.date_input("เลือกวันที่", [min_d, max_d], key="rp_view_dates")

                df_view = df_rp.copy()
                if time_col_rp and not df_view.empty:
                    if sel_period == "รายสัปดาห์ (7 วันล่าสุด)":
                        df_view = df_view[df_view[time_col_rp] >= datetime.now() - timedelta(days=7)]
                    elif sel_period == "เลือกช่วงวันที่เอง" and sel_dates and len(sel_dates) == 2:
                        st_dt = pd.to_datetime(sel_dates[0]).replace(hour=0,  minute=0,  second=0)
                        en_dt = pd.to_datetime(sel_dates[1]).replace(hour=23, minute=59, second=59)
                        df_view = df_view[(df_view[time_col_rp] >= st_dt) & (df_view[time_col_rp] <= en_dt)]

                st.caption(f"แสดง {len(df_view):,} รายการ")
                st.dataframe(df_view, use_container_width=True, hide_index=True)
            else:
                st.info("ยังไม่มีข้อมูล Re-pass")

            if st.button("🔙 ปิดหน้าดูข้อมูล", use_container_width=True):
                st.session_state['view_repass'] = False
                st.rerun()
            return

        # เลือก Line
        st.subheader("📍 1. เลือก Line ที่ต้องการจัดการ")
        active_lines = []
        if not df_box.empty and line_col_box and status_col_box:
            active_lines = df_box[df_box[status_col_box] != 'AF'][line_col_box].unique().tolist()

        cols = st.columns(3)
        for i, line in enumerate(active_lines):
            if cols[i % 3].button(f"Line: {line}", key=f"btn_line_{line}", use_container_width=True):
                st.session_state['sel_line_re']  = line
                st.session_state['view_repass']  = False
                st.rerun()

        next_idx = len(active_lines)
        if cols[next_idx % 3].button("➕ Other (ระบุเอง)", key="btn_other_re", use_container_width=True):
            st.session_state['sel_line_re']  = "Other"
            st.session_state['sel_batch_re'] = "Other"
            st.session_state['view_repass']  = False
            st.rerun()

        st.write("---")

    # ==========================================
    # STEP 2: เลือก Batch
    # ==========================================
    elif 'sel_line_re' in st.session_state and 'sel_batch_re' not in st.session_state:
        line_target = st.session_state['sel_line_re']
        st.subheader(f"📍 2. เลือก Batch ใน {line_target} ที่มีงานเสีย")

        active_rej_batches = []
        if not df_box.empty and line_col_box and status_col_box and batch_col_box:
            active_rej_batches = df_box[
                (df_box[line_col_box] == line_target) &
                (df_box[status_col_box] != 'AF')
            ][batch_col_box].unique().tolist()

        if not active_rej_batches:
            st.warning(f"❌ ไม่พบงานเสียคงค้างใน Line: {line_target}")
        else:
            cols = st.columns(3)
            for i, batch in enumerate(active_rej_batches):
                if cols[i % 3].button(f"Batch: {batch}", key=f"btn_batch_{batch}", use_container_width=True):
                    st.session_state['sel_batch_re'] = batch
                    st.rerun()

        st.write("---")
        if st.button("⬅️ กลับไปเลือก Line", use_container_width=True):
            del st.session_state['sel_line_re']
            st.rerun()

    # ==========================================
    # STEP 3: บันทึก Re-pass
    # ==========================================
    else:
        from constants import DEFECT_LIST, LINES, BOX_STATUS

        line_target  = st.session_state.get('sel_line_re', 'Other')
        batch_target = st.session_state['sel_batch_re']

        st.subheader("🔄 บันทึกข้อมูล Re-pass ลง Cloud")
        st.info(f"✅ **Line:** {line_target}  |  🆔 **Batch:** {batch_target}")

        # เลือกกล่องและดึงสถานะเดิม
        if batch_target == "Other":
            f_line         = st.selectbox("ระบุ Line", LINES)
            f_batch        = st.text_input("ระบุเลข Batch")
            f_box_num      = st.text_input("ระบุเลขกล่อง")
            current_stat   = "N/A"
            old_defect_val = "ระบุเอง"
        else:
            f_line  = line_target
            f_batch = batch_target

            boxes_to_fix = pd.DataFrame()
            if not df_box.empty and batch_col_box and status_col_box:
                boxes_to_fix = df_box[
                    (df_box[batch_col_box].astype(str) == str(batch_target)) &
                    (df_box[status_col_box] != 'AF')
                ]

            box_list  = boxes_to_fix[box_col_box].unique().tolist() if box_col_box and not boxes_to_fix.empty else []
            f_box_num = st.selectbox("เลือกเลขกล่อง", box_list)

            if f_box_num and not boxes_to_fix.empty and box_col_box:
                match          = boxes_to_fix[boxes_to_fix[box_col_box].astype(str) == str(f_box_num)].iloc[-1]
                current_stat   = match[status_col_box]
                old_defect_val = match[defect_col_box] if defect_col_box and match[defect_col_box] != "" else "ไม่มี Defect"
            else:
                current_stat, old_defect_val = "N/A", "N/A"

        st.warning(f"📌 สถานะเดิมในระบบ: **{current_stat}** | Defect เดิม: **{old_defect_val}**")

        # ประเภทงาน
        mode = st.radio("ประเภทงาน Re-pass", ["Online", "Offline"], horizontal=True)

        # ⏰ เวลาเริ่มงาน
        st.markdown("**⏰ เวลาเริ่มงาน Re-pass**")
        tc1, tc2 = st.columns(2)
        start_date = tc1.date_input("วันที่เริ่มงาน", value=datetime.now().date(), key="rp_start_date")

        time_options = [f"{h:02d}:{m:02d}" for h in range(0, 24) for m in (0, 15, 30, 45)]
        now_minute  = datetime.now().minute
        rounded_m   = (now_minute // 15) * 15
        default_t   = datetime.now().strftime(f"%H:{rounded_m:02d}")
        default_idx = time_options.index(default_t) if default_t in time_options else 0
        start_time  = tc2.selectbox("เวลาเริ่มงาน", time_options, index=default_idx, key="rp_start_time")

        start_datetime_str = f"{start_date} {start_time}"

        # สถานะหลัง Re-pass
        new_stat       = st.selectbox("สถานะหลังทำการ Re-pass", BOX_STATUS, key="repass_stat_select")
        show_def_input = new_stat != "AF"

        # Form บันทึก
        with st.form("repass_final_action"):
            new_def      = []
            final_reason = ""

            if show_def_input:
                st.markdown("<b style='color:red;'>⚠️ จำเป็นต้องระบุข้อมูลรายละเอียด Defect ด้านล่างนี้</b>",
                            unsafe_allow_html=True)
                new_def      = st.multiselect("🔴 ระบุ Defect (เลือกได้มากกว่า 1 รายการ)", DEFECT_LIST)
                final_reason = st.text_area("ระบุเหตุผลหรือหมายเหตุเพิ่มเติม")

            st.write("---")
            c1, c2 = st.columns(2)

            if c1.form_submit_button("💾 บันทึกการ Re-pass ลง Cloud", use_container_width=True, type="primary"):
                if not f_batch or not f_box_num:
                    st.error("❌ ไม่สามารถบันทึกได้: กรุณาระบุข้อมูล Batch และเลขกล่องให้ครบถ้วน")
                elif show_def_input and not new_def:
                    st.error(f"❌ ไม่สามารถบันทึกได้: สถานะ [{new_stat}] จำเป็นต้องระบุ Defect อย่างน้อย 1 รายการ")
                else:
                    new_rp_record = pd.DataFrame([{
                        "Time":            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Line":            f_line,
                        "Batch":           f_batch,
                        "Box":             f_box_num,
                        "Previous_Status": current_stat,
                        "Result_Status":   new_stat,
                        "New_Defects":     ",".join(new_def) if show_def_input else "",
                        "Type":            mode,
                        "Reason":          "Normal Re-pass" if new_stat == "AF" else final_reason,
                        "Start time":      start_datetime_str,  # ✅ ตรงชื่อ sheet จริง
                    }])

                    save_to_csv("re_pass", new_rp_record)

                    # อัปเดต box_status
                    if batch_target != "Other" and batch_col_box and box_col_box and status_col_box:
                        new_def_str = ",".join(new_def) if show_def_input else ""
                        mask = (
                            (df_box[batch_col_box].astype(str) == str(f_batch)) &
                            (df_box[box_col_box].astype(str)   == str(f_box_num))
                        )
                        df_box.loc[mask, status_col_box] = new_stat
                        if defect_col_box:
                            df_box.loc[mask, defect_col_box] = new_def_str
                        conn.update(worksheet="box_status", data=df_box)

                    st.cache_data.clear()
                    st.success("🎉 บันทึกข้อมูลและปรับเปลี่ยนสถานะเรียบร้อยแล้ว!")
                    for key in ['sel_line_re', 'sel_batch_re']:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()

            if c2.form_submit_button("❌ ยกเลิกและกลับ", use_container_width=True):
                for key in ['sel_line_re', 'sel_batch_re']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
