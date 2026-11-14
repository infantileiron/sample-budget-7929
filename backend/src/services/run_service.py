from uuid import uuid4
from fastapi import HTTPException
from ..models.run import AllocationRun
from ..models.plan import SamplingPlan
from ..models.lot import ArchiveLot
from ..utils.queue import enqueue
from .allocation import calculate
from .draw_service import generate
from . import registry_service

def create(db,body):
 if not db.get(SamplingPlan,body.plan_id):raise HTTPException(422,"抽样计划不存在")
 row=AllocationRun(id=str(uuid4()),plan_id=body.plan_id,status="queued",result={},error="");db.add(row);db.commit()
 try:enqueue(row.id)
 except Exception:
  row.status="failed";row.error="Redis队列不可用，请重试";db.commit();raise HTTPException(503,row.error)
 return row

def compute(db,run_id):
 row=db.get(AllocationRun,run_id)
 if row is None or row.status not in ["queued","running"]:return
 row.status="running";db.commit()
 try:
  plan=db.get(SamplingPlan,row.plan_id);lots=[db.get(ArchiveLot,i) for i in plan.lot_ids]
  registries=registry_service.registry_map(db,plan.lot_ids)
  lot_payload,void_lots=[],[]
  for lot in lots:
   registry=registries.get(lot.id)
   if registry is None:
    effective=lot.size # 未导入逐份底册的老批次：沿用登记份数与连续编号
   else:
    effective=registry.valid_count
    if effective==0:void_lots.append(lot.name)
   lot_payload.append({"id":lot.id,"stratum":lot.stratum,"size":effective,"estimated_error_rate":lot.estimated_error_rate,"declared_size":lot.size})
  result=calculate(lot_payload,plan.target_detection,plan.budget,void_lots=void_lots)
  row.result={**result,"plan_name":plan.name,"seed":plan.seed};row.status="completed" if result["feasible"] else "infeasible";db.commit()
  if result["feasible"]:generate(db,row)
 except Exception as e:
  db.rollback();row=db.get(AllocationRun,run_id);row.status="failed";row.error=str(e)[:1000];db.commit()
