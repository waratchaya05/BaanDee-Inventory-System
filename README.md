# BaanDee Living: Stockout Risk & Smart Replenishment System

ระบบช่วยตรวจสอบสินค้าเสี่ยงขาดสต็อกและจัดทำข้อเสนอสั่งซื้ออัตโนมัติ (Data/AI Product Prototype) สำหรับธุรกิจค้าปลีกของตกแต่งบ้าน BaanDee Living

---

## 1. Problem & Persona (ปัญหาและผู้ใช้งานหลัก)
* **Target Persona:** เจ้าหน้าที่ฝ่ายจัดซื้อและบริหารสินค้าคงคลัง (Inventory & Procurement Specialist)
* **Core Pain Point:** ข้อมูลสต็อกกระจัดกระจาย การคำนวณรอบสั่งซื้อสินค้าใช้เวลานาน และไม่มีการคำนวณเปรียบเทียบกับระยะเวลาจัดส่งของซัพพลายเออร์ (Supplier Lead Time) ทำให้สินค้าขายดีขาดสต็อกบ่อยครั้ง
* **Value Delivered:** ประเมินความเสี่ยงสต็อกแบบเรียลไทม์ พร้อมหลักฐานประกอบการตัดสินใจ (Evidence-based) และระบบร่างใบสั่งซื้อ (Restock PO) ที่บันทึกและแก้ไขข้อมูลได้จริง

---

## 2. System Architecture & Boundaries (สถาปัตยกรรมระบบ)

[ Raw Datasets ] ───────► [ Data Prep Pipeline (DQ Fixes) ]
  - inventory_snapshot.csv   - Fix Negative Stock (Log to correction_log.csv)
  - supplier_lead_times.json - Handle Type Inconsistency
                             - Quarantine Unmapped items
                                          │
                                          ▼
                               [ data/checkpoints/ ]
                                          │
   ┌──────────────────────────────────────┴──────────────────────────────────────┐
   ▼                                                                             ▼
[ FastAPI Service (Port 8000) ]                                       [ Streamlit UI (Port 8501) ]
  - 200 OK: Evidence & Stockout Risk                                    - Tab 1: Risk Analysis & PO Draft
  - 404 Not Found: Unknown Products                                     - Tab 2: Persistent CRUD Management
  - 503 Unavailable: Data Source Down                                   - Tab 3: Data Quality Audit
   ▲                                                                             │
   └────────────────────────── HTTP REST Requests ───────────────────────────────┘
                                          │
                                          ▼
                               [ data/generated/restock_orders.json ] (Data Persistence)

---

## 3. Data Sources & Quality Assurance (การจัดการข้อมูล)
* **New Dataset Integration:** `data/raw/supplier_lead_times.json` บันทึก Lead Time และยอดสั่งขั้นต่ำ เชื่อมโยงด้วย `product_id`
* **Data Quality Points (DQ):**
  1. **Negative Stock Handling:** ตรวจจับสต็อกติดลบ รีเซ็ตเป็น 0 และบันทึกลง `data/checkpoints/correction_log.csv`
  2. **Type Inconsistency:** แปลงและตรวจสอบชนิดข้อมูลตัวเลขให้อยู่ในรูปแบบ Integer มาตรฐาน
  3. **Quarantine Unmapped Data:** สินค้าที่ไม่มีข้อมูล Lead Time จะถูกแยกไปไว้ที่ `data/checkpoints/quarantine_unmapped.csv` เพื่อรอเจ้าหน้าที่ตรวจสอบ ไม่เดาข้อมูลเอง

---

## 4. Setup & Running Instructions (ขั้นตอนการติดตั้งและรันระบบ)

### 4.1 สภาพแวดล้อมที่รองรับ
* Python 3.10 ขึ้นไป
* ติดตั้งไลบรารี:
  pip install pandas fastapi uvicorn requests streamlit pytest httpx

### 4.2 การรัน Data Pipeline
  python -m src.data_prep

### 4.3 การเปิดใช้งาน Backend API
  uvicorn api.main:app --reload --port 8000

### 4.4 การเปิดใช้งาน Frontend Dashboard
  streamlit run src/app.py

### 4.5 การรัน Automated Test Suite
  pytest tests/test_stockout_engine.py -v

---

## 5. Automated Tests Summary (ผลการทดสอบ 5 กรณี)
1. test_case_1_successful_risk_evaluation: ทดสอบประเมินความเสี่ยงสำเร็จ (HTTP 200)
2. test_case_2_unmapped_product_returns_404: ทดสอบกรณีค้นหาสินค้าไม่พบ (HTTP 404)
3. test_case_3_negative_stock_correction_log: ตรวจสอบการสร้างไฟล์ Correction Log
4. test_case_4_quarantine_unmapped_creation: ตรวจสอบการคัดแยกไฟล์ Quarantine
5. test_case_5_crud_persistence: ตรวจสอบความถูกต้องของการบันทึกและแก้ไขข้อมูลลงไฟล์ JSON