import streamlit as st
import pandas as pd
from datetime import datetime
from constants import (
    LINES, CUSTOMER_NAMES, METAL_DETECTOR_OPTIONS,
    COUNTRIES, BOX_PACKING_OPTIONS, INK_OPTIONS, BATCH_STATUS
)


def show_plan_page(load_csv, save_to_csv, update_full_sheet):
    st.markdown("<div class='main-header'>📅 Production Planning Management</div>", unsafe_allow_html=True)
    plan_df = load_csv("plan")
    if 'editing_batch' not in st.session_state:
        st.session_state.editing_batch = None

    # ==========================================
    if st.session_state.editing_batch is not None:
        idx = st.session_state.editing_batch
        row = plan_df.iloc[idx]
        st.subheader(f"📝 แก้ไขข้อมูล Batch: {row['batch number']}")

        with st.form("edit_mode_form"):
            st.markdown("##### 📦 ข้อมูลการผลิต")
            r1c1, r1c2, r1c3, r1c4 = st.columns(4)
            e_line = r1c1.selectbox("Line", LINES, index=LINES.index(row['line']) if row['line'] in LINES else 0)
            e_batch = r1c2.text_input("Batch Number", value=str(row['batch number']))
            e_sap = r1c3.text_input("SAP Batch", value=str(row['sap batch']))
            e_order = r1c4.text_input("Prod. Order", value=str(row['production order']))

            r2c1, r2c2, r2c3, r2c4 = st.columns(4)
            e_inspec = r2c1.text_input("Inspec. Lot", value=str(row['inspection lot']))
            e_so = r2c2.text_input("Sales Order", value=str(row['sales order']))
            e_so_item = r2c3.text_input("SO Item", value=str(row['sales order item']))
            e_fert = r2c4.text_input("FERT Code", value=str(row['fert code']))

            r3c1, r3c2, r3c3, r3c4 = st.columns(4)
            e_semi = r3c1.text_input("Semi Code", value=str(row['semifinish code']))
            e_qty = r3c2.number_input("Item Qty (K)", value=float(row['item qty']), format="%.3f")
            e_af = r3c3.number_input("Need AF Box", value=float(row['need af box']), format="%.0f")
            e_cust = r3c4.selectbox("Customer", CUSTOMER_NAMES, index=CUSTOMER_NAMES.index(row['customer name']) if row[
                                                                                                                        'customer name'] in CUSTOMER_NAMES else 0)

            st.markdown("##### 🎨 รายละเอียดบรรจุภัณฑ์")
            r4c1, r4c2, r4c3, r4c4 = st.columns(4)
            e_finish = r4c1.date_input("Plan Finish", value=pd.to_datetime(row['planned finish date']))
            e_desp = r4c2.date_input("To be Desp.", value=pd.to_datetime(row['to be desp on']))
            e_metal = r4c3.selectbox("Metal Det.", METAL_DETECTOR_OPTIONS,
                                     index=METAL_DETECTOR_OPTIONS.index(row['metal detector']) if row[
                                                                                                      'metal detector'] in METAL_DETECTOR_OPTIONS else 0)
            e_print = r4c4.selectbox("Print Type", ["U", "P"],
                                     index=["U", "P"].index(row['print type']) if row['print type'] in ["U",
                                                                                                        "P"] else 0)

            r5c1, r5c2, r5c3, r5c4 = st.columns(4)
            e_country = r5c1.selectbox("Country", COUNTRIES,
                                       index=COUNTRIES.index(row['country']) if row['country'] in COUNTRIES else 0)
            e_box = r5c2.selectbox("Box Packing", BOX_PACKING_OPTIONS,
                                   index=BOX_PACKING_OPTIONS.index(row['box packing']) if row[
                                                                                              'box packing'] in BOX_PACKING_OPTIONS else 0)
            e_ink_cap = r5c3.selectbox("Ink Cap", INK_OPTIONS,
                                       index=INK_OPTIONS.index(row['ink cap']) if row['ink cap'] in INK_OPTIONS else 0)
            e_rol_cap = r5c4.text_input("Roller Des Cap", value=str(row['roller des cap']))

            r6c1, r6c2, r6c3, r6c4 = st.columns(4)
            e_ink_body = r6c1.selectbox("Ink Body", INK_OPTIONS, index=INK_OPTIONS.index(row['ink body']) if row[
                                                                                                                 'ink body'] in INK_OPTIONS else 0)
            e_rol_body = r6c2.text_input("Roller Des Body", value=str(row['roller des body']))
            e_status = r6c3.selectbox("Status", ["Running", "Finished"],
                                      index=0 if row['batch status'] == "Running" else 1)

            bc1, bc2 = st.columns(2)
            if bc1.form_submit_button("💾 บันทึกการแก้ไข", use_container_width=True, type="primary"):
                plan_df.iloc[idx] = [e_line, e_batch, e_sap, e_order, e_inspec, e_so, e_so_item, e_fert, e_semi, e_qty,
                                     e_af, e_cust, str(e_finish), str(e_desp), e_metal, e_print, e_country, e_box,
                                     e_ink_cap, e_rol_cap, e_ink_body, e_rol_body, e_status]

                update_full_sheet(plan_df, "plan")
                st.cache_data.clear()
                st.session_state.editing_batch = None
                st.rerun()

            if bc2.form_submit_button("❌ ยกเลิก", use_container_width=True):
                st.session_state.editing_batch = None
                st.rerun()
        st.stop()

    # ==========================================
    t_view, t_add, t_finish = st.tabs(["🔍 Plan", "➕ Add Plan", "🔄 Manage Plan"])

    with t_view:
        col_f1, col_f2 = st.columns([2, 1])
        show_finished = col_f2.checkbox("แสดง Batch ที่จบงานแล้ว (Finished)")

        display_df = plan_df.copy()
        if not show_finished:
            display_df = display_df[display_df['batch status'] == "Running"]

        if not display_df.empty:
            display_df['sort_line'] = display_df['line'].astype(str).str.extract(r'(\d+)').astype(float).fillna(999)
            display_df['sort_batch'] = pd.to_numeric(display_df['batch number'], errors='coerce').fillna(9999999999)
            display_df = display_df.sort_values(by=['sort_line', 'sort_batch'], ascending=[True, True])
            display_df = display_df.drop(columns=['sort_line', 'sort_batch'])

        st.dataframe(display_df, use_container_width=True, hide_index=True)

    with t_add:
        st.subheader("กรอกข้อมูลแผนใหม่ (23 คอลัมน์)")
        with st.form("full_add_form", clear_on_submit=True):
            st.markdown("##### 📦 ข้อมูลการผลิต")
            a1, a2, a3, a4 = st.columns(4)
            n_line = a1.selectbox("Line", LINES)
            n_batch = a2.text_input("Batch Number")
            n_sap = a3.text_input("SAP Batch")
            n_order = a4.text_input("Prod. Order")

            a5, a6, a7, a8 = st.columns(4)
            n_inspec = a5.text_input("Inspection Lot")
            n_so = a6.text_input("Sales Order")
            n_so_item = a7.text_input("SO Item")
            n_fert = a8.text_input("FERT Code")

            a9, a10, a11, a12 = st.columns(4)
            n_semi = a9.text_input("Semifinish Code")
            n_qty = a10.number_input("Item Qty (K)", min_value=0.0, format="%.3f")
            n_af = a11.number_input("Need AF Box", min_value=0.0, format="%.0f")
            n_cust = a12.selectbox("Customer", CUSTOMER_NAMES)

            st.markdown("##### 🎨 รายละเอียดบรรจุภัณฑ์")
            a13, a14, a15, a16 = st.columns(4)
            n_finish = a13.date_input("Plan Finish Date")
            n_desp = a14.date_input("To be Desp. on")
            n_metal = a15.selectbox("Metal Detector", METAL_DETECTOR_OPTIONS)
            n_print = a16.selectbox("Print Type", ["U", "P"])

            a17, a18, a19, a20 = st.columns(4)
            n_country = a17.selectbox("Country", COUNTRIES)
            n_box = a18.selectbox("Box Packing", BOX_PACKING_OPTIONS)
            n_ink_cap = a19.selectbox("Ink Cap", INK_OPTIONS)
            n_rol_cap = a20.text_input("Roller Des Cap")

            a21, a22, a23 = st.columns(3)
            n_ink_body = a21.selectbox("Ink body", INK_OPTIONS)
            n_rol_body = a22.text_input("Roller Des Body")
            n_status = a23.selectbox("Batch Status", BATCH_STATUS)

            if st.form_submit_button("➕ บันทึกแผนงานใหม่", use_container_width=False, type="primary"):
                if n_batch:
                    new_row = [n_line, n_batch, n_sap, n_order, n_inspec, n_so, n_so_item, n_fert, n_semi, n_qty, n_af,
                               n_cust, str(n_finish), str(n_desp), n_metal, n_print, n_country, n_box, n_ink_cap,
                               n_rol_cap, n_ink_body, n_rol_body, n_status]

                    save_to_csv("plan", pd.DataFrame([new_row], columns=plan_df.columns))

                    # 🎯 ล้างแคชเมื่อเพิ่มแผนสำเร็จ เพื่อให้ดึงข้อมูลชุดใหม่ไปแสดงในหน้า Plan
                    st.cache_data.clear()
                    st.success("บันทึกแผนใหม่เรียบร้อย!")
                    st.rerun()
                else:
                    st.error("กรุณาระบุ Batch Number")

    with t_finish:
        st.markdown("""
            <style>
                div[data-testid="stBlock"] div[border="true"] {
                    padding: 6px 10px !important;
                    margin-bottom: -10px !important;
                }
                div[data-testid="stBlock"] p {
                    margin-bottom: 2px !important;
                    font-size: 14px !important;
                }
                div[data-testid="stBlock"] button {
                    padding-top: 2px !important;
                    padding-bottom: 2px !important;
                    min-height: 28px !important;
                    font-size: 13px !important;
                }
            </style>
        """, unsafe_allow_html=True)

        run_df = plan_df[plan_df['batch status'] == "Running"]
        if not run_df.empty:
            run_df_sorted = run_df.copy()
            run_df_sorted['sort_line'] = run_df_sorted['line'].astype(str).str.extract(r'(\d+)').astype(float).fillna(
                999)
            run_df_sorted['sort_batch'] = pd.to_numeric(run_df_sorted['batch number'], errors='coerce').fillna(
                9999999999)
            run_df_sorted = run_df_sorted.sort_values(by=['sort_line', 'sort_batch'], ascending=[True, True])

            for idx, row in run_df_sorted.iterrows():
                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 0.7, 0.7])
                    c1.write(f"📍 Line: {row['line']} | Batch: **{row['batch number']}** | FERT: {row['fert code']}")

                    if c2.button("📝 แก้ไข", key=f"e_{idx}"):
                        st.session_state.editing_batch = idx
                        st.rerun()

                    if c3.button("🚩 จบงาน", key=f"f_{idx}", type="primary"):
                        plan_df.at[idx, 'batch status'] = "Finished"

                        update_full_sheet(plan_df, "plan")
                        st.cache_data.clear()
                        st.rerun()
        else:
            st.info("ไม่มีงานค้างในระบบ")
