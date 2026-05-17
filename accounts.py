import streamlit as st
import pandas as pd


def show_account_page(load_csv, save_to_csv, update_full_sheet):
    st.markdown("<div class='main-header'>👥 Account Management</div>", unsafe_allow_html=True)
    acc_df = load_csv("accounts")
    if "active_account_tab" not in st.session_state:
        st.session_state.active_account_tab = 0  # เริ่มต้นที่แทร็บแรก (0 = เพิ่มผู้ใช้, 1 = จัดการข้อมูล)

    # ผูกค่าใน st.tabs เข้ากับความจำของแอปพลิเคชัน
    tab_titles = ["➕ เพิ่มผู้ใช้ใหม่", "⚙️ จัดการ/แก้ไขข้อมูล"]

    # ดึงค่าแทร็บล่าสุดขึ้นมาแสดงผลโดยอัตโนมัติ
    tabs = st.tabs(tab_titles)
    tab_add = tabs[0]
    tab_manage = tabs[1]

    # ==========================================
    with tab_add:
        st.subheader("📝 กรอกข้อมูลผู้ใช้ใหม่")
        with st.form("add_acc_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            fn = c1.text_input("ชื่อ-นามสกุล")
            eid = c2.text_input("รหัสพนักงาน")
            un = c1.text_input("Username")
            pw = c2.text_input("Password", type="password")
            rl = st.selectbox("ตำแหน่ง", ["operator", "supervisor", "admin"])

            if st.form_submit_button("💾 บันทึกและสร้างบัญชี", use_container_width=True, type="primary"):
                if fn and un and pw:
                    if not acc_df.empty and un.strip() in acc_df['username'].astype(str).values:
                        st.error("❌ Username นี้มีในระบบแล้ว กรุณาใช้ชื่ออื่น")
                    else:
                        new_acc = pd.DataFrame([{
                            "fullname": fn.strip(),
                            "emp_id": eid.strip(),
                            "username": un.strip(),
                            "password": pw,
                            "role": rl,
                            "first_login": True
                        }])
                        save_to_csv("accounts", new_acc)

                        # 🎯 บันทึกเสร็จ ให้หน้าจอยังคงล็อกอยู่ที่แทร็บแรก
                        st.session_state.active_account_tab = 0
                        st.cache_data.clear()

                        st.success(f"✅ เพิ่มผู้ใช้ {fn} เรียบร้อยแล้ว")
                        st.rerun()
                else:
                    st.error("⚠️ กรุณากรอกข้อมูล ชื่อ-นามสกุล, Username และ Password ให้ครบถ้วน")

    # แทร็บที่ 2: จัดการ / แก้ไขข้อมูล / ลบข้อมูล
    # ==========================================
    with tab_manage:
        if not acc_df.empty:
            st.subheader("📋 รายชื่อผู้ใช้ในระบบปัจจุบัน")
            st.dataframe(
                acc_df[['fullname', 'emp_id', 'username', 'role']],
                use_container_width=True,
                hide_index=True
            )

            st.markdown("---")
            st.subheader("⚙️ ดำเนินการจัดการบัญชี")

            # หากพนักงานกำลังเลือกคนหรือตั้งท่าจะกดจัดการ ให้ล็อกสถานะแทร็บเป็นแทร็บที่ 2 (index 1) ทันที
            user_options = [f"{row['fullname']} ({row['username']})" for _, row in acc_df.iterrows()]

            # บังคับส่งสัญญาณว่ามีการเข้ามาใช้พื้นที่ของแทร็บจัดการข้อมูลแล้ว
            selected_option = st.selectbox("เลือกบัญชีที่ต้องการจัดการ", user_options, key="acc_select_box")

            target_user = selected_option.split("(")[-1].replace(")", "").strip()
            user_row = acc_df[acc_df['username'] == target_user].iloc[0]

            if "edit_mode" not in st.session_state:
                st.session_state.edit_mode = False
            if "last_target" not in st.session_state:
                st.session_state.last_target = target_user

            if st.session_state.last_target != target_user:
                st.session_state.edit_mode = False
                st.session_state.last_target = target_user
                st.session_state.active_account_tab = 1

            c1, c2 = st.columns([2, 2])

            if c1.button("📝 แก้ไขข้อมูลผู้ใช้", use_container_width=True):
                st.session_state.edit_mode = True
                st.session_state.active_account_tab = 1
                st.rerun()

            if c2.button("🗑️ ลบผู้ใช้", use_container_width=True, type="primary"):
                current_login_user = st.session_state.user_data.get('username')

                if user_row['role'] == "admin" or target_user == "admin":
                    st.error("❌ ระบบรักษาความปลอดภัยขั้นสูง: ไม่สามารถลบบัญชีระดับ Administrator ออกจากระบบได้")
                elif target_user == current_login_user:
                    st.error("❌ ไม่สามารถลบบัญชีผู้ใช้ที่คุณกำลังล็อกอินใช้งานอยู่ในปัจจุบันได้")
                else:
                    updated_acc_df = acc_df[acc_df['username'] != target_user]
                    update_full_sheet(updated_acc_df, "accounts")

                    st.session_state.active_account_tab = 1
                    st.cache_data.clear()

                    st.success(f"🗑️ ลบผู้ใช้งาน [{user_row['fullname']}] ออกจากระบบเรียบร้อยแล้ว!")
                    st.session_state.edit_mode = False
                    st.rerun()

            if st.session_state.edit_mode:
                st.markdown("### ✏️ แก้ไขข้อมูลรายละเอียดบัญชี")
                with st.form("edit_user_form"):
                    col_edit1, col_edit2 = st.columns(2)

                    new_fullname = col_edit1.text_input("ชื่อ-นามสกุล", value=str(user_row['fullname']))
                    new_emp_id = col_edit2.text_input("รหัสพนักงาน", value=str(user_row['emp_id']))
                    new_username = col_edit1.text_input("Username", value=str(user_row['username']))

                    roles_options = ["operator", "supervisor", "admin"]
                    default_role_idx = roles_options.index(user_row['role']) if user_row['role'] in roles_options else 0
                    new_role = col_edit2.selectbox("เปลี่ยนตำแหน่งเป็น", roles_options, index=default_role_idx)

                    form_c1, form_c2 = st.columns(2)
                    if form_c1.form_submit_button("💾 บันทึกการแก้ไขข้อมูล", use_container_width=True, type="primary"):
                        if new_fullname.strip() and new_username.strip():
                            duplicate_check = acc_df[
                                (acc_df['username'] == new_username.strip()) & (acc_df['username'] != target_user)]

                            if not duplicate_check.empty:
                                st.error("❌ Username นี้มีผู้ใช้งานอื่นในระบบใช้แล้ว ไม่สามารถซ้ำกันได้")
                            else:
                                idx = acc_df[acc_df['username'] == target_user].index[0]
                                acc_df.loc[idx, 'fullname'] = new_fullname.strip()
                                acc_df.loc[idx, 'emp_id'] = new_emp_id.strip()
                                acc_df.loc[idx, 'username'] = new_username.strip()
                                acc_df.loc[idx, 'role'] = new_role

                                update_full_sheet(acc_df, "accounts")

                                # 🎯 แก้ไขเสร็จ ล้างแคช ล็อกให้อยู่หน้าเดิมเพื่อให้เห็นความเปลี่ยนแปลง
                                st.session_state.active_account_tab = 1
                                st.cache_data.clear()

                                st.success("🎉 อัปเดตข้อมูลผู้ใช้งานสำเร็จ!")
                                st.session_state.edit_mode = False
                                st.rerun()
                        else:
                            st.error("⚠️ ไม่สามารถบันทึกค่าว่างได้ กรุณากรอก ชื่อ-นามสกุล และ Username")

                    if form_c2.form_submit_button("❌ ยกเลิก", use_container_width=True):
                        st.session_state.edit_mode = False
                        st.session_state.active_account_tab = 1
                        st.rerun()
        else:
            st.info("ℹ️ ยังไม่มีข้อมูลบัญชีผู้ใช้ในระบบในขณะนี้")

    if st.session_state.active_account_tab == 1:
        st.components.v1.html(
            """
            <script>
            window.parent.document.querySelectorAll('button[role="tab"]')[1].click();
            </script>
            """,
            height=0,
        )

