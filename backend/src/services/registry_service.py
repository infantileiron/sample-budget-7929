from uuid import uuid4
from sqlalchemy import select
from fastapi import HTTPException
from ..models.lot import ArchiveLot
from ..models.registry import LotRegistry
from .registry_merge import merge_import

def get_or_none(db,lot_id):
 return db.scalar(select(LotRegistry).where(LotRegistry.lot_id==lot_id))

def require_lot(db,lot_id):
 lot=db.get(ArchiveLot,lot_id)
 if lot is None:raise HTTPException(404,"批次不存在")
 return lot

def import_registry(db,lot_id,body):
 require_lot(db,lot_id)
 registry=get_or_none(db,lot_id)
 existing=registry.entries if registry else []
 merged=merge_import(existing,body.rows)
 if registry is None:
  registry=LotRegistry(id=str(uuid4()),lot_id=lot_id,entries=[],quarantined=[],last_import={})
  db.add(registry)
 registry.entries=merged["entries"]
 # 隔离区累积保留：历次无法裁决的记录都留在隔离明细中并保留原因
 registry.quarantined=(registry.quarantined or [])+merged["quarantined"]
 registry.valid_count=merged["valid_count"]
 registry.void_count=merged["void_count"]
 registry.last_import={"counts":merged["counts"],"adopted":merged["adopted"],"ignored":merged["ignored"],"quarantined":merged["quarantined"]}
 db.commit();db.refresh(registry)
 return detail(db,lot_id)

def detail(db,lot_id):
 require_lot(db,lot_id)
 registry=get_or_none(db,lot_id)
 if registry is None:
  return {"lot_id":lot_id,"imported":False,"entries":[],"quarantined":[],"last_import":None,"valid_count":0,"void_count":0}
 return {"lot_id":lot_id,"imported":True,"entries":registry.entries,"quarantined":registry.quarantined,"last_import":registry.last_import,"valid_count":registry.valid_count,"void_count":registry.void_count}

def registry_map(db,lot_ids):
 """批量取底册：返回 {lot_id: LotRegistry|None}，未导入底册的批次为 None（沿用连续编号）。"""
 rows=db.scalars(select(LotRegistry).where(LotRegistry.lot_id.in_(lot_ids))).all()
 return {r.lot_id:r for r in rows}

def effective_size(db,lot):
 """单个批次参与容量/差错/抽样的有效档号数；未导入底册时回退到登记份数。"""
 registry=get_or_none(db,lot.id)
 if registry is None:return lot.size
 return registry.valid_count

def valid_archive_nos(registry):
 return [e["archive_no"] for e in registry.entries if e["status"]=="valid"]
