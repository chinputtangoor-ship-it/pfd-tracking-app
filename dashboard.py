import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io


def show_dashboard_page(load_csv):

    st.markdown("""
    <style>
    .kpi-card {
        background: linear-gradient(135deg, #1e2a3a 0%, #0f1923 100%);
        border: 1px solid #2d4a6e; border-radius: 12px;
        padding: 20px 24px; text-align: center; margin: 4px 0;
    }
    .kpi-label { font-size: 11px; font-weight: 600; letter-spacing: 1.5px;
        text-transform: uppercase; color: #7ab3d4; margin-bottom: 8px; }
    .kpi-value { font-size: 32px; font-weight: 800; line-height: 1; margin-bottom: 4px; }
    .kpi-sub   { font-size: 12px; color: #8899aa; }
    .kpi-green  { color: #00d4aa; } .kpi-red { color: #ff4757; }
    .kpi-yellow { color: #ffa502; } .kpi-blue { color: #54a0ff; }
    .kpi-white  { color: #ffffff; }
    .section-header { font-size: 15px; font-weight: 700; color: #54a0ff;
        border-left: 4px solid #54a0ff; padding-left: 12px;
        margin: 18px 0 12px 0; letter-spacing: 0.5px; }
    .line-card { background: #1a2332; border-radius: 10px;
        padding: 14px 16px; margin: 4px 0; border-left: 4px solid #2d4a6e; }
    .line-card-green  { border-left-color: #00d4aa; }
    .line-card-red    { border-left-color: #ff4757; }
    .line-card-yellow { border-left-color: #ffa502; }
    .line-card-gray   { border-left-color: #556677; }
    .filter-bar { background: #0f1923; border: 1px solid #2d4a6e;
        border-radius: 10px; padding: 12px 16px; margin-bottom: 16px; }
    .dashboard-title { font-size: 24px; font-weight: 800; color: #ffffff;
        letter-spacing: 1px; margin-bottom: 4px; }
    .dashboard-sub { font-size: 13px; color: #7ab3d4; margin-bottom: 8px; }
    </style>
    """, unsafe_allow_html=True)

    # ── โหลดข้อมูล ──────────────────────────────────────────────────────────
    df_plan    = load_csv("plan").fillna("")
    df_box     = load_csv("box_status").fillna("")
    df_backlog = load_csv("backlog").fillna(0)
    df_rej     = load_csv("rejection").fillna(0)
    df_camera  = load_csv("camera").fillna("")
    df_repass  = load_csv("re_pass").fillna("")

    from constants import STATUS_COLORS, LINES, BOX_STATUS

    def find_col(df, *candidates):
        lmap = {c.strip().lower(): c for c in df.columns}
        for cand in candidates:
            if cand.strip().lower() in lmap:
                return lmap[cand.strip().lower()]
        return None

    # ── detect columns ───────────────────────────────────────────────────────
    box_line_col   = find_col(df_box, 'Line','line')
    box_batch_col  = find_col(df_box, 'Batch','batch')
    box_status_col = find_col(df_box, 'Status','status')
    box_defect_col = find_col(df_box, 'Defects','defects')
    box_box_col    = find_col(df_box, 'Box','box')
    box_time_col   = find_col(df_box, 'Time','time')

    plan_line_col   = find_col(df_plan, 'Line','line')
    plan_batch_col  = find_col(df_plan, 'Batch','batch')
    plan_target_col = find_col(df_plan, 'Need af box','need af box','Need AF Box','need_af_box')
    plan_status_col = find_col(df_plan, 'Batch status','batch status','batch_status')

    rej_line_col = find_col(df_rej, 'Line','line')
    rej_ats_col  = find_col(df_rej, 'ATS_kg','ats_kg')
    rej_prt_col  = find_col(df_rej, 'Print_kg','print_kg')
    rej_cam_col  = find_col(df_rej, 'Cam_kg','cam_kg')

    bl_line_col  = find_col(df_backlog, 'Line','line')
    bl_total_col = find_col(df_backlog, 'Total_caps','total_caps')

    rp_line_col   = find_col(df_repass, 'Line','line')
    rp_result_col = find_col(df_repass, 'Result_Status','result_status')
    rp_prev_col   = find_col(df_repass, 'Previous_Status','previous_status')
    rp_time_col   = find_col(df_repass, 'Time','time')

    cam_line_col = find_col(df_camera, 'Line','line')
    cam_time_col = find_col(df_camera, 'Time','time')

    # ── cleansing batch ──────────────────────────────────────────────────────
    if box_batch_col:
        df_box[box_batch_col] = df_box[box_batch_col].astype(str).str.replace(r'\.0$','',regex=True).str.strip()
    if plan_batch_col:
        df_plan[plan_batch_col] = df_plan[plan_batch_col].astype(str).str.replace(r'\.0$','',regex=True).str.strip()

    # ── parse datetime สำหรับ filter ────────────────────────────────────────
    if box_time_col and not df_box.empty:
        df_box[box_time_col] = pd.to_datetime(df_box[box_time_col], errors='coerce')
    if rp_time_col and not df_repass.empty:
        df_repass[rp_time_col] = pd.to_datetime(df_repass[rp_time_col], errors='coerce')
    if cam_time_col and not df_camera.empty:
        df_camera[cam_time_col] = pd.to_datetime(df_camera[cam_time_col], errors='coerce')
    rej_time_col = find_col(df_rej, 'Time','time')
    if rej_time_col and not df_rej.empty:
        df_rej[rej_time_col] = pd.to_datetime(df_rej[rej_time_col], errors='coerce')

    # ════════════════════════════════════════════════════════════════════════
    # GLOBAL FILTER BAR
    # ════════════════════════════════════════════════════════════════════════
    now_str = datetime.now().strftime("%d %b %Y  %H:%M")
    st.markdown(f"""
    <div class='dashboard-title'>📈 Executive Production Dashboard</div>
    <div class='dashboard-sub'>Monitoring 13 สายการผลิต  ·  อัปเดตล่าสุด: {now_str}</div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='filter-bar'>", unsafe_allow_html=True)
    fc1, fc2, fc3 = st.columns([1, 1, 2])

    with fc1:
        line_opts    = ["ทั้งหมด"] + sorted(df_box[box_line_col].dropna().unique().tolist()) if box_line_col and not df_box.empty else ["ทั้งหมด"]
        filter_line  = st.selectbox("🏭 สายการผลิต (Line)", line_opts, key="gf_line")

    with fc2:
        period_opts  = ["ทั้งหมด", "วันนี้", "7 วันล่าสุด", "30 วันล่าสุด", "กำหนดเอง"]
        filter_period = st.selectbox("📅 ช่วงเวลา", period_opts, key="gf_period")

    with fc3:
        filter_dates = None
        if filter_period == "กำหนดเอง":
            min_d = (df_box[box_time_col].dropna().min().date()
                     if box_time_col and not df_box.empty and not df_box[box_time_col].dropna().empty
                     else datetime.now().date() - timedelta(days=30))
            max_d = datetime.now().date()
            filter_dates = st.date_input("🗓️ เลือกช่วงวันที่", [min_d, max_d], key="gf_dates")
        else:
            st.markdown(f"<div style='padding-top:28px;color:#7ab3d4;font-size:13px;'>⚡ โหมด: <b>{filter_period}</b></div>",
                        unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # ── helper: apply global filter ─────────────────────────────────────────
    def apply_filter(df, time_col, line_col):
        df_f = df.copy()

        # filter line
        if line_col and filter_line != "ทั้งหมด":
            df_f = df_f[df_f[line_col].astype(str).str.strip() == filter_line]

        # filter time
        if time_col and time_col in df_f.columns and not df_f.empty:
            now = datetime.now()
            if filter_period == "วันนี้":
                cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
                df_f   = df_f[df_f[time_col] >= cutoff]
            elif filter_period == "7 วันล่าสุด":
                df_f   = df_f[df_f[time_col] >= now - timedelta(days=7)]
            elif filter_period == "30 วันล่าสุด":
                df_f   = df_f[df_f[time_col] >= now - timedelta(days=30)]
            elif filter_period == "กำหนดเอง" and filter_dates and len(filter_dates) == 2:
                st_dt  = pd.to_datetime(filter_dates[0]).replace(hour=0,  minute=0,  second=0)
                en_dt  = pd.to_datetime(filter_dates[1]).replace(hour=23, minute=59, second=59)
                df_f   = df_f[(df_f[time_col] >= st_dt) & (df_f[time_col] <= en_dt)]
        return df_f

    # ── apply filter to all sheets ──────────────────────────────────────────
    df_box_f    = apply_filter(df_box,     box_time_col,  box_line_col)
    df_rej_f    = apply_filter(df_rej,     rej_time_col,  rej_line_col)
    df_camera_f = apply_filter(df_camera,  cam_time_col,  cam_line_col)
    df_repass_f = apply_filter(df_repass,  rp_time_col,   rp_line_col)

    # plan ไม่มี time → filter แค่ line
    df_plan_f = df_plan.copy()
    if plan_line_col and filter_line != "ทั้งหมด":
        df_plan_f = df_plan_f[df_plan_f[plan_line_col].astype(str).str.strip() == filter_line]

    # backlog → filter line เท่านั้น (ไม่มี time filter ที่ตรงกับ global)
    df_backlog_f = df_backlog.copy()
    if bl_line_col and filter_line != "ทั้งหมด":
        df_backlog_f = df_backlog_f[df_backlog_f[bl_line_col].astype(str).str.strip() == filter_line]

    # แสดง filter summary
    n_box = len(df_box_f)
    st.caption(f"🔍 กรองแล้ว — Box Status: {n_box:,} รายการ  |  Line: {filter_line}  |  ช่วงเวลา: {filter_period}")

    # ── running plan ─────────────────────────────────────────────────────────
    running_plan = pd.DataFrame()
    if plan_status_col and not df_plan_f.empty:
        running_plan = df_plan_f[df_plan_f[plan_status_col].astype(str).str.strip().str.lower() != 'finished']

    # ── KPI รวม (คำนวณจากข้อมูลที่ filter แล้ว) ─────────────────────────────
    total_target = 0
    if plan_target_col and not running_plan.empty:
        total_target = pd.to_numeric(running_plan[plan_target_col], errors='coerce').fillna(0).sum()

    total_af = 0
    if box_status_col and not df_box_f.empty:
        total_af = (df_box_f[box_status_col].astype(str).str.upper().str.strip() == 'AF').sum()

    yield_pct = round(total_af / total_target * 100, 1) if total_target > 0 else 0.0

    active_lines_count = df_box_f[box_line_col].nunique() if box_line_col and not df_box_f.empty else 0

    total_non_af = (df_box_f[box_status_col].astype(str).str.upper().str.strip() != 'AF').sum() if box_status_col and not df_box_f.empty else 0
    total_boxes  = total_af + total_non_af
    scrap_pct    = round(total_non_af / total_boxes * 100, 1) if total_boxes > 0 else 0.0

    total_backlog = 0
    if bl_total_col and not df_backlog_f.empty:
        total_backlog = int(pd.to_numeric(df_backlog_f[bl_total_col], errors='coerce').iloc[-1])

    total_repass = len(df_repass_f)

    # ── Excel helper ──────────────────────────────────────────────────────────
    def excel_btn(df_exp, label, fname):
        try:
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine='openpyxl') as w:
                df_exp.to_excel(w, index=True, sheet_name='Report')
            buf.seek(0)
            st.download_button(f"📥 Export {label}", buf,
                               f"{fname}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        except Exception:
            try:
                csv_buf = io.StringIO()
                df_exp.to_csv(csv_buf)
                st.download_button(f"📥 Export {label} (CSV)",
                                   csv_buf.getvalue().encode('utf-8-sig'),
                                   f"{fname}_{datetime.now().strftime('%Y%m%d')}.csv",
                                   mime="text/csv")
            except Exception as e2:
                st.warning(f"⚠️ Export ไม่ได้: {e2}")

    # ════════════════════════════════════════════════════════════════════════
    # 3 TABS
    # ════════════════════════════════════════════════════════════════════════
    tab1, tab2, tab3 = st.tabs([
        "📊 Overview & Progress",
        "🔬 Quality Analysis",
        "📋 Detail & Pending"
    ])

    # ════════════════════════════════════════════════════════════════════════
    # TAB 1
    # ════════════════════════════════════════════════════════════════════════
    with tab1:
        st.markdown("<div class='section-header'>Q1 — Executive KPIs  |  ภาพรวมสายการผลิต</div>",
                    unsafe_allow_html=True)

        yield_color = "kpi-green"  if yield_pct >= 90 else ("kpi-yellow" if yield_pct >= 70 else "kpi-red")
        scrap_color = "kpi-green"  if scrap_pct <= 2  else ("kpi-yellow" if scrap_pct <= 5  else "kpi-red")
        bl_color    = "kpi-green"  if total_backlog == 0 else ("kpi-yellow" if total_backlog <= 5 else "kpi-red")

        k1,k2,k3,k4,k5,k6 = st.columns(6)
        k1.markdown(f"""<div class='kpi-card'><div class='kpi-label'>Yield Rate</div>
            <div class='kpi-value {yield_color}'>{yield_pct:.1f}%</div>
            <div class='kpi-sub'>AF / Target</div></div>""", unsafe_allow_html=True)
        k2.markdown(f"""<div class='kpi-card'><div class='kpi-label'>Good Boxes (AF)</div>
            <div class='kpi-value kpi-green'>{total_af:,}</div>
            <div class='kpi-sub'>จาก {total_target:,.0f} เป้า</div></div>""", unsafe_allow_html=True)
        k3.markdown(f"""<div class='kpi-card'><div class='kpi-label'>Scrap Rate</div>
            <div class='kpi-value {scrap_color}'>{scrap_pct:.1f}%</div>
            <div class='kpi-sub'>{total_non_af:,} กล่องไม่ผ่าน</div></div>""", unsafe_allow_html=True)
        k4.markdown(f"""<div class='kpi-card'><div class='kpi-label'>Active Lines</div>
            <div class='kpi-value kpi-blue'>{active_lines_count}/13</div>
            <div class='kpi-sub'>สายที่มีข้อมูล</div></div>""", unsafe_allow_html=True)
        k5.markdown(f"""<div class='kpi-card'><div class='kpi-label'>Backlog (caps)</div>
            <div class='kpi-value {bl_color}'>{total_backlog:,}</div>
            <div class='kpi-sub'>งานค้างสะสม</div></div>""", unsafe_allow_html=True)
        k6.markdown(f"""<div class='kpi-card'><div class='kpi-label'>Re-pass Total</div>
            <div class='kpi-value kpi-yellow'>{total_repass:,}</div>
            <div class='kpi-sub'>ชิ้นงานส่งซ่อม</div></div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div class='section-header'>Q2 — Real-time Line Status Matrix  &  Production Progress</div>",
                    unsafe_allow_html=True)

        col_matrix, col_prog = st.columns([1, 1.6])

        with col_matrix:
            st.markdown("##### 🟢 สถานะ 13 สายการผลิต")
            line_stats = {}
            if box_line_col and box_status_col and not df_box_f.empty:
                for ln in df_box_f[box_line_col].unique():
                    ln_df   = df_box_f[df_box_f[box_line_col] == ln]
                    n_af    = (ln_df[box_status_col].astype(str).str.upper().str.strip() == 'AF').sum()
                    n_total = len(ln_df)
                    scr_r   = round((n_total-n_af)/n_total*100,1) if n_total>0 else 0.0
                    batch_str = ""
                    if box_batch_col:
                        batches   = ln_df[box_batch_col].unique()
                        batch_str = ", ".join([b for b in batches if b and b not in ['nan','0','']])
                    line_stats[str(ln).strip()] = {'af':n_af,'total':n_total,'scrap_pct':scr_r,'batch':batch_str}

            all_lines = [f"H5{str(i).zfill(2)}" for i in range(1,14)]
            cols_g    = st.columns(3)
            for i, ln in enumerate(all_lines):
                stat = line_stats.get(ln, None)
                if stat is None:
                    cc, st_txt = "line-card line-card-gray","ไม่มีข้อมูล"
                    val_html   = "<span style='color:#556677;'>—</span>"
                elif stat['scrap_pct'] > 10:
                    cc, st_txt = "line-card line-card-red", f"⚠️ {stat['scrap_pct']:.1f}%"
                    val_html   = f"<span style='color:#ff4757;font-weight:700;'>{stat['af']}/{stat['total']}</span>"
                elif stat['scrap_pct'] > 3:
                    cc, st_txt = "line-card line-card-yellow", f"⚡ {stat['scrap_pct']:.1f}%"
                    val_html   = f"<span style='color:#ffa502;font-weight:700;'>{stat['af']}/{stat['total']}</span>"
                else:
                    cc, st_txt = "line-card line-card-green", f"✅ {stat['scrap_pct']:.1f}%"
                    val_html   = f"<span style='color:#00d4aa;font-weight:700;'>{stat['af']}/{stat['total']}</span>"

                batch_info = f"<div style='font-size:10px;color:#667788;margin-top:2px;'>{stat['batch'][:18] if stat else ''}</div>" if stat else ""
                cols_g[i%3].markdown(f"""<div class='{cc}'>
                    <div style='font-size:13px;font-weight:700;color:#cdd9e5;'>{ln}</div>
                    <div style='font-size:11px;margin:3px 0;'>AF: {val_html}</div>
                    <div style='font-size:10px;color:#8899aa;'>{st_txt}</div>{batch_info}
                </div>""", unsafe_allow_html=True)

        with col_prog:
            st.markdown("##### 📊 Production Progress % by Line & Batch")
            if box_status_col and box_line_col and box_batch_col and not df_box_f.empty and plan_target_col and plan_batch_col:
                df_af_only = df_box_f[df_box_f[box_status_col].astype(str).str.upper().str.strip()=='AF']
                df_prog    = df_af_only.groupby([box_line_col,box_batch_col]).size().reset_index(name='Good_Boxes')
                df_plan_m  = df_plan.copy()
                df_plan_m[plan_target_col] = pd.to_numeric(df_plan_m[plan_target_col], errors='coerce').fillna(0)

                if plan_line_col:
                    df_tgt = (df_plan_m.groupby([plan_line_col,plan_batch_col])[plan_target_col]
                              .first().reset_index()
                              .rename(columns={plan_line_col:box_line_col, plan_batch_col:box_batch_col,
                                               plan_target_col:'Target'}))
                    df_prog = df_prog.merge(df_tgt, on=[box_line_col,box_batch_col], how='left')
                else:
                    tgt_d = df_plan_m.groupby(plan_batch_col)[plan_target_col].first().to_dict()
                    df_prog['Target'] = df_prog[box_batch_col].map(tgt_d)

                df_prog['Target'] = df_prog['Target'].fillna(0)
                df_prog['Pct']    = df_prog.apply(lambda r: round(r['Good_Boxes']/r['Target']*100,1) if r['Target']>0 else 0.0, axis=1)
                df_prog['Label']  = df_prog[box_line_col] + "<br>(" + df_prog[box_batch_col].str[-6:] + ")"
                df_prog['Color']  = df_prog['Pct'].apply(lambda x: '#00d4aa' if x>=90 else ('#ffa502' if x>=60 else '#ff4757'))
                df_prog = df_prog.sort_values([box_line_col,box_batch_col])

                if not df_prog.empty:
                    fig_p = go.Figure(go.Bar(
                        x=df_prog['Label'], y=df_prog['Pct'],
                        text=df_prog['Pct'].map('{:.1f}%'.format), textposition='outside',
                        marker_color=df_prog['Color'],
                        customdata=df_prog[['Good_Boxes','Target']],
                        hovertemplate="<b>%{x}</b><br>AF: %{customdata[0]:,}<br>Target: %{customdata[1]:,}<br>%{y:.1f}%<extra></extra>"
                    ))
                    fig_p.add_hline(y=90, line_dash="dash", line_color="#ffa502",
                                    annotation_text="Target 90%", annotation_font_color="#ffa502")
                    fig_p.update_layout(
                        height=380, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        font_color='#cdd9e5', margin=dict(t=30,b=10,l=10,r=10),
                        yaxis=dict(ticksuffix='%', range=[0,max(df_prog['Pct'].max()*1.25,110)], gridcolor='#1e2a3a'),
                        xaxis=dict(gridcolor='#1e2a3a')
                    )
                    st.plotly_chart(fig_p, use_container_width=True)
                else:
                    st.info("💡 ไม่มีข้อมูล AF")
            else:
                st.info("💡 ไม่มีข้อมูลเพียงพอ")

    # ════════════════════════════════════════════════════════════════════════
    # TAB 2
    # ════════════════════════════════════════════════════════════════════════
    with tab2:
        st.markdown("<div class='section-header'>Q3 — Scrap Pareto  &  Camera Performance</div>",
                    unsafe_allow_html=True)

        col_q3, col_cam = st.columns([1, 1])

        with col_q3:
            st.markdown("##### 🔴 Scrap / Defect Pareto (box_status)")
            defect_counts = {}
            if box_status_col and box_defect_col and not df_box_f.empty:
                df_rej_box = df_box_f[df_box_f[box_status_col].astype(str).str.upper().str.strip()!='AF']
                for val in df_rej_box[box_defect_col].astype(str):
                    for d in val.split(","):
                        d = d.strip()
                        if d and d.lower() not in ['nan','none','','0','-']:
                            defect_counts[d] = defect_counts.get(d,0) + 1

            if defect_counts:
                df_pareto = (pd.DataFrame(list(defect_counts.items()), columns=['Defect','Count'])
                             .query('Count>0').sort_values('Count',ascending=False).head(10))
                total_d             = df_pareto['Count'].sum()
                df_pareto['Pct']    = df_pareto['Count']/total_d*100
                df_pareto['CumPct'] = df_pareto['Pct'].cumsum()
                bar_colors = ['#ff4757' if i==0 else '#ff6b81' if i==1 else '#ffa502' if i<4 else '#54a0ff'
                              for i in range(len(df_pareto))]

                fig_par = go.Figure()
                fig_par.add_trace(go.Bar(x=df_pareto['Defect'], y=df_pareto['Count'],
                    marker_color=bar_colors, name='จำนวน',
                    text=df_pareto['Count'], textposition='outside',
                    customdata=df_pareto['Pct'],
                    hovertemplate="<b>%{x}</b><br>%{y} ครั้ง (%{customdata:.1f}%)<extra></extra>"))
                fig_par.add_trace(go.Scatter(x=df_pareto['Defect'], y=df_pareto['CumPct'],
                    mode='lines+markers', name='Cumulative %',
                    line=dict(color='#00d4aa',width=2), marker=dict(size=6), yaxis='y2'))
                fig_par.add_hline(y=80, line_dash="dash", line_color="#ffa502",
                                  yref='y2', annotation_text="80%", annotation_font_color="#ffa502")
                fig_par.update_layout(
                    height=340, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font_color='#cdd9e5', margin=dict(t=30,b=10,l=10,r=10),
                    legend=dict(bgcolor='rgba(0,0,0,0)', font_size=10, orientation='h', y=1.12),
                    yaxis=dict(title='จำนวน', gridcolor='#1e2a3a'),
                    yaxis2=dict(title='Cumulative %', overlaying='y', side='right',
                                range=[0,110], ticksuffix='%'))
                st.plotly_chart(fig_par, use_container_width=True)

                top3 = df_pareto.head(3)
                cols_t = st.columns(3)
                for i,(_, row) in enumerate(top3.iterrows()):
                    clr = ["#ff4757","#ffa502","#54a0ff"][i]
                    cols_t[i].markdown(f"""<div class='kpi-card' style='border-color:{clr}40;'>
                        <div style='font-size:20px;font-weight:900;color:{clr};'>#{i+1}</div>
                        <div style='font-size:13px;font-weight:700;color:#cdd9e5;margin:4px 0;'>{row['Defect']}</div>
                        <div style='font-size:11px;color:#8899aa;'>{int(row['Count'])} ครั้ง ({row['Pct']:.1f}%)</div>
                    </div>""", unsafe_allow_html=True)
            else:
                st.success("🟢 ไม่พบ Defect")

        with col_cam:
            st.markdown("##### 📷 Camera Performance by Line")
            if not df_camera_f.empty and cam_line_col:
                df_cam = df_camera_f.copy()
                c1_pass = find_col(df_cam,'Cam1_Pass_Rate','cam1_pass_rate')
                c2_pass = find_col(df_cam,'Cam2_Pass_Rate','cam2_pass_rate')
                c1_rej  = find_col(df_cam,'Cam1_Total_Qty','cam1_total_qty')
                c2_rej  = find_col(df_cam,'Cam2_Total_Qty','cam2_total_qty')
                c1_def  = find_col(df_cam,'Cam1_Defects','cam1_defects')
                c2_def  = find_col(df_cam,'Cam2_Defects','cam2_defects')

                for c in [c1_pass,c2_pass]:
                    if c: df_cam[c] = pd.to_numeric(df_cam[c], errors='coerce').fillna(100)
                for c in [c1_rej,c2_rej]:
                    if c: df_cam[c] = pd.to_numeric(df_cam[c], errors='coerce').fillna(0)

                def parse_defects(series):
                    counts = {}
                    for val in series.astype(str):
                        for item in val.split(","):
                            item = item.strip()
                            if not item or item.lower() in ['nan','none','null','0','0.0','-','']: continue
                            if "(" in item and ")" in item:
                                try:
                                    name = item[:item.index("(")].strip()
                                    cnt  = int(item[item.index("(")+1:item.index(")")].strip())
                                    if name and any(c.isalpha() for c in name):
                                        counts[name] = counts.get(name,0)+cnt
                                except Exception: pass
                            elif item.endswith(")") and "(" not in item: continue
                            else:
                                if any(c.isalpha() for c in item):
                                    counts[item] = counts.get(item,0)+1
                    return counts

                cam_rows = []
                for ln in df_cam[cam_line_col].unique():
                    ln_cam = df_cam[df_cam[cam_line_col]==ln]
                    c1_avg = ln_cam[c1_pass].mean() if c1_pass else 100.0
                    c2_avg = ln_cam[c2_pass].mean() if c2_pass else 100.0
                    c1r    = ln_cam[c1_rej].sum()   if c1_rej else 0
                    c2r    = ln_cam[c2_rej].sum()   if c2_rej else 0
                    all_dc = {}
                    for dc in [c1_def,c2_def]:
                        if dc:
                            for k,v in parse_defects(ln_cam[dc]).items():
                                all_dc[k] = all_dc.get(k,0)+v
                    top_def = sorted(all_dc.items(), key=lambda x:-x[1])[:3]
                    top_str = ", ".join([f"{k}({v})" for k,v in top_def]) if top_def else "-"
                    cam_rows.append({'Line':str(ln),'Cam1 Pass%':round(c1_avg,2),'Cam2 Pass%':round(c2_avg,2),
                                     'Cam1 Rej':int(c1r),'Cam2 Rej':int(c2r),'Top Defects':top_str})

                df_cam_sum = pd.DataFrame(cam_rows)
                if not df_cam_sum.empty:
                    fig_cam = go.Figure()
                    fig_cam.add_trace(go.Bar(name='Cam1 Pass%', x=df_cam_sum['Line'], y=df_cam_sum['Cam1 Pass%'],
                        marker_color='#54a0ff', text=df_cam_sum['Cam1 Pass%'].map('{:.2f}%'.format), textposition='inside',
                        hovertemplate="<b>%{x}</b><br>Cam1: %{y:.2f}%<extra></extra>"))
                    fig_cam.add_trace(go.Bar(name='Cam2 Pass%', x=df_cam_sum['Line'], y=df_cam_sum['Cam2 Pass%'],
                        marker_color='#00d4aa', text=df_cam_sum['Cam2 Pass%'].map('{:.2f}%'.format), textposition='inside',
                        hovertemplate="<b>%{x}</b><br>Cam2: %{y:.2f}%<extra></extra>"))
                    fig_cam.add_hline(y=98, line_dash="dash", line_color="#ffa502",
                                      annotation_text="Target 98%", annotation_font_color="#ffa502")
                    fig_cam.update_layout(
                        barmode='group', height=280,
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        font_color='#cdd9e5', margin=dict(t=30,b=10,l=10,r=10),
                        legend=dict(bgcolor='rgba(0,0,0,0)', orientation='h', y=1.12, font_size=10),
                        yaxis=dict(ticksuffix='%', range=[0,105], gridcolor='#1e2a3a'),
                        xaxis=dict(gridcolor='#1e2a3a'))
                    st.plotly_chart(fig_cam, use_container_width=True)

                    all_defects_total = {}
                    for dc in [c1_def,c2_def]:
                        if dc:
                            for k,v in parse_defects(df_camera_f[dc]).items():
                                all_defects_total[k] = all_defects_total.get(k,0)+v
                    if all_defects_total:
                        df_cd = (pd.DataFrame(list(all_defects_total.items()), columns=['Defect','Count'])
                                 .sort_values('Count',ascending=True).tail(8))
                        fig_cd = px.bar(df_cd, x='Count', y='Defect', orientation='h', text='Count',
                                        color='Count', color_continuous_scale=[[0,'#1e6b4a'],[0.5,'#ffa502'],[1,'#ff4757']])
                        fig_cd.update_traces(textposition='outside')
                        fig_cd.update_layout(
                            height=250, title="Camera Defect รวม (Cam1+Cam2)",
                            title_font_color='#7ab3d4', title_font_size=12,
                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            font_color='#cdd9e5', margin=dict(t=40,b=10,l=10,r=10),
                            showlegend=False, coloraxis_showscale=False,
                            xaxis=dict(gridcolor='#1e2a3a'), yaxis=dict(gridcolor='#1e2a3a'))
                        st.plotly_chart(fig_cd, use_container_width=True)

                    with st.expander("📋 Camera Detail Table"):
                        def c_pass(v):
                            if v>=99: return 'color:#00d4aa;font-weight:bold'
                            if v>=95: return 'color:#ffa502;font-weight:bold'
                            return 'color:#ff4757;font-weight:bold'
                        styled_cam = (df_cam_sum.style.map(c_pass, subset=['Cam1 Pass%','Cam2 Pass%'])
                                      .format({'Cam1 Pass%':'{:.2f}%','Cam2 Pass%':'{:.2f}%'}))
                        st.dataframe(styled_cam, use_container_width=True, hide_index=True)
                        excel_btn(df_cam_sum.set_index('Line'), "Camera", "Camera_Performance")
            else:
                st.info("💡 ไม่มีข้อมูล Camera")

    # ════════════════════════════════════════════════════════════════════════
    # TAB 3
    # ════════════════════════════════════════════════════════════════════════
    with tab3:
        st.markdown("<div class='section-header'>📋 Detailed Line-by-Line Breakdown  &  Pending Work</div>",
                    unsafe_allow_html=True)

        col_tbl, col_side = st.columns([1.8, 1])

        with col_tbl:
            st.markdown("##### 📊 สรุปผลแต่ละสายการผลิต")
            rows = []
            if box_line_col and box_status_col and not df_box_f.empty:
                for ln in sorted(df_box_f[box_line_col].unique()):
                    ln_df   = df_box_f[df_box_f[box_line_col]==ln]
                    n_af    = (ln_df[box_status_col].astype(str).str.upper().str.strip()=='AF').sum()
                    n_tot   = len(ln_df)
                    n_scrap = n_tot - n_af
                    tgt     = 0
                    if plan_line_col and plan_batch_col and plan_target_col and not running_plan.empty:
                        ln_pl = running_plan[running_plan[plan_line_col].astype(str).str.strip()==str(ln).strip()]
                        if not ln_pl.empty:
                            tgt = pd.to_numeric(ln_pl[plan_target_col], errors='coerce').fillna(0).sum()
                    yld   = round(n_af/tgt*100,1)     if tgt>0   else 0.0
                    scr   = round(n_scrap/n_tot*100,1) if n_tot>0 else 0.0
                    rej_kg = 0.0
                    if rej_line_col and not df_rej_f.empty:
                        ln_rej = df_rej_f[df_rej_f[rej_line_col].astype(str).str.strip()==str(ln).strip()]
                        for rc in [rej_ats_col,rej_prt_col,rej_cam_col]:
                            if rc: rej_kg += pd.to_numeric(ln_rej[rc], errors='coerce').sum()
                    bl_val = 0
                    if bl_line_col and bl_total_col and not df_backlog_f.empty:
                        ln_bl = df_backlog_f[df_backlog_f[bl_line_col].astype(str).str.strip()==str(ln).strip()]
                        if not ln_bl.empty:
                            bl_val = int(pd.to_numeric(ln_bl[bl_total_col], errors='coerce').iloc[-1])
                    rows.append({'Line':str(ln),'AF Box':n_af,'Target':int(tgt),
                                 'Yield%':yld,'Scrap%':scr,'Rej (kg)':round(rej_kg,2),
                                 'Backlog':bl_val,'Status':"🟢" if scr<=3 else ("🟡" if scr<=10 else "🔴")})

            if rows:
                df_tbl = pd.DataFrame(rows)
                def c_yield(v):
                    if v>=90: return 'color:#00d4aa;font-weight:bold'
                    if v>=70: return 'color:#ffa502;font-weight:bold'
                    return 'color:#ff4757;font-weight:bold'
                def c_scrap(v):
                    if v<=3: return 'color:#00d4aa'
                    if v<=10: return 'color:#ffa502;font-weight:bold'
                    return 'color:#ff4757;font-weight:bold'
                styled = (df_tbl.style.map(c_yield,subset=['Yield%']).map(c_scrap,subset=['Scrap%'])
                          .format({'Yield%':'{:.1f}%','Scrap%':'{:.1f}%','Rej (kg)':'{:.2f}',
                                   'AF Box':'{:,}','Target':'{:,}','Backlog':'{:,}'})
                          .set_properties(**{'background-color':'#1a2332','color':'#cdd9e5'}))
                st.dataframe(styled, use_container_width=True, hide_index=True, height=340)
                excel_btn(df_tbl.set_index('Line'), "Line Breakdown", "Line_Breakdown")
            else:
                st.info("💡 ไม่มีข้อมูล")

        with col_side:
            st.markdown("##### ⏳ Backlog (งานค้างสะสม)")
            if bl_total_col and not df_backlog_f.empty and bl_line_col:
                df_bl = (df_backlog_f.groupby(bl_line_col).last().reset_index()[[bl_line_col,bl_total_col]])
                df_bl[bl_total_col] = pd.to_numeric(df_bl[bl_total_col], errors='coerce').fillna(0)
                df_bl = df_bl[df_bl[bl_total_col]>0].sort_values(bl_total_col,ascending=False)
                if not df_bl.empty:
                    fig_bl = px.bar(df_bl, x=bl_line_col, y=bl_total_col, text=bl_total_col,
                                    color=bl_total_col,
                                    color_continuous_scale=[[0,'#1e6b4a'],[0.5,'#ffa502'],[1,'#ff4757']])
                    fig_bl.update_traces(textposition='outside')
                    fig_bl.update_layout(
                        height=200, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        font_color='#cdd9e5', margin=dict(t=10,b=5,l=5,r=5),
                        showlegend=False, coloraxis_showscale=False,
                        yaxis=dict(gridcolor='#1e2a3a'), xaxis=dict(title=''))
                    st.plotly_chart(fig_bl, use_container_width=True)
                else:
                    st.success("🟢 ไม่มีงานค้าง!")
            else:
                st.info("💡 ไม่มีข้อมูล Backlog")

            st.markdown("##### 🔄 Re-pass Summary")
            if rp_result_col and not df_repass_f.empty:
                rp_success = (df_repass_f[rp_result_col].astype(str).str.upper().str.strip()=='AF').sum()
                rp_rate    = round(rp_success/len(df_repass_f)*100,1) if len(df_repass_f)>0 else 0
                r1,r2,r3   = st.columns(3)
                for col_r,lbl,val,clr in [
                    (r1,'ทั้งหมด',len(df_repass_f),'kpi-white'),
                    (r2,'สำเร็จ',rp_success,'kpi-green'),
                    (r3,'Success%',f"{rp_rate}%",'kpi-green' if rp_rate>=80 else 'kpi-yellow')]:
                    col_r.markdown(f"""<div class='kpi-card'>
                        <div class='kpi-label'>{lbl}</div>
                        <div class='kpi-value {clr}' style='font-size:22px;'>{val}</div>
                    </div>""", unsafe_allow_html=True)
                if rp_line_col:
                    rp_by_line = df_repass_f.groupby(rp_line_col).size().reset_index(name='Count')
                    fig_rp = px.bar(rp_by_line, x=rp_line_col, y='Count', text='Count',
                                    color='Count', color_continuous_scale='Reds')
                    fig_rp.update_traces(textposition='outside')
                    fig_rp.update_layout(
                        height=160, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        font_color='#cdd9e5', margin=dict(t=10,b=5,l=5,r=5),
                        showlegend=False, coloraxis_showscale=False,
                        yaxis=dict(gridcolor='#1e2a3a'), xaxis=dict(title=''))
                    st.plotly_chart(fig_rp, use_container_width=True)
            else:
                st.info("💡 ไม่มีข้อมูล Re-pass")

        st.markdown("---")

        # ── Non-AF Pending — dedup เอาแถวล่าสุดของแต่ละ Line+Batch+Box ────────
        st.markdown("<div class='section-header'>⚠️ กล่องที่รอการ Re-pass / ยังไม่ผ่าน (Non-AF)</div>",
                    unsafe_allow_html=True)

        if box_status_col and not df_box.empty:  # ใช้ df_box ดิบ (ไม่ filter time เพื่อให้เห็นสถานะล่าสุด)
            df_box_latest = df_box.copy()

            # ✅ dedup: เอา record ล่าสุดของแต่ละ Line+Batch+Box
            # sort by time แล้ว groupby เอา last
            if box_time_col and box_line_col and box_batch_col and box_box_col:
                df_box_latest = (
                    df_box_latest
                    .sort_values(box_time_col, na_position='first')
                    .groupby([box_line_col, box_batch_col, box_box_col], as_index=False)
                    .last()
                )
            elif box_line_col and box_batch_col and box_box_col:
                df_box_latest = (
                    df_box_latest
                    .groupby([box_line_col, box_batch_col, box_box_col], as_index=False)
                    .last()
                )

            # filter line ถ้ามี global filter
            if box_line_col and filter_line != "ทั้งหมด":
                df_box_latest = df_box_latest[df_box_latest[box_line_col].astype(str).str.strip() == filter_line]

            df_pending = df_box_latest[
                df_box_latest[box_status_col].astype(str).str.upper().str.strip() != 'AF'
            ].copy()

            if not df_pending.empty:
                col_tbl2, col_pie = st.columns([2, 1])
                with col_tbl2:
                    st.markdown(f"**พบ {len(df_pending):,} กล่อง** รอดำเนินการ "
                                f"<span style='font-size:11px;color:#7ab3d4;'>(แสดงสถานะล่าสุดของแต่ละกล่อง)</span>",
                                unsafe_allow_html=True)
                    st.dataframe(df_pending, use_container_width=True, hide_index=True, height=250)
                with col_pie:
                    STATUS_COLORS_MAP = {'Sort':'#f1c40f','PS':'#e67e22','HP':'#3498db',
                                         'HUP':'#2980b9','HFX':'#9b59b6','Scrap':'#e74c3c'}
                    s_dist = (df_pending[box_status_col].astype(str).str.strip()
                              .value_counts().reset_index())
                    s_dist.columns = ['Status','Count']
                    clrs   = [STATUS_COLORS_MAP.get(s,'#95a5a6') for s in s_dist['Status']]
                    fig_pie = px.pie(s_dist, values='Count', names='Status',
                                     color_discrete_sequence=clrs, hole=0.45)
                    fig_pie.update_traces(textinfo='percent+label', textposition='inside')
                    fig_pie.update_layout(
                        height=250, paper_bgcolor='rgba(0,0,0,0)',
                        font_color='#cdd9e5', margin=dict(t=10,b=10,l=10,r=10), showlegend=False)
                    st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.success("🟢 ทุกกล่องผ่านเกณฑ์ AF แล้ว ไม่มีงานค้าง")
        else:
            st.info("💡 ไม่มีข้อมูล Box Status")

    st.markdown(
        f"<div style='text-align:center;color:#445566;font-size:11px;margin-top:20px;'>"
        f"📊 ประมวลผลล่าสุด: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ·  Production Tracking System"
        f"</div>", unsafe_allow_html=True)
