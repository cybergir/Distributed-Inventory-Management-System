from fastapi import APIRouter, HTTPException
from app.schemas import StockUpdate
from app.services.inventory import update_stock

router = APIRouter()

@router.post("/inventory/update")
async def update_inventory(update: StockUpdate):
    try:
        result = update_stock(
            update.product_id,
            update.warehouse_id,
            update.quantity_change
        )
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))