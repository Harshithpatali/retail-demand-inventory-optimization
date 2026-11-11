from fastapi import APIRouter, HTTPException

from api.schemas.inventory import InventoryRequest, InventoryResponse
from api.services.inventory_service import InventoryService

router = APIRouter()


@router.post("/inventory", response_model=InventoryResponse)
def inventory(req: InventoryRequest):
    try:
        return InventoryService().calculate(
            **req.model_dump(),
            include_model_metadata=False,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        status_code = 404 if "Unknown store_id/item_id" in str(exc) else 422
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Inventory calculation failed due to an internal error.",
        ) from exc
