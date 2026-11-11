from fastapi import APIRouter, HTTPException

from api.schemas.inventory import InventoryRequest, InventoryResponse
from api.services.inventory_service import InventoryService

router = APIRouter()


@router.post("/inventory", response_model=InventoryResponse)
def inventory(req: InventoryRequest):
    try:
        # Inventory policy uses observed demand statistics; loading the
        # forecasting model artifact here is unnecessary.
        return InventoryService().calculate(
            **req.model_dump(),
            include_model_metadata=False,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Inventory calculation failed due to an internal error.",
        )
