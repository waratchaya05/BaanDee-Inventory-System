"""
BaanDee Living - Stockout Risk & Replenishment Dashboard
Interactive Prototype with Full CRUD Persistence & Decision Evidence
"""
import streamlit as st
import requests
import json
import os
import pandas as pd

st.set_page_config(page_title="BaanDee Inventory Copilot", layout="wide")

API_BASE_URL = "http://127.0.0.1:8000/api/v1/inventory"
STORAGE_DIR = "data/generated"
PO_FILE = os.path.join(STORAGE_DIR, "restock_orders.json")
os.makedirs(STORAGE_DIR, exist_ok=True)

# Helper functions จัดการ Persistent JSON
def load_po_records():
    if not os.path.exists(PO_FILE):
        return []
    try:
        with open(PO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_po_records(records):
    with open(PO_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

st.title("📦 ระบบช่วยตรวจสอบสินค้าเสี่ยงขาดสต็อก & เสนอสั่งซื้อ")
st.caption("BaanDee Living Operations & Procurement Data Product Prototype")

# โหลดรายการสินค้าจาก checkpoint มาเป็นตัวเลือก
clean_inv_path = "data/checkpoints/inventory_clean.csv"
product_options = ["P001", "P002", "P003", "P004", "P999_UNKNOWN"]
if os.path.exists(clean_inv_path):
    try:
        raw_list = pd.read_csv(clean_inv_path)["product_id"].astype(str).unique().tolist()
        if raw_list:
            product_options = raw_list[:10] + ["P999_UNKNOWN"]
    except Exception:
        pass

tab1, tab2, tab3 = st.tabs(["🔍 ตรวจสอบความเสี่ยง & ออกใบสั่งซื้อ", "📋 จัดการและแก้ไขใบสั่งซื้อ (CRUD)", "📊 ประวัติการคลีนข้อมูล (Data Quality)"])

# ----------------- TAB 1: ตรวจสอบความเสี่ยง -----------------
with tab1:
    st.subheader("1. เลือกสินค้าเพื่อตรวจสอบสถานะสต็อก")
    col_sel, col_btn = st.columns([3, 1])
    with col_sel:
        selected_pid = st.selectbox("รหัสสินค้า (Product ID):", product_options)
    with col_btn:
        st.write("")
        st.write("")
        check_btn = st.button("🔎 ประเมินความเสี่ยง", use_container_width=True)

    if check_btn or "analysis_result" in st.session_state:
        if check_btn:
            try:
                res = requests.get(f"{API_BASE_URL}/{selected_pid}")
                if res.status_code == 200:
                    st.session_state["analysis_result"] = res.json()
                elif res.status_code == 404:
                    st.session_state["analysis_result"] = {"error": "404", "msg": res.json().get("detail")}
                else:
                    st.session_state["analysis_result"] = {"error": str(res.status_code), "msg": "API Service Unavailable (503)"}
            except Exception as e:
                st.session_state["analysis_result"] = {"error": "connection", "msg": f"เชื่อมต่อ API ไม่สำเร็จ: {e}"}

        result = st.session_state.get("analysis_result", {})
        if "error" in result:
            st.error(f"⚠️ การตอบสนองจากระบบ: {result['msg']}")
            st.info("💡 ข้อสังเกต: สินค้ารายการนี้ถูกคัดแยกเข้า Quarantine หรือไม่มีข้อมูลในระบบซัพพลายเออร์")
        else:
            st.success("✅ ได้รับข้อมูลหลักฐานสำหรับการตัดสินใจจาก API เรียบร้อยแล้ว")
            
            # แสดง Evidence Dashboard
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("สต็อกปัจจุบัน", f"{result['current_stock']} ชิ้น")
            c2.metric("ระยะเวลาขนส่ง (Lead Time)", f"{result['lead_time_days']} วัน")
            c3.metric("สต็อกพอขายได้อีก", f"{result['days_to_stockout']} วัน")
            
            status_color = "🔴" if result['risk_level'] == "CRITICAL" else ("🟡" if result['risk_level'] == "WARNING" else "🟢")
            c4.metric("ระดับความเสี่ยง", f"{status_color} {result['risk_level']}")

            st.write(f"**หลักฐานประกอบการตัดสินใจ:** {result['evidence_summary']}")
            st.write(f"**ซัพพลายเออร์คู่ค้า:** {result['supplier_name']}")

            # ส่วนสร้างใบสั่งซื้อ (Create & Save)
            st.markdown("---")
            st.subheader("📝 ออกใบขอสั่งซื้อสินค้าเติมสต็อก (Create PO Draft)")
            with st.form("create_po_form"):
                order_qty = st.number_input(
                    "จำนวนที่ต้องการสั่งซื้อ (ชิ้น):",
                    min_value=1,
                    value=int(result.get("suggested_order_qty", 10) if result.get("suggested_order_qty", 0) > 0 else 10)
                )
                urgency = st.selectbox("ความเร่งด่วน:", ["ด่วนมาก (Critical)", "ปกติ (Standard)", "รอรอบปกติ (Low)"])
                note = st.text_input("หมายเหตุเพิ่มเติม:", value=f"ความเสี่ยงระดับ {result['risk_level']}")
                
                submit_po = st.form_submit_button("💾 บันทึกใบขอสั่งซื้อ (Save to Storage)")
                if submit_po:
                    current_pos = load_po_records()
                    new_po = {
                        "po_id": f"PO-{result['product_id']}-{len(current_pos)+1:03d}",
                        "product_id": result["product_id"],
                        "supplier_name": result["supplier_name"],
                        "quantity": int(order_qty),
                        "urgency": urgency,
                        "note": note,
                        "status": "Pending Review"
                    }
                    current_pos.append(new_po)
                    save_po_records(current_pos)
                    st.success(f"🎉 สร้างใบสั่งซื้อ {new_po['po_id']} สำเร็จ และบันทึกข้อมูลลง JSON แล้ว!")

# ----------------- TAB 2: จัดการและแก้ไขข้อมูล (CRUD) -----------------
with tab2:
    st.subheader("📋 รายการใบสั่งซื้อในระบบ (Persistent Data Store)")
    po_list = load_po_records()
    
    if not po_list:
        st.info("ยังไม่มีข้อมูลใบสั่งซื้อในระบบ สามารถสร้างรายการใหม่ได้ที่แท็บแรก")
    else:
        st.dataframe(pd.DataFrame(po_list), use_container_width=True)
        
        st.markdown("---")
        st.subheader("✏️ แก้ไขข้อมูลใบสั่งซื้อ (Update Existing Record)")
        po_ids = [p["po_id"] for p in po_list]
        selected_po_to_edit = st.selectbox("เลือกใบสั่งซื้อที่ต้องการแก้ไข:", po_ids)
        target_record = next(p for p in po_list if p["po_id"] == selected_po_to_edit)
        
        with st.form("edit_po_form"):
            new_qty = st.number_input("ปรับจำนวนสั่งซื้อ:", min_value=1, value=int(target_record["quantity"]))
            new_status = st.selectbox("ปรับสถานะ:", ["Pending Review", "Approved", "Order Placed", "Cancelled"], index=0)
            new_note = st.text_input("แก้ไขหมายเหตุ:", value=target_record.get("note", ""))
            
            save_edit_btn = st.form_submit_button("💾 อัปเดตการแก้ไข (Save Changes)")
            if save_edit_btn:
                for p in po_list:
                    if p["po_id"] == selected_po_to_edit:
                        p["quantity"] = int(new_qty)
                        p["status"] = new_status
                        p["note"] = new_note
                        break
                save_po_records(po_list)
                st.success(f"✅ บันทึกการแก้ไขของ {selected_po_to_edit} เรียบร้อยแล้ว ข้อมูลคงอยู่อย่างถาวร!")
                st.rerun()

# ----------------- TAB 3: แสดงประวัติคุณภาพข้อมูล -----------------
# ----------------- TAB 3: แสดงประวัติคุณภาพข้อมูล -----------------
with tab3:
    st.subheader("📊 ตรวจสอบหลักฐานการทำความสะอาดข้อมูล (Data Quality Audit)")
    log_file = "data/checkpoints/correction_log.csv"
    quarantine_file = "data/checkpoints/quarantine_unmapped.csv"
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.write("##### 🛠️ รายการแก้ไขสต็อกติดลบ/ผิดฟอร์แมต (Correction Log)")
        if os.path.exists(log_file) and os.path.getsize(log_file) > 0:
            try:
                st.dataframe(pd.read_csv(log_file), use_container_width=True)
            except Exception:
                st.info("ยังไม่มีรายการแก้ไขที่ต้องบันทึก")
        else:
            st.info("ยังไม่มีประวัติการแก้ไขข้อมูล (ข้อมูลผ่านเกณฑ์ทั้งหมด)")
            
    with col_b:
        st.write("##### ⚠️ รายการที่ตรวจสอบไม่ได้ แยกเข้า Quarantine")
        if os.path.exists(quarantine_file) and os.path.getsize(quarantine_file) > 0:
            try:
                st.dataframe(pd.read_csv(quarantine_file), use_container_width=True)
            except Exception:
                st.info("ไม่มีรายการใน Quarantine")
        else:
            st.info("ไม่มีรายการสินค้าที่ตกค้างใน Quarantine")