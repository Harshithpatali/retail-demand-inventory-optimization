from fastapi import APIRouter
from api.services.business_service import BusinessService
router=APIRouter()
@router.get("/business")
def business(): return BusinessService().get()
