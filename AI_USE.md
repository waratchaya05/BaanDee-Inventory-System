# AI Use Disclosure & Verification Log

เอกสารรายงานการใช้ประโยชน์จากเครื่องมือ Generative AI ในการพัฒนาระบบ BaanDee Stockout Risk & Replenishment System

---

## 1. AI Tools Utilized
* **Primary Tool:** Google Gemini
* **Purpose:** ผู้ช่วยระดมความคิดการออกแบบสถาปัตยกรรมซอฟต์แวร์ (Thought Partner), ช่วยแนะนำการวางโครงสร้าง FastAPI/Streamlit, และช่วยร่าง Test Cases

---

## 2. Prompts & Workflows (ตัวอย่างการ Prompt ใช้งานจริง)
* **การออกแบบ Data Preparation:**
  * *Prompt:* "ช่วยออกแบบกระบวนการคลีนข้อมูลที่แก้ปัญหาสต็อกติดลบ และแยกสินค้า unmapped เข้า quarantine ตามเกณฑ์ Data Quality"
  * *Human Verification:* ผู้พัฒนาได้นำโค้ดมาปรับปรุงตรรกะการตรวจสอบคอลัมน์อัตโนมัติ เพื่อป้องกัน KeyError เมื่อโครงสร้างข้อมูลดิบมีความคลาดเคลื่อน
* **การออกแบบ API Boundary:**
  * *Prompt:* "สร้าง FastAPI สำหรับระบบประเมินความเสี่ยงสต็อกที่รองรับ 3 สถานการณ์: 200 Success, 404 Not Found, และ 503 Unavailable"
  * *Human Verification:* ทดสอบเรียก API ผ่าน Swagger UI และเขียน Automated Tests ตรวจสอบ HTTP Status Codes จริง
* **การสร้าง CRUD & Persistence ใน Streamlit:**
  * *Prompt:* "ช่วยเขียน Streamlit UI ที่มีฟอร์มบันทึกใบสั่งซื้อลงไฟล์ JSON และมีแท็บเปิดอ่านพร้อมอัปเดตข้อมูลเดิมได้จริง"
  * *Human Verification:* ดักจับ EmptyDataError และทดสอบบันทึก-รีเฟรชข้อมูลบนหน้าเว็บเพื่อยืนยัน Persistence

---

## 3. Reflection & Verification Summary
AI ถูกนำมาใช้ในฐานะเครื่องมือเร่งความเร็วในการพัฒนา (Scaffolding & Boilerplate generation) โค้ดและตรรกะทางธุรกิจทั้งหมดได้รับการตรวจสอบและรันจริงใน Local Environment โดยผู้พัฒนามีความเข้าใจโครงสร้างและการทำงานของทุกโมดูล 100%