import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io


def show_dashboard_page(load_csv):
    st.markdown("<div class='main-header'>📈 Executive Production Dashboard</div>", unsafe_allow_html=True)

    # 📥 1. โหลดข้อมูลทั้งหมดจากระบบคลาวด์ชีต
    df_plan = load_csv("plan").fillna(0)
    df_box = load_csv("box_status").fillna(0)
    df_backlog = load_csv("backlog").fillna(0)
    df_rej = load_csv("rejection").fillna(0)
    df_camera = load_csv("camera").fillna(0)
    df_repass = load_csv("re_pass").fillna(0)

    from constants import STATUS_COLORS, LINES, BOX_STATUS

    # 🛠️ ฟังก์ชันส่วนกลาง: ระบบกรองข้อมูลขั้นสูง (ตัวกรองอ้างอิงช่วงเวลาและสายการผลิต)
    def render_filter_widgets(df_target, key_prefix):
        col_l, col_p, col_d = st.columns([1, 1, 1.5])

        line_col = next((c for c in ['Line', 'line', 'LINE'] if c in df_target.columns), None)
        date_col = next((c for c in ['Timestamp', 'timestamp', 'Date', 'date'] if c in df_target.columns), None)

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
                    min_d, max_d = datetime.now().date() - timedelta(days=30), datetime.now().date()
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
                cutoff = datetime.now() - timedelta(days=7)
                df_filtered = df_filtered[df_filtered[date_col] >= cutoff]
            elif selected_period == "รายเดือน (ย้อนหลัง 30 วัน)":
                cutoff = datetime.now() - timedelta(days=30)
                df_filtered = df_filtered[df_filtered[date_col] >= cutoff]
            elif selected_period == "เลือกช่วงวันที่เอง (Custom)" and selected_dates and len(selected_dates) == 2:
                start_dt = pd.to_datetime(selected_dates[0]).replace(hour=0, minute=0, second=0)
                end_dt = pd.to_datetime(selected_dates[1]).replace(hour=23, minute=59, second=59)
                df_filtered = df_filtered[(df_filtered[date_col] >= start_dt) & (df_filtered[date_col] <= end_dt)]

        return df_filtered, selected_line

    # 🛠️ ฟังก์ชันสำหรับกรองตารางย่อยอื่น ๆ ให้ซิงค์ตามเงื่อนไขของตารางหลักโดยตรง
    def filter_sub_dataframe(df_sub, selected_line, period_type, date_range_vals):
        df_sub_filtered = df_sub.copy()
        line_col = next((c for c in ['Line', 'line', 'LINE'] if c in df_sub_filtered.columns), None)
        date_col = next(
            (c for c in ['Time', 'time', 'Timestamp', 'timestamp', 'Date', 'date', 'uploaded_date'] if
             c in df_sub_filtered.columns),
            None)

        if line_col and selected_line != "ทั้งหมด":
            df_sub_filtered = df_sub_filtered[
                df_sub_filtered[line_col].astype(str).str.strip() == str(selected_line).strip()]

        if date_col and not df_sub_filtered.empty:
            df_sub_filtered[date_col] = pd.to_datetime(df_sub_filtered[date_col], errors='coerce')
            df_sub_filtered = df_sub_filtered.dropna(subset=[date_col])

            if period_type == "รายสัปดาห์ (ย้อนหลัง 7 วัน)":
                df_sub_filtered = df_sub_filtered[df_sub_filtered[date_col] >= (datetime.now() - timedelta(days=7))]
            elif period_type == "รายเดือน (ย้อนหลัง 30 วัน)":
                df_sub_filtered = df_sub_filtered[df_sub_filtered[date_col] >= (datetime.now() - timedelta(days=30))]
            elif period_type == "เลือกช่วงวันที่เอง (Custom)" and date_range_vals and len(date_range_vals) == 2:
                st_dt = pd.to_datetime(date_range_vals[0]).replace(hour=0, minute=0, second=0)
                en_dt = pd.to_datetime(date_range_vals[1]).replace(hour=23, minute=59, second=59)
                df_sub_filtered = df_sub_filtered[
                    (df_sub_filtered[date_col] >= st_dt) & (df_sub_filtered[date_col] <= en_dt)]
        return df_sub_filtered

    # 🛠️ ฟังก์ชันสร้างปุ่มดาวน์โหลดไฟล์ Excel (.xlsx)
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

    # 📋 2. จัดสร้างแถบ 3 แท็บใหญ่สำหรับการสแกนโมเดลข้อมูล
    t1, t2, t3 = st.tabs(["📊 11. Production Progress", "📷 12. Camera Analysis", "🔄 13. Re-pass Tracking"])

    # =========================================================
    # 📑 TAB 11: PROGRESS
    # =========================================================
    with t1:
        st.markdown("### 🔍 ตัวกรองข้อมูลฝ่ายผลิตประจำสถานี")

        # ดึงสถานะตัวแปรฟิลเตอร์ของ Tab 1 มาใช้งานควบคุมทุกตารางที่เกี่ยวข้อง
        col_l, col_p, col_d = st.columns([1, 1, 1.5])
        with col_l:
            available_lines = ["ทั้งหมด"] + [str(l) for l in LINES]
            current_t1_line = st.selectbox("🏭 เลือกสายการผลิต (Line)", available_lines, key="t1_progress_line")
        with col_p:
            period_opt = ["เลือกช่วงวันที่เอง (Custom)", "รายสัปดาห์ (ย้อนหลัง 7 วัน)", "รายเดือน (ย้อนหลัง 30 วัน)"]
            selected_period = st.selectbox("📅 ตัวกรองรอบเวลา", period_opt, key="t1_progress_period")
        with col_d:
            if selected_period == "เลือกช่วงวันที่เอง (Custom)":
                date_col_box = next((c for c in ['Timestamp', 'timestamp', 'Date', 'date'] if c in df_box.columns),
                                    None)
                if date_col_box and not df_box.empty:
                    df_box[date_col_box] = pd.to_datetime(df_box[date_col_box], errors='coerce')
                    min_d = df_box[date_col_box].dropna().min().date() if not df_box[
                        date_col_box].dropna().empty else datetime.now().date() - timedelta(days=30)
                    max_d = df_box[date_col_box].dropna().max().date() if not df_box[
                        date_col_box].dropna().empty else datetime.now().date()
                else:
                    min_d, max_d = datetime.now().date() - timedelta(days=30), datetime.now().date()
                selected_dates = st.date_input("🗓️ เลือกวันที่ (เริ่ม - สิ้นสุด)", [min_d, max_d],
                                               key="t1_progress_date_range")
            else:
                st.info(f"⚡ ระบบเปิดใช้งานโหมด {selected_period} อัตโนมัติ")
                selected_dates = None

        # ทำการกรองตารางกล่องหลัก และตาราง Rejection, Plan ตามฟิลเตอร์ทันทีเพื่อความสอดคล้องกันของรูป 1 และ 2
        df_box_filtered = filter_sub_dataframe(df_box, current_t1_line, selected_period, selected_dates)
        df_rej_filtered = filter_sub_dataframe(df_rej, current_t1_line, selected_period, selected_dates)
        df_plan_filtered = filter_sub_dataframe(df_plan, current_t1_line, selected_period, selected_dates)

        st.write("---")

        # ตรวจสอบหัวคอลัมน์แบบยืดหยุ่น (Case-insensitive)
        status_col = next((c for c in ['Status', 'status', 'Grade', 'grade'] if c in df_box_filtered.columns), 'Status')
        line_col_box = next((c for c in ['Line', 'line', 'LINE'] if c in df_box_filtered.columns), 'Line')
        batch_col = next((c for c in ['Batch', 'batch', 'BATCH'] if c in df_box_filtered.columns), None)
        target_box_col = next((c for c in ['need af box', 'need_af_box', 'Need AF Box'] if c in df_plan.columns),
                              'need af box')
        plan_batch_col = next((c for c in ['Batch', 'batch', 'BATCH'] if c in df_plan.columns), 'Batch')

        # ✨ [CLEANSING POINT] จัดการล้างข้อมูลคอลัมน์ Batch ของทุกตารางให้ฟอร์แมตข้อความสะอาดเท่ากัน
        if batch_col and batch_col in df_box_filtered.columns:
            # แปลงเป็น string -> ตัด .0 (กรณีหลุดมาจาก float) -> ลบช่องว่างหัวท้าย
            df_box_filtered[batch_col] = df_box_filtered[batch_col].astype(str).str.replace(r'\.0$', '',
                                                                                            regex=True).str.strip()

        if plan_batch_col in df_plan.columns:
            df_plan[plan_batch_col] = df_plan[plan_batch_col].astype(str).str.replace(r'\.0$', '',
                                                                                      regex=True).str.strip()
            df_plan_filtered[plan_batch_col] = df_plan_filtered[plan_batch_col].astype(str).str.replace(r'\.0$', '',
                                                                                                        regex=True).str.strip()

        # ค้นหา Running Batch ให้สัมพันธ์กับไลน์ที่เลือก
        if batch_col and batch_col in df_box_filtered.columns and not df_box_filtered.empty:
            running_batches = df_box_filtered[df_box_filtered[batch_col] != '0'][batch_col].unique()
            running_batches = [b for b in running_batches if b and b.lower() != 'nan' and b != '0']
            running_batch_str = ", ".join(running_batches) if running_batches else "ไม่มี Batch Running"
        else:
            running_batches = []
            running_batch_str = "ไม่พบข้อมูลคอลัมน์ Batch"

        # 🎯 คำนวณหา Total Target (box) อิงตาม Batch เดี่ยวๆ
        if target_box_col in df_plan.columns and plan_batch_col in df_plan.columns and running_batches:
            df_plan_all = df_plan.copy()
            df_running_plan = df_plan_all[df_plan_all[plan_batch_col].isin(running_batches)]
            # ดึงค่าสูงสุดรายแผนงานของ Batch นั้นๆ แล้วนำมารวมกัน
            total_target_box = df_running_plan.groupby(plan_batch_col)[target_box_col].max().sum()
        else:
            if target_box_col in df_plan_filtered.columns:
                total_target_box = pd.to_numeric(df_plan_filtered[target_box_col], errors='coerce').sum()
            else:
                total_target_box = 0

        # คำนวณจำนวนกล่องสถานะของดี (AF) ของไลน์ช่วงเวลานั้นๆ
        if status_col in df_box_filtered.columns:
            total_actual = len(df_box_filtered[df_box_filtered[status_col].astype(str).str.upper().str.strip() == 'AF'])
        else:
            total_actual = 0

        total_backlog = pd.to_numeric(df_backlog['Total_caps'], errors='coerce').iloc[-1] if not df_backlog.empty else 0

        # ยอด Rejection
        total_ats = pd.to_numeric(df_rej_filtered['ATS_kg'],
                                  errors='coerce').sum() if 'ATS_kg' in df_rej_filtered.columns else 0.0
        total_print = pd.to_numeric(df_rej_filtered['Print_kg'],
                                    errors='coerce').sum() if 'Print_kg' in df_rej_filtered.columns else 0.0
        total_cam_rej = pd.to_numeric(df_rej_filtered['Cam_kg'],
                                      errors='coerce').sum() if 'Cam_kg' in df_rej_filtered.columns else 0.0

        # แสดงผลเมทริกซ์หลัก 6 ช่อง
        m1, m2, m3, mr1, mr2, mr3 = st.columns(6)
        m1.metric("🎯 Total Target (box)", f"{total_target_box:,.0f}")
        m2.metric("✅ Good (AF) Boxes", f"{total_actual:,.0f}")
        m3.metric("⏳ Current Backlog", f"{total_backlog:,.0f}")
        mr1.metric("🗑️ Rejection ATS (kg)", f"{total_ats:,.2f}")
        mr2.metric("🗑️ Rejection Print (kg)", f"{total_print:,.2f}")
        mr3.metric("🗑️ Rejection Camera (kg)", f"{total_cam_rej:,.2f}")

        st.info(
            f"🏃 **Running Batch ปัจจุบัน ({'ไลน์การผลิต: ' + current_t1_line if current_t1_line != 'ทั้งหมด' else 'ทุกสายการผลิต'}):** {running_batch_str}")
        st.write("---")

        # --- แถวแรก: กราฟแท่งความคืบหน้าคิดเป็น % ---
        st.markdown("#### 📉 1. Production Progress Percentage By Line & Batch (% งานที่เสร็จเทียบกับเป้าหมาย)")

        if (status_col in df_box_filtered.columns
                and line_col_box in df_box_filtered.columns
                and batch_col and batch_col in df_box_filtered.columns
                and not df_box_filtered.empty):

            # 1. นับ AF boxes แยกราย Line + Batch
            df_af = df_box_filtered[
                df_box_filtered[status_col].astype(str).str.upper().str.strip() == 'AF'
                ].copy()

            df_prog_merge = (
                df_af.groupby([line_col_box, batch_col])
                .size()
                .reset_index(name='Good_Boxes')
            )
            df_prog_merge[line_col_box] = df_prog_merge[line_col_box].astype(str).str.strip()
            df_prog_merge[batch_col] = df_prog_merge[batch_col].astype(str).str.strip()

            # ล้างแถวขยะ
            for _c in [line_col_box, batch_col]:
                df_prog_merge = df_prog_merge[
                    ~df_prog_merge[_c].isin(['0', 'nan', '', 'None', 'null'])
                ]

            # 2. เตรียม plan_target — join ด้วย Line + Batch (plan sheet มีทั้งคู่)
            if target_box_col in df_plan.columns and plan_batch_col in df_plan.columns:
                df_plan_map = df_plan.copy()
                df_plan_map[target_box_col] = pd.to_numeric(
                    df_plan_map[target_box_col], errors='coerce'
                ).fillna(0)
                df_plan_map[plan_batch_col] = (
                    df_plan_map[plan_batch_col]
                    .astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                )

                # ตรวจว่า plan มีคอลัมน์ line ไหม (จากรูปมีชื่อ 'line' ตัวเล็ก)
                plan_line_col = next(
                    (c for c in ['Line', 'line', 'LINE'] if c in df_plan_map.columns), None
                )

                if plan_line_col:
                    # ✅ join ด้วย Line + Batch → แม่นยำที่สุด
                    df_plan_map[plan_line_col] = (
                        df_plan_map[plan_line_col].astype(str).str.strip()
                    )
                    df_target_map = (
                        df_plan_map
                        .groupby([plan_line_col, plan_batch_col])[target_box_col]
                        .first()  # 1 Batch = 1 แถว unique → ใช้ first() ตรงๆ
                        .reset_index()
                        .rename(columns={
                            plan_line_col: line_col_box,
                            plan_batch_col: batch_col,
                            target_box_col: 'Target_Boxes'
                        })
                    )
                    df_prog_merge = df_prog_merge.merge(
                        df_target_map, on=[line_col_box, batch_col], how='left'
                    )
                else:
                    # fallback: join ด้วย Batch เท่านั้น
                    plan_dict = (
                        df_plan_map
                        .groupby(plan_batch_col)[target_box_col]
                        .first()
                        .to_dict()
                    )
                    df_prog_merge['Target_Boxes'] = df_prog_merge[batch_col].map(plan_dict)

                df_prog_merge['Target_Boxes'] = df_prog_merge['Target_Boxes'].fillna(0)
            else:
                df_prog_merge['Target_Boxes'] = 0

            # 3. คำนวณ % (ป้องกันหารศูนย์)
            df_prog_merge['Progress_Percent'] = df_prog_merge.apply(
                lambda r: round(r['Good_Boxes'] / r['Target_Boxes'] * 100, 2)
                if r['Target_Boxes'] > 0 else 0.0,
                axis=1
            )

            df_prog_merge = df_prog_merge.sort_values([line_col_box, batch_col])
            df_prog_merge['X_Axis_Label'] = (
                    "Line " + df_prog_merge[line_col_box]
                    + "<br>(" + df_prog_merge[batch_col] + ")"
            )

            # 4. อัปเดต total_target_box ให้ตรงกับสิ่งที่แสดงในกราฟ
            total_target_box = df_prog_merge['Target_Boxes'].sum()
            # (อัปเดต metric m1 ด้วย — ต้องประกาศ m1 ก่อนบรรทัดนี้)

            if not df_prog_merge.empty:
                fig_prog = go.Figure(data=[
                    go.Bar(
                        x=df_prog_merge['X_Axis_Label'],
                        y=df_prog_merge['Progress_Percent'],
                        text=df_prog_merge['Progress_Percent'].map('{:,.1f}%'.format),
                        textposition='outside',
                        marker_color='#2ecc71',
                        customdata=df_prog_merge[['Good_Boxes', 'Target_Boxes']],
                        hovertemplate=(
                            "<b>%{x}</b><br>"
                            "AF (ผลิตสำเร็จ): %{customdata[0]:,.0f} กล่อง<br>"
                            "Need AF Box (เป้า): %{customdata[1]:,.0f} กล่อง<br>"
                            "Progress: %{y:.1f}%<extra></extra>"
                        )
                    )
                ])
                fig_prog.update_layout(
                    height=380,
                    margin=dict(t=30, b=50, l=10, r=10),
                    plot_bgcolor='rgba(0,0,0,0)',
                    yaxis=dict(
                        title="เปอร์เซ็นต์ความสำเร็จ (%)",
                        ticksuffix="%",
                        range=[0, max(df_prog_merge['Progress_Percent'].max() * 1.2, 110)]
                    )
                )
                st.plotly_chart(fig_prog, use_container_width=True)
            else:
                st.info("💡 ไม่มีข้อมูลรายงานความคืบหน้าในรอบเวลานี้")

        st.write("---")

        # --- แถวสอง: ตารางวิเคราะห์ Matrix ---
        mx_col1, mx_col2 = st.columns([3, 1])
        with mx_col1:
            st.markdown("#### 📦 2. Box Status Matrix (สถิติจำนวนกล่องเรียงสไตล์รูปที่ 3)")
        with mx_col2:
            if status_col in df_box_filtered.columns and line_col_box in df_box_filtered.columns and not df_box_filtered.empty:
                try:
                    df_matrix_prep = df_box_filtered.copy()
                    df_matrix_prep[status_col] = df_matrix_prep[status_col].astype(str).str.strip().str.upper()
                    df_matrix_prep[line_col_box] = df_matrix_prep[line_col_box].astype(str).str.strip()

                    raw_matrix = df_matrix_prep.pivot_table(index=status_col, columns=line_col_box, aggfunc='size',
                                                            fill_value=0)
                    clean_box_status = [str(st_item).strip().upper() for st_item in BOX_STATUS]
                    export_matrix = raw_matrix.reindex(clean_box_status).fillna(0).astype(int)
                    create_excel_download_button(export_matrix, "Matrix Table", "Box_Status_Matrix")
                except:
                    pass

        if status_col in df_box_filtered.columns and line_col_box in df_box_filtered.columns and not df_box_filtered.empty:
            try:
                df_matrix_prep = df_box_filtered.copy()
                df_matrix_prep[status_col] = df_matrix_prep[status_col].astype(str).str.strip().str.upper()
                df_matrix_prep[line_col_box] = df_matrix_prep[line_col_box].astype(str).str.strip()

                matrix = df_matrix_prep.pivot_table(index=status_col, columns=line_col_box, aggfunc='size',
                                                    fill_value=0)
                clean_box_status = [str(st_item).strip().upper() for st_item in BOX_STATUS]
                valid_idx = [idx for idx in clean_box_status if idx in matrix.index]

                if valid_idx:
                    matrix = matrix.reindex(valid_idx).fillna(0).astype(int)
                else:
                    matrix = matrix.fillna(0).astype(int)

                st.dataframe(
                    matrix.style.applymap(
                        lambda x: 'color: #0F172A; font-weight: bold;' if x > 0 else 'color: #94A3B8;')
                    .background_gradient(cmap='Blues', axis=1).format("{:,}"),
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"⚠️ ไม่สามารถขึ้นรูปตารางดัชนีระบุเกรดได้: {e}")
        else:
            st.info("💡 ไม่มีข้อมูล Box Status ในช่วงเวลาที่เลือก")

        # =========================================================
        # 📑 TAB 12: CAMERA ANALYSIS
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

                    items = entry.split(",")
                    for i in items:
                        i = i.strip()
                        if not i or i.lower() in ['nan', 'none', 'null', '0', '0.0', '-', '']:
                            continue

                        # รูปแบบ: "Bubble(5)" หรือ "Mashed(11)"
                        if "(" in i and ")" in i:
                            try:
                                name = i[:i.index("(")].strip()
                                count_str = i[i.index("(") + 1: i.index(")")].strip()
                                count = int(count_str) if count_str.isdigit() else 1
                            except Exception:
                                name = i.strip()
                                count = 1

                        # รูปแบบ: "5)" ← เศษหางที่หลุดจากการ split เช่น "Bubble(5),Mashed(11)"
                        elif i.endswith(")") and "(" not in i:
                            continue  # ข้ามเศษหางทันที

                        # รูปแบบ: ชื่อเปล่าๆ ไม่มีวงเล็บ
                        else:
                            name = i.strip()
                            count = 1

                        # Validate ชื่อ — ต้องมีตัวอักษรอย่างน้อย 1 ตัว
                        if not name:
                            continue
                        if not any(c.isalpha() for c in name):
                            continue
                        if name.lower() in ['nan', 'none', 'null', '0', '0.0', '-']:
                            continue

                        def_counts[name] = def_counts.get(name, 0) + count

                if def_counts:
                    df_def_plot = pd.DataFrame(list(def_counts.items()), columns=['Defect', 'Qty'])
                    df_def_plot = df_def_plot[df_def_plot['Qty'] > 0].sort_values('Qty', ascending=False)

                    if not df_def_plot.empty:
                        fig_def = px.pie(
                            df_def_plot, values='Qty', names='Defect', hole=0.4,
                            color_discrete_sequence=px.colors.qualitative.Pastel
                        )
                        fig_def.update_traces(
                            textposition='inside',
                            textinfo='percent+label'
                        )
                        fig_def.update_layout(height=380, margin=dict(t=10, b=10, l=10, r=10))
                        st.plotly_chart(fig_def, use_container_width=True)
                    else:
                        st.info("🟢 กล้องวิชั่นทำงานเสถียร! ไม่มีรายการของเสียในช่วงเวลานี้")
                else:
                    st.info("🟢 กล้องวิชั่นทำงานเสถียร! ยังไม่มีรายการประวัติของเสียในช่วงนี้")
            else:
                st.info("💡 ไม่มีข้อมูลบันทึกในช่วงเวลาที่เลือก")

            st.write("---")

            tx_col1, tx_col2 = st.columns([3, 1])
            with tx_col1:
                st.markdown("#### 📷 2. Camera Performance Summary Table (สรุปรายไลน์)")
            with tx_col2:
                if not df_camera_filtered.empty and 'Line' in df_camera_filtered.columns:
                    try:
                        excel_cam = df_camera_filtered.groupby('Line').agg({
                            'Cam1_Pass_Rate': 'mean',
                            'Cam2_Pass_Rate': 'mean'
                        })
                        create_excel_download_button(excel_cam, "Camera Performance Table", "Camera_Performance")
                    except Exception:
                        pass

            if not df_camera_filtered.empty and 'Line' in df_camera_filtered.columns:
                df_cam_calc = df_camera_filtered.copy()
                df_cam_calc['Cam1_Pass_Rate'] = pd.to_numeric(
                    df_cam_calc['Cam1_Pass_Rate'], errors='coerce'
                ).fillna(100.0)
                df_cam_calc['Cam2_Pass_Rate'] = pd.to_numeric(
                    df_cam_calc['Cam2_Pass_Rate'], errors='coerce'
                ).fillna(100.0)

                cam_summary = df_cam_calc.groupby('Line').agg(
                    Cam1_Avg_Pass=('Cam1_Pass_Rate', 'mean'),
                    Cam2_Avg_Pass=('Cam2_Pass_Rate', 'mean'),
                    Recent_Defects=('Cam1_Defects', lambda x: ", ".join(
                        sorted(set(
                            str(v).strip() for v in x
                            if str(v).strip() not in ['', 'nan', 'None', '0', '0.0', 'null', '-']
                        ))
                    )[:80] + "..." if any(
                        str(v).strip() not in ['', 'nan', 'None', '0', '0.0', 'null', '-']
                        for v in x
                    ) else "-")
                ).reset_index()

                cam_summary.columns = [
                    'Line',
                    'Camera 1 Avg Pass Rate (%)',
                    'Camera 2 Avg Pass Rate (%)',
                    'Recent Detected Defects'
                ]

                st.dataframe(
                    cam_summary.style.format({
                        'Camera 1 Avg Pass Rate (%)': '{:.2f}%',
                        'Camera 2 Avg Pass Rate (%)': '{:.2f}%',
                    }),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("💡 ไม่พบโครงสร้างตารางข้อมูลเพื่อคำนวณ")

    # =========================================================
    # 📑 TAB 13: RE-PASS
    # =========================================================
    with t3:
        st.markdown("### 🔍 ตัวกรองประวัติการแก้ไขงานทำซ้ำ (Re-pass Filter)")
        df_repass_filtered, _ = render_filter_widgets(df_repass, "t3_repass")
        st.write("---")

        st.markdown("##### 📍 แผนภูมิปริมาณความถี่การส่งงาน Re-pass แยกราย Line")
        if not df_repass_filtered.empty and 'Line' in df_repass_filtered.columns:
            repass_counts = df_repass_filtered.groupby('Line').size().reset_index(name='Counts')
            fig_re = px.bar(repass_counts, x='Line', y='Counts', text='Counts', color='Counts',
                            color_continuous_scale='Reds')
            fig_re.update_traces(textposition='outside')
            fig_re.update_layout(plot_bgcolor='rgba(0,0,0,0)', height=320)
            st.plotly_chart(fig_re, use_container_width=True)
        else:
            st.info("🔄 สภาพแวดล้อมปกติ ไม่มีข้อมูลประวัติการส่งชิ้นงาน Re-pass")

        st.write("---")

        st.markdown("##### 🏁 ผลลัพธ์สุดท้ายหลังเสร็จสิ้นกระบวนการ Re-pass (Result Status)")
        if not df_repass_filtered.empty and 'Result_Status' in df_repass_filtered.columns:
            res_counts = df_repass_filtered.groupby('Result_Status').size().reset_index(name='Qty')
            fig_res = px.pie(res_counts, values='Qty', names='Result_Status', color='Result_Status',
                             color_discrete_map=STATUS_COLORS, hole=0.3)
            fig_res.update_layout(height=340, margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig_res, use_container_width=True)
        else:
            st.info("💡 รอการรายงานสรุปผลประเมินเกรดชิ้นงานซ่อมแซม")

        st.write("---")

        st.markdown(
            "##### 📋 รายการชิ้นงานที่อยู่ระหว่างรอการ Re-pass และตรวจสอบซ้ำ (ดึงข้อมูลโครงสร้างเรียลไทม์ตามชีต box_status)")

        if status_col in df_box.columns and not df_box.empty:
            df_pending_box = df_box[df_box[status_col].astype(str).str.strip().str.upper() != 'AF']

            if not df_pending_box.empty:
                st.dataframe(df_pending_box, use_container_width=True, hide_index=True)
                st.caption(
                    f"⚠️ ตรวจพบจำนวนกล่องงานคงค้างรอการ Re-pass ทั้งสิ้น: {len(df_pending_box):,} กล่อง ประจำช่วงเวลา")
            else:
                st.success(
                    "🟢 ยอดเยี่ยม! ข้อมูลในระบบฐานข้อมูลหลักเปลี่ยนรูปกลับมาเป็นเกรดดีผ่านเกณฑ์ (AF) เรียบร้อยครบถ้วน ไม่มีรายการงานค้างสะสม")
        else:
            st.info("💡 ไม่มีประวัติข้อมูลกล่องสถานะคงเหลือรอรับรอบตรวจสอบซ้ำในช่วงเวลานี้")

    st.caption(
        f"📊 ระบบประมวลผลและกระจายชุดข้อมูลข้อมูลอัตโนมัติล่าสุดเมื่อ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

