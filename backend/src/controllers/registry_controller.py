from ..services import registry_service
from ..schemas.registry import RegistryImport

def detail(db,lot_id):return registry_service.detail(db,lot_id)
def import_registry(db,lot_id,body:RegistryImport):return registry_service.import_registry(db,lot_id,body)
