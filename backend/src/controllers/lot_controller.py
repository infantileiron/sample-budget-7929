from sqlalchemy import select
from ..services import lot_service,registry_service
from ..models.lot import ArchiveLot
from ..models.registry import LotRegistry
from ..models.common import serialize
from .common import listing,require
def list_all(db):
 rows=listing(db,ArchiveLot)
 registries={r.lot_id:r for r in db.scalars(select(LotRegistry)).all()}
 for row in rows:
  registry=registries.get(row["id"])
  row["registry_imported"]=registry is not None
  row["valid_count"]=registry.valid_count if registry else row["size"]
  row["void_count"]=registry.void_count if registry else 0
 return rows
def detail(db,ident):return serialize(require(db,ArchiveLot,ident))
def create(db,body):return serialize(lot_service.create(db,body))
