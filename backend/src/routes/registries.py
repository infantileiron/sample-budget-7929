from fastapi import APIRouter,Depends
from ..config.database import get_db
from ..utils.auth import current,write_user
from ..schemas.registry import RegistryImport
from ..controllers import registry_controller as controller
router=APIRouter(prefix="/lots/{lot_id}/registry",tags=["lot-registry"])
@router.get("")
def detail(lot_id:str,db=Depends(get_db),user=Depends(current)):return controller.detail(db,lot_id)
@router.put("",status_code=200)
def import_registry(lot_id:str,body:RegistryImport,db=Depends(get_db),user=Depends(write_user)):return controller.import_registry(db,lot_id,body)
