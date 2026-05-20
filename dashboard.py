import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io


def show_dashboard_page(load_csv):
    st.markdown("<div class='main-header'>📈 Executive Production Dashboard</div>", unsafe_allow_html=True)

    df_plan    = load_csv("plan").fillna(0)
    df_box     = load_csv("box_status").fillna(0)
    df_backlog = load_csv("backlog").fillna(0)
    df_rej     = load_csv("rejection").fillna(0)
    df_camera  = load_csv("camera").fillna(0)
    df_repass  = load_csv("re_pass").fillna(0)

    from constants import STATUS_COLORS, LINES, BOX_STATUS

    # ── ฟังก์ชัน detect คอลัมน์แบบ case-insensitive ──────────────────────────
    def find_col(df, *candidates):
        """คืนชื่อคอลัมน์จริงที่ตรงกับ candidate ตัวใดตัวหนึ่ง (lower-strip)"""
        lmap = {c.strip().lower(): c for c in df.columns}
        for cand in candidates:
            if cand.strip().lower() in lmap:
                return lmap[cand.strip().lower()]
        return None

    # ── render_filter_widgets ─────────────────────────────────────────────────
    def render_filter_widgets(df_target, key_prefix):
        col_l, col_p, col_d = st.columns([1, 1, 1.5])

        line_col = find_col(df_target, 'Line', 'line', 'LINE')
        date_col = find_col(df_target, 'Time', 'time', 'Timestamp', 'timestamp', 'Date', 'date')

        if date_col and not df_target.empty:
            df_target[date_col] = pd.to_datetime(df_target[date_col], errors='coerce')
            df_target = df_target.dropna(subset=[date_col])

        with col_l:
            available_lines = ["ทั้งหมด"] + [str(l) for l in LINES]
            selected_line = st.selectbox("🏭 เลือกสายการผลิต (Line)", available_lines, key=f"{key_prefix}_line")

        with col_p:
            period_opt = ["เลือกช่วงวันที่เอง (Custom)", "รายสัปดาห์ (ย้อนหลัง 7 วัน)", "รายเดือน (ย้อนหลัง 30 วัน)"]
            selected_period = st.selectbox("📅 ตัวกรองรอบเวลา", period_opt, key=f"{key_prefix}_period")

        with col_d:
            if selected_period == "เลือกช่วงวันที่เอง (Custom)":
                if date_col and not df_target.empty:
                    min_d = df_target[date_col].min().date()
                    max_d = df_target[date_col].max().date()
                else:
                    min_d = datetime.now().date() - timedelta(days=30)
                    max_d = datetime.now().date()
                selected_dates = st.date_input("🗓️ เลือกวันที่ (เริ่ม - สิ้นสุด)", [min_d, max_d],
                                               key=f"{key_prefix}_date_range")
            else:
                st.info(f"⚡ ระบบเปิดใช้งานโหมด {selected_period} อัตโนมัติ")
                selected_dates = None

        df_filtered = df_target.copy()
        if line_col and selected_line != "ทั้งหมด":
            df_filtered = df_filtered[df_filtered[line_col].astype(str).str.strip() == str(selected_line).strip()]

        if date_col and not df_filtered.empty:
            if selected_period == "รายสัปดาห์ (ย้อนหลัง 7 วัน)":
                df_filtered = df_filtered[df_filtered[date_col] >= datetime.now() - timedelta(days=7)]
            elif selected_period == "รายเดือน (ย้อนหลัง 30 วัน)":
                df_filtered = df_filtered[df_filtered[date_col] >= datetime.now() - timedelta(days=30)]
            elif selected_period == "เลือกช่วงวันที่เอง (Custom)" and selected_dates and len(selected_dates) == 2:
                st_dt = pd.to_datetime(selected_dates[0]).replace(hour=0,  minute=0,  second=0)
                en_dt = pd.to_datetime(selected_dates[1]).replace(hour=23, minute=59, second=59)
                df_filtered = df_filtered[(df_filtered[date_col] >= st_dt) & (df_filtered[date_col] <= en_dt)]

        return df_filtered, selected_line

    # ── filter_sub_dataframe ──────────────────────────────────────────────────
    def filter_sub_dataframe(df_sub, selected_line, period_type, date_range_vals):
        df_sub_filtered = df_sub.copy()
        line_col = find_col(df_sub_filtered, 'Line', 'line', 'LINE')
        date_col = find_col(df_sub_filtered, 'Time', 'time', 'Timestamp', 'timestamp', 'Date', 'date')

        if line_col and selected_line != "ทั้งหมด":
            df_sub_filtered = df_sub_filtered[
                df_sub_filtered[line_col].astype(str).str.strip() == str(selected_line).strip()]

        if date_col and not df_sub_filtered.empty:
            df_sub_filtered[date_col] = pd.to_datetime(df_sub_filtered[date_col], errors='coerce')
            df_sub_filtered = df_sub_filtered.dropna(subset=[date_col])

            if period_type == "รายสัปดาห์ (ย้อนหลัง 7 วัน)":
                df_sub_filtered = df_sub_filtered[df_sub_filtered[date_col] >= datetime.now() - timedelta(days=7)]
            elif period_type == "รายเดือน (ย้อนหลัง 30 วัน)":
                df_sub_filtered = df_sub_filtered[df_sub_filtered[date_col] >= datetime.now() - timedelta(days=30)]
            elif period_type == "เลือกช่วงวันที่เอง (Custom)" and date_range_vals and len(date_range_vals) == 2:
                st_dt = pd.to_datetime(date_range_vals[0]).replace(hour=0,  minute=0,  second=0)
                en_dt = pd.to_datetime(date_range_vals[1]).replace(hour=23, minute=59, second=59)
                df_sub_filtered = df_sub_filtered[
                    (df_sub_filtered[date_col] >= st_dt) & (df_sub_filtered[date_col] <= en_dt)]
        return df_sub_filtered

    # ── Excel download ────────────────────────────────────────────────────────
    def create_excel_download_button(df_to_export, file_label, filename):
        towrite = io.BytesIO()
        with pd.ExcelWriter(towrite, engine='openpyxl') as writer:
            df_to_export.to_excel(writer, index=True, sheet_name='Dashboard_Report')
        towrite.seek(0)
        st.download_button(
            label=f"📥 Export {file_label} to Excel",
            data=towrite,
            file_name=f"{filename}_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # ── 3 แท็บหลัก ───────────────────────────────────────────────────────────
    t1, t2, t3 = st.tabs(["📊 11. Production Progress", "📷 12. Camera Analysis", "🔄 13. Re-pass Tracking"])

    # =========================================================
    # TAB 11: PRODUCTION PROGRESS
    # =========================================================
    with t1:
        st.markdown("### 🔍 ตัวกรองข้อมูลฝ่ายผลิตประจำสถานี")

        col_l, col_p, col_d = st.columns([1, 1, 1.5])
        with col_l:
            available_lines = ["ทั้งหมด"] + [str(l) for l in LINES]
            current_t1_line = st.selectbox("🏭 เลือกสายการผลิต (Line)", available_lines, key="t1_progress_line")
        with col_p:
            period_opt    = ["เลือกช่วงวันที่เอง (Custom)", "รายสัปดาห์ (ย้อนหลัง 7 วัน)", "รายเดือน (ย้อนหลัง 30 วัน)"]
            selected_period = st.selectbox("📅 ตัวกรองรอบเวลา", period_opt, key="t1_progress_period")
        with col_d:
            if selected_period == "เลือกช่วงวันที่เอง (Custom)":
                date_col_box = find_col(df_box, 'Time', 'time', 'Timestamp', 'Date', 'date')
                if date_col_box and not df_box.empty:
                    df_box[date_col_box] = pd.to_datetime(df_box[date_col_box], errors='coerce')
                    min_d = df_box[date_col_box].dropna().min().date() if not df_box[date_col_box].dropna().empty else datetime.now().date() - timedelta(days=30)
                    max_d = df_box[date_col_box].dropna().max().date() if not df_box[date_col_box].dropna().empty else datetime.now().date()
                else:
                    min_d = datetime.now().date() - timedelta(days=30)
                    max_d = datetime.now().date()
                selected_dates = st.date_input("🗓️ เลือกวันที่ (เริ่ม - สิ้นสุด)", [min_d, max_d], key="t1_progress_date_range")
            else:
                st.info(f"⚡ ระบบเปิดใช้งานโหมด {selected_period} อัตโนมัติ")
                selected_dates = None

        df_box_filtered  = filter_sub_dataframe(df_box,  current_t1_line, selected_period, selected_dates)
        df_rej_filtered  = filter_sub_dataframe(df_rej,  current_t1_line, selected_period, selected_dates)
        df_plan_filtered = filter_sub_dataframe(df_plan, current_t1_line, selected_period, selected_dates)

        st.write("---")

        # detect columns ─────────────────────────────────────────────────────
        status_col    = find_col(df_box_filtered, 'Status', 'status', 'Grade', 'grade') or 'Status'
        line_col_box  = find_col(df_box_filtered, 'Line', 'line', 'LINE') or 'Line'
        batch_col     = find_col(df_box_filtered, 'Batch', 'batch', 'BATCH')

        # ✅ detect 'Need af box' แบบ case-insensitive ครอบคลุมทุกรูปแบบ
        target_box_col = find_col(df_plan, 'Need af box', 'need af box', 'Need AF Box', 'need_af_box', 'Need Af Box')
        plan_line_col  = find_col(df_plan, 'Line', 'line', 'LINE')
        plan_batch_col = find_col(df_plan, 'Batch', 'batch', 'BATCH')

        # cleansing batch columns
        if batch_col and batch_col in df_box_filtered.columns:
            df_box_filtered[batch_col] = df_box_filtered[batch_col].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        if plan_batch_col and plan_batch_col in df_plan.columns:
            df_plan[plan_batch_col]          = df_plan[plan_batch_col].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
            df_plan_filtered[plan_batch_col] = df_plan_filtered[plan_batch_col].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

        # running batches
        if batch_col and batch_col in df_box_filtered.columns and not df_box_filtered.empty:
            running_batches   = df_box_filtered[df_box_filtered[batch_col] != '0'][batch_col].unique()
            running_batches   = [b for b in running_batches if b and b.lower() not in ('nan', '0', '')]
            running_batch_str = ", ".join(running_batches) if running_batches else "ไม่มี Batch Running"
        else:
            running_batches   = []
            running_batch_str = "ไม่พบข้อมูลคอลัมน์ Batch"

        # total target ───────────────────────────────────────────────────────
        total_target_box = 0
        if target_box_col and plan_batch_col and running_batches:
            df_running_plan  = df_plan[df_plan[plan_batch_col].isin(running_batches)].copy()
            df_running_plan[target_box_col] = pd.to_numeric(df_running_plan[target_box_col], errors='coerce').fillna(0)
            total_target_box = df_running_plan.groupby(plan_batch_col)[target_box_col].max().sum()
        elif target_box_col and target_box_col in df_plan_filtered.columns:
            total_target_box = pd.to_numeric(df_plan_filtered[target_box_col], errors='coerce').sum()

        # total actual AF
        if status_col in df_box_filtered.columns:
            total_actual = len(df_box_filtered[df_box_filtered[status_col].astype(str).str.upper().str.strip() == 'AF'])
        else:
            total_actual = 0

        # backlog
        backlog_total_col = find_col(df_backlog, 'Total_caps', 'total_caps')
        total_backlog = pd.to_numeric(df_backlog[backlog_total_col], errors='coerce').iloc[-1] if (backlog_total_col and not df_backlog.empty) else 0

        # rejection
        ats_col   = find_col(df_rej_filtered, 'ATS_kg',   'ats_kg')
        print_col = find_col(df_rej_filtered, 'Print_kg', 'print_kg')
        cam_col   = find_col(df_rej_filtered, 'Cam_kg',   'cam_kg')
        total_ats     = pd.to_numeric(df_rej_filtered[ats_col],   errors='coerce').sum() if ats_col   else 0.0
        total_print   = pd.to_numeric(df_rej_filtered[print_col], errors='coerce').sum() if print_col else 0.0
        total_cam_rej = pd.to_numeric(df_rej_filtered[cam_col],   errors='coerce').sum() if cam_col   else 0.0

        # metrics
        m1, m2, m3, mr1, mr2, mr3 = st.columns(6)
        m1.metric("🎯 Total Target (box)",      f"{total_target_box:,.0f}")
        m2.metric("✅ Good (AF) Boxes",          f"{total_actual:,.0f}")
        m3.metric("⏳ Current Backlog",           f"{total_backlog:,.0f}")
        mr1.metric("🗑️ Rejection ATS (kg)",      f"{total_ats:,.2f}")
        mr2.metric("🗑️ Rejection Print (kg)",    f"{total_print:,.2f}")
        mr3.metric("🗑️ Rejection Camera (kg)",   f"{total_cam_rej:,.2f}")

        st.info(f"🏃 **Running Batch ({'ไลน์: ' + current_t1_line if current_t1_line != 'ทั้งหมด' else 'ทุกสายการผลิต'}):** {running_batch_str}")
        st.write("---")

        # ── กราฟ 1: Production Progress % ───────────────────────────────────
        st.markdown("#### 📉 1. Production Progress Percentage By Line & Batch")

        if (status_col in df_box_filtered.columns
                and line_col_box in df_box_filtered.columns
                and batch_col and batch_col in df_box_filtered.columns
                and not df_box_filtered.empty):

            df_af = df_box_filtered[df_box_filtered[status_col].astype(str).str.upper().str.strip() == 'AF'].copy()
            df_prog_merge = df_af.groupby([line_col_box, batch_col]).size().reset_index(name='Good_Boxes')
            df_prog_merge[line_col_box] = df_prog_merge[line_col_box].astype(str).str.strip()
            df_prog_merge[batch_col]    = df_prog_merge[batch_col].astype(str).str.strip()

            for _c in [line_col_box, batch_col]:
                df_prog_merge = df_prog_merge[~df_prog_merge[_c].isin(['0', 'nan', '', 'None', 'null'])]

            if target_box_col and plan_batch_col:
                df_plan_map = df_plan.copy()
                df_plan_map[target_box_col] = pd.to_numeric(df_plan_map[target_box_col], errors='coerce').fillna(0)
                df_plan_map[plan_batch_col] = df_plan_map[plan_batch_col].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

                if plan_line_col:
                    df_plan_map[plan_line_col] = df_plan_map[plan_line_col].astype(str).str.strip()
                    df_target_map = (
                        df_plan_map
                        .groupby([plan_line_col, plan_batch_col])[target_box_col]
                        .first().reset_index()
                        .rename(columns={plan_line_col: line_col_box, plan_batch_col: batch_col, target_box_col: 'Target_Boxes'})
                    )
                    df_prog_merge = df_prog_merge.merge(df_target_map, on=[line_col_box, batch_col], how='left')
                else:
                    plan_dict = df_plan_map.groupby(plan_batch_col)[target_box_col].first().to_dict()
                    df_prog_merge['Target_Boxes'] = df_prog_merge[batch_col].map(plan_dict)

                df_prog_merge['Target_Boxes'] = df_prog_merge['Target_Boxes'].fillna(0)
            else:
                df_prog_merge['Target_Boxes'] = 0

            df_prog_merge['Progress_Percent'] = df_prog_merge.apply(
                lambda r: round(r['Good_Boxes'] / r['Target_Boxes'] * 100, 2) if r['Target_Boxes'] > 0 else 0.0, axis=1)
            df_prog_merge = df_prog_merge.sort_values([line_col_box, batch_col])
            df_prog_merge['X_Axis_Label'] = "Line " + df_prog_merge[line_col_box] + "<br>(" + df_prog_merge[batch_col] + ")"

            total_target_box = df_prog_merge['Target_Boxes'].sum()

            if not df_prog_merge.empty:
                fig_prog = go.Figure(data=[go.Bar(
                    x=df_prog_merge['X_Axis_Label'],
                    y=df_prog_merge['Progress_Percent'],
                    text=df_prog_merge['Progress_Percent'].map('{:,.1f}%'.format),
                    textposition='outside',
                    marker_color='#2ecc71',
                    customdata=df_prog_merge[['Good_Boxes', 'Target_Boxes']],
                    hovertemplate="<b>%{x}</b><br>AF: %{customdata[0]:,.0f} กล่อง<br>เป้า: %{customdata[1]:,.0f} กล่อง<br>Progress: %{y:.1f}%<extra></extra>"
                )])
                fig_prog.update_layout(
                    height=380, margin=dict(t=30, b=50, l=10, r=10),
                    plot_bgcolor='rgba(0,0,0,0)',
                    yaxis=dict(title="เปอร์เซ็นต์ความสำเร็จ (%)", ticksuffix="%",
                               range=[0, max(df_prog_merge['Progress_Percent'].max() * 1.2, 110)])
                )
                st.plotly_chart(fig_prog, use_container_width=True)
            else:
                st.info("💡 ไม่มีข้อมูลรายงานความคืบหน้าในรอบเวลานี้")

        st.write("---")

        # ── ตาราง 2: Box Status Matrix ───────────────────────────────────────
        mx_col1, mx_col2 = st.columns([3, 1])
        with mx_col1:
            st.markdown("#### 📦 2. Box Status Matrix")
        with mx_col2:
            if status_col in df_box_filtered.columns and line_col_box in df_box_filtered.columns and not df_box_filtered.empty:
                try:
                    df_mp = df_box_filtered.copy()
                    df_mp[status_col]   = df_mp[status_col].astype(str).str.strip().str.upper()
                    df_mp[line_col_box] = df_mp[line_col_box].astype(str).str.strip()
                    raw_m  = df_mp.pivot_table(index=status_col, columns=line_col_box, aggfunc='size', fill_value=0)
                    clean_bs = [str(s).strip().upper() for s in BOX_STATUS]
                    export_m = raw_m.reindex(clean_bs).fillna(0).astype(int)
                    create_excel_download_button(export_m, "Matrix Table", "Box_Status_Matrix")
                except Exception:
                    pass

        if status_col in df_box_filtered.columns and line_col_box in df_box_filtered.columns and not df_box_filtered.empty:
            try:
                df_mp = df_box_filtered.copy()
                df_mp[status_col] = df_mp[status_col].astype(str).str.strip().str.upper()
                df_mp[line_col_box] = df_mp[line_col_box].astype(str).str.strip()
                matrix = df_mp.pivot_table(index=status_col, columns=line_col_box, aggfunc='size', fill_value=0)
                clean_bs = [str(s).strip().upper() for s in BOX_STATUS]
                valid_idx = [i for i in clean_bs if i in matrix.index]
                matrix = matrix.reindex(valid_idx).fillna(0).astype(int) if valid_idx else matrix.fillna(0).astype(int)

                # ✅ map สีพื้นหลังตาม STATUS_COLORS (key เป็น upper เพื่อให้ตรงกับ index)
                STATUS_COLORS_UPPER = {k.upper(): v for k, v in STATUS_COLORS.items()}

                def color_row(row):
                    status = row.name  # index ของแถวคือชื่อ status (upper แล้ว)
                    bg = STATUS_COLORS_UPPER.get(status, "#ecf0f1")  # default เทาอ่อน
                    # คำนวณสีตัวอักษรให้ contrast กับพื้นหลัง
                    dark_bg = status in ['AF', 'SORT', 'PS']
                    text_color = "#ffffff" if status not in ['AF', 'SORT'] else "#1a1a2e"
                    return [
                        f"background-color: {bg}; color: {'#1a1a2e' if bg in ['#2ecc71', '#f1c40f'] else '#ffffff'}; font-weight: bold; text-align: right;"
                        if v > 0
                        else f"background-color: {bg}20; color: #94A3B8; text-align: right;"
                        for v in row
                    ]

                styled = matrix.style.apply(color_row, axis=1).format("{:,}")
                st.dataframe(styled, use_container_width=True)
            except Exception as e:
                st.error(f"⚠️ ไม่สามารถขึ้นรูปตาราง: {e}")
        else:
            st.info("💡 ไม่มีข้อมูล Box Status ในช่วงเวลาที่เลือก")

    # =========================================================
    # TAB 12: CAMERA ANALYSIS
    # =========================================================
    with t2:
        st.markdown("### 🔍 ตัวกรองการวิเคราะห์กล้องวิชั่น (Camera Filter)")
        df_camera_filtered, _ = render_filter_widgets(df_camera, "t2_camera")
        st.write("---")

        st.markdown("#### 🔴 1. Camera Defect Distribution (สัดส่วนสิ่งบกพร่องสะสม)")
        if not df_camera_filtered.empty:
            all_defs = []
            for col_cam in ['Cam1_Defects', 'Cam2_Defects']:
                if col_cam in df_camera_filtered.columns:
                    all_defs += df_camera_filtered[col_cam].astype(str).tolist()

            def_counts = {}
            for entry in all_defs:
                entry = str(entry).strip()
                if not entry or entry.lower() in ['nan', 'none', 'null', '0', '0.0', '-', '']:
                    continue
                for i in entry.split(","):
                    i = i.strip()
                    if not i or i.lower() in ['nan', 'none', 'null', '0', '0.0', '-', '']:
                        continue
                    if "(" in i and ")" in i:
                        try:
                            name      = i[:i.index("(")].strip()
                            count_str = i[i.index("(")+1: i.index(")")].strip()
                            count     = int(count_str) if count_str.isdigit() else 1
                        except Exception:
                            name, count = i.strip(), 1
                    elif i.endswith(")") and "(" not in i:
                        continue
                    else:
                        name, count = i.strip(), 1

                    if not name or not any(c.isalpha() for c in name):
                        continue
                    if name.lower() in ['nan', 'none', 'null', '0', '0.0', '-']:
                        continue
                    def_counts[name] = def_counts.get(name, 0) + count

            if def_counts:
                df_def_plot = pd.DataFrame(list(def_counts.items()), columns=['Defect', 'Qty'])
                df_def_plot = df_def_plot[df_def_plot['Qty'] > 0].sort_values('Qty', ascending=False)
                if not df_def_plot.empty:
                    fig_def = px.pie(df_def_plot, values='Qty', names='Defect', hole=0.4,
                                     color_discrete_sequence=px.colors.qualitative.Pastel)
                    fig_def.update_traces(textposition='inside', textinfo='percent+label')
                    fig_def.update_layout(height=380, margin=dict(t=10, b=10, l=10, r=10))
                    st.plotly_chart(fig_def, use_container_width=True)
                else:
                    st.info("🟢 ไม่มีรายการของเสียในช่วงเวลานี้")
            else:
                st.info("🟢 ยังไม่มีรายการประวัติของเสียในช่วงนี้")
        else:
            st.info("💡 ไม่มีข้อมูลบันทึกในช่วงเวลาที่เลือก")

        st.write("---")

        tx_col1, tx_col2 = st.columns([3, 1])
        with tx_col1:
            st.markdown("#### 📷 2. Camera Performance Summary Table (สรุปรายไลน์)")
        with tx_col2:
            cam_line_col = find_col(df_camera_filtered, 'Line', 'line')
            if not df_camera_filtered.empty and cam_line_col:
                try:
                    excel_cam = df_camera_filtered.groupby(cam_line_col).agg(
                        {'Cam1_Pass_Rate': 'mean', 'Cam2_Pass_Rate': 'mean'})
                    create_excel_download_button(excel_cam, "Camera Performance Table", "Camera_Performance")
                except Exception:
                    pass

        if not df_camera_filtered.empty and cam_line_col:
            df_cam_calc = df_camera_filtered.copy()
            df_cam_calc['Cam1_Pass_Rate'] = pd.to_numeric(df_cam_calc['Cam1_Pass_Rate'], errors='coerce').fillna(100.0)
            df_cam_calc['Cam2_Pass_Rate'] = pd.to_numeric(df_cam_calc['Cam2_Pass_Rate'], errors='coerce').fillna(100.0)

            cam_summary = df_cam_calc.groupby(cam_line_col).agg(
                Cam1_Avg_Pass=('Cam1_Pass_Rate', 'mean'),
                Cam2_Avg_Pass=('Cam2_Pass_Rate', 'mean'),
                Recent_Defects=('Cam1_Defects', lambda x: (", ".join(
                    sorted(set(str(v).strip() for v in x
                               if str(v).strip() not in ['', 'nan', 'None', '0', '0.0', 'null', 'None', '-'])))[:80] + "..."
                ) if any(str(v).strip() not in ['', 'nan', 'None', '0', '0.0', 'null', '-'] for v in x) else "-")
            ).reset_index()
            cam_summary.columns = ['Line', 'Camera 1 Avg Pass Rate (%)', 'Camera 2 Avg Pass Rate (%)', 'Recent Detected Defects']
            st.dataframe(
                cam_summary.style.format({'Camera 1 Avg Pass Rate (%)': '{:.2f}%', 'Camera 2 Avg Pass Rate (%)': '{:.2f}%'}),
                use_container_width=True, hide_index=True)
        else:
            st.info("💡 ไม่พบโครงสร้างตารางข้อมูลเพื่อคำนวณ")

    # =========================================================
    # TAB 13: RE-PASS TRACKING
    # =========================================================
    with t3:
        st.markdown("### 🔍 ตัวกรองประวัติการแก้ไขงานทำซ้ำ (Re-pass Filter)")
        df_repass_filtered, _ = render_filter_widgets(df_repass, "t3_repass")
        st.write("---")

        st.markdown("##### 📍 แผนภูมิปริมาณความถี่การส่งงาน Re-pass แยกราย Line")
        rp_line_col = find_col(df_repass_filtered, 'Line', 'line')
        if not df_repass_filtered.empty and rp_line_col:
            repass_counts = df_repass_filtered.groupby(rp_line_col).size().reset_index(name='Counts')
            fig_re = px.bar(repass_counts, x=rp_line_col, y='Counts', text='Counts',
                            color='Counts', color_continuous_scale='Reds')
            fig_re.update_traces(textposition='outside')
            fig_re.update_layout(plot_bgcolor='rgba(0,0,0,0)', height=320)
            st.plotly_chart(fig_re, use_container_width=True)
        else:
            st.info("🔄 ไม่มีข้อมูลประวัติการส่งชิ้นงาน Re-pass")

        st.write("---")

        # ✅ เปลี่ยนจาก Result_Status pie → Defect Distribution จาก box_status
        st.markdown("##### 🏁 Defect Distribution จากข้อมูล Box Status (สถิติของเสียสะสม)")

        box_status_col  = find_col(df_box, 'Status', 'status')
        box_defect_col  = find_col(df_box, 'Defects', 'defects')
        box_line_col    = find_col(df_box, 'Line', 'line')

        if not df_box.empty and box_defect_col and box_status_col:
            # กรองเฉพาะกล่องที่ไม่ใช่ AF (มีของเสีย)
            df_box_rej = df_box[df_box[box_status_col].astype(str).str.upper().str.strip() != 'AF'].copy()
            df_box_rej = df_box_rej[df_box_rej[box_defect_col].astype(str).str.strip().str.lower().isin(['', 'nan', 'none']) == False]

            defect_counts = {}
            for val in df_box_rej[box_defect_col].astype(str):
                for d in val.split(","):
                    d = d.strip()
                    if d and d.lower() not in ['nan', 'none', '', '0', '-']:
                        defect_counts[d] = defect_counts.get(d, 0) + 1

            if defect_counts:
                df_def = pd.DataFrame(list(defect_counts.items()), columns=['Defect', 'Count'])
                df_def = df_def.sort_values('Count', ascending=False)

                fig_def_box = px.bar(
                    df_def, x='Defect', y='Count', text='Count',
                    color='Count', color_continuous_scale='Reds',
                    title="สถิติของเสียสะสม (Box Status)"
                )
                fig_def_box.update_traces(textposition='outside')
                fig_def_box.update_layout(
                    height=380, plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(t=40, b=50, l=10, r=10),
                    xaxis_title="ประเภทของเสีย", yaxis_title="จำนวน (กล่อง)"
                )
                st.plotly_chart(fig_def_box, use_container_width=True)
            else:
                st.success("🟢 ไม่มีข้อมูลของเสียใน Box Status")
        else:
            st.info("💡 ไม่มีข้อมูล Box Status")

        st.write("---")

        st.markdown("##### 📋 รายการกล่องที่รอการ Re-pass (box_status ที่ไม่ใช่ AF)")
        if box_status_col and not df_box.empty:
            df_pending_box = df_box[df_box[box_status_col].astype(str).str.strip().str.upper() != 'AF']
            if not df_pending_box.empty:
                st.dataframe(df_pending_box, use_container_width=True, hide_index=True)
                st.caption(f"⚠️ ตรวจพบกล่องคงค้าง: {len(df_pending_box):,} กล่อง")
            else:
                st.success("🟢 ไม่มีรายการงานค้างสะสม ทุกกล่องผ่านเกณฑ์ AF แล้ว")
        else:
            st.info("💡 ไม่มีข้อมูล Box Status")

    st.caption(f"📊 ประมวลผลล่าสุด: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
