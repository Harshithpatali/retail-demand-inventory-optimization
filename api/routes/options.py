from fastapi import APIRouter, HTTPException
from api.services.artifacts import ArtifactStore
router=APIRouter()
@router.get("/options")
def options():
    try:
        df=ArtifactStore().load_data(); pairs=df[["store_id","item_id"]].astype(str).drop_duplicates().sort_values(["store_id","item_id"]).to_dict("records"); return {"options":pairs}
    except (FileNotFoundError,ValueError) as exc: raise HTTPException(status_code=400,detail=str(exc))
    except Exception: raise HTTPException(status_code=500,detail="Options unavailable due to an internal error.")
