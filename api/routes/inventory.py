from fastapi import APIRouter, HTTPException
from api.schemas.inventory import InventoryRequest, InventoryResponse
from api.services.inventory_service import InventoryService
router=APIRouter()
@router.post("/inventory",response_model=InventoryResponse)
def inventory(req: InventoryRequest):
    try: return InventoryService().calculate(**req.model_dump())
    except (FileNotFoundError,ValueError) as exc: raise HTTPException(status_code=400,detail=str(exc))
    except Exception: raise HTTPException(status_code=500,detail="Inventory calculation failed due to an internal error.")
