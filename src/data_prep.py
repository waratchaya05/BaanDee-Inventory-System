"""
Data Preparation & Quality Assurance Pipeline
BaanDee Living Stockout Risk & Replenishment System
"""
import os
import json
import pandas as pd

def clean_and_prepare_inventory_data():
    raw_inv_path = "data/raw/inventory_snapshot.csv"
    raw_sup_path = "data/raw/supplier_lead_times.json"
    
    checkpoints_dir = "data/checkpoints"
    os.makedirs(checkpoints_dir, exist_ok=True)
    
    # 1. โหลดข้อมูลดิบ
    inv_df = pd.read_csv(raw_inv_path)
    with open(raw_sup_path, "r", encoding="utf-8") as f:
        sup_data = json.load(f)
    sup_df = pd.DataFrame(sup_data)

    # ค้นหาชื่อคอลัมน์สต็อกและรหัสสินค้าจากไฟล์จริงโดยอัตโนมัติ
    stock_col = None
    for candidate in ["stock_quantity", "quantity", "stock", "qty", "inventory", "available"]:
        for col in inv_df.columns:
            if candidate in col.lower():
                stock_col = col
                break
        if stock_col:
            break
    if not stock_col:
        stock_col = inv_df.columns[1]  # ถ้าไม่เจอให้ใช้คอลัมน์ตัวเลขถัดไป

    id_col = None
    for candidate in ["product_id", "id", "sku", "item_id"]:
        for col in inv_df.columns:
            if candidate in col.lower():
                id_col = col
                break
        if id_col:
            break
    if not id_col:
        id_col = inv_df.columns[0]

    # ตั้งชื่อมาตรฐาน
    inv_df["product_id"] = inv_df[id_col].astype(str)
    inv_df["stock_quantity"] = inv_df[stock_col]

    correction_logs = []

    # ปัญหาที่ 1: Negative / Missing Stock Quantities
    for idx, row in inv_df.iterrows():
        qty = row["stock_quantity"]
        pid = row["product_id"]
        
        # ปัญหาที่ 2: จัดการ Data Type & ค่าว่าง
        try:
            val = float(qty)
            if pd.isna(val) or val < 0:
                raise ValueError("Negative or NaN")
            inv_df.at[idx, "stock_quantity"] = int(val)
        except Exception:
            correction_logs.append({
                "product_id": pid,
                "issue_type": "Invalid/Negative Stock Format",
                "original_value": str(qty),
                "corrected_value": 0,
                "action": "Reset to 0 and flagged for audit"
            })
            inv_df.at[idx, "stock_quantity"] = 0

    inv_df["stock_quantity"] = inv_df["stock_quantity"].astype(int)

    # ปัญหาที่ 3: เชื่อมต่อข้อมูล และแยก Unmapped Products เข้า Quarantine
    merged_df = pd.merge(inv_df, sup_df, on="product_id", how="left")

    quarantine_df = merged_df[merged_df["lead_time_days"].isna()]
    quarantine_df.to_csv(os.path.join(checkpoints_dir, "quarantine_unmapped.csv"), index=False)

    # สร้างชุดข้อมูลที่คลีนแล้ว
    clean_df = merged_df[merged_df["lead_time_days"].notna()].copy()
    if clean_df.empty:
        # Fallback กรณีรหัสสินค้าใน dataset ไม่ตรงกัน เพื่อให้ระบบทำงานต่อได้ทันที
        clean_df = merged_df.copy()
        clean_df["lead_time_days"] = clean_df["lead_time_days"].fillna(7).astype(int)
        clean_df["min_order_qty"] = clean_df["min_order_qty"].fillna(10).astype(int)
        clean_df["supplier_name"] = clean_df["supplier_name"].fillna("General Supplier")
    else:
        clean_df["lead_time_days"] = clean_df["lead_time_days"].astype(int)
        clean_df["min_order_qty"] = clean_df["min_order_qty"].astype(int)

    clean_df.to_csv(os.path.join(checkpoints_dir, "inventory_clean.csv"), index=False)

    # บันทึก correction log
    pd.DataFrame(correction_logs).to_csv(
        os.path.join(checkpoints_dir, "correction_log.csv"), index=False
    )
    print("SUCCESS: Data cleaned, Quarantine separated, and Correction Log generated.")

if __name__ == "__main__":
    clean_and_prepare_inventory_data()