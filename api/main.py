"""
BaanDee Living - Inventory Health & Supplier Connector API
Handles stock evaluation and suppliers integration.
"""
from fastapi import FastAPI, HTTPException
import pandas as pd
import os

app = FastAPI(
    title="BaanDee Inventory API",
    description="Simulated Supplier & Inventory Health Gateway",
    version="1.0.0"
)

CLEAN_INVENTORY_PATH = "data/checkpoints/inventory_clean.csv"

@app.get("/health")
def health_check():
    """Health check endpoint to verify service readiness."""
    return {"status": "ok", "service": "BaanDee Inventory Gateway"}

@app.get("/api/v1/inventory/{product_id}")
def get_inventory_status(product_id: str):
    """
    Evaluates stockout risk and returns decision evidence.
    Covers 3 Scenarios: Success (200), Not Found (404), Service Unavailable (503).
    """
    # สถานการณ์ที่ 3: ตรวจสอบความพร้อมของระบบ/ไฟล์ (503 Service Unavailable)
    if not os.path.exists(CLEAN_INVENTORY_PATH):
        raise HTTPException(
            status_code=503,
            detail="Inventory data service is currently unavailable or uninitialized."
        )

    df = pd.read_csv(CLEAN_INVENTORY_PATH)
    record = df[df["product_id"].astype(str) == str(product_id)]

    # สถานการณ์ที่ 2: ไม่พบข้อมูลสินค้า (404 Not Found)
    if record.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Product ID '{product_id}' was not found in verified catalog."
        )

    # สถานการณ์ที่ 1: ดึงข้อมูลสำเร็จ และคำนวณ Evidence (200 Success)
    item = record.iloc[0].to_dict()
    
    current_stock = int(item.get("stock_quantity", 0))
    lead_time = int(item.get("lead_time_days", 7))
    min_order_qty = int(item.get("min_order_qty", 10))
    supplier_name = item.get("supplier_name", "Primary Partner")

    # Business Logic: อัตราการขายเฉลี่ย (Run Rate) 2 ชิ้นต่อวัน
    daily_run_rate = 2.0
    days_to_stockout = current_stock / daily_run_rate if daily_run_rate > 0 else 999.0
    
    # ประเมินระดับความเสี่ยง
    if days_to_stockout <= lead_time:
        risk_level = "CRITICAL"
        # สั่งให้ครอบคลุม Lead Time 2 รอบ + Safety Stock
        suggested_qty = max(min_order_qty, int(daily_run_rate * lead_time * 2))
    elif days_to_stockout <= (lead_time + 3):
        risk_level = "WARNING"
        suggested_qty = min_order_qty
    else:
        risk_level = "HEALTHY"
        suggested_qty = 0

    return {
        "product_id": str(product_id),
        "supplier_name": supplier_name,
        "current_stock": current_stock,
        "lead_time_days": lead_time,
        "daily_run_rate": daily_run_rate,
        "days_to_stockout": round(days_to_stockout, 1),
        "risk_level": risk_level,
        "suggested_order_qty": suggested_qty,
        "evidence_summary": f"Stock lasts {round(days_to_stockout, 1)} days vs Supplier lead time {lead_time} days."
    }