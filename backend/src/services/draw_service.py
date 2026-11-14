import random
from uuid import uuid4
from sqlalchemy import select
from fastapi import HTTPException
from ..models.draw import SampleDraw
from ..models.run import AllocationRun
from ..models.plan import SamplingPlan
from ..models.lot import ArchiveLot
from . import registry_service

def _population_for_lot(lot,registry):
 """返回该批次进入抽样总体的文档行。

 已导入逐份底册：仅状态为有效的档号，档号即文档编号，断号与作废档号自然缺席。
 未导入底册的老批次：沿用 PREFIX-00001 起的连续编号。
 """
 base={"lot_id":lot.id,"lot_name":lot.name,"stratum":lot.stratum}
 if registry is None:
  return [dict(base,document_id=lot.doc_prefix+"-"+str(i+1).zfill(5)) for i in range(lot.size)]
 return [dict(base,document_id=archive_no) for archive_no in registry_service.valid_archive_nos(registry)]

def manifest(lot_records,strata,seed):
 rng=random.Random(seed);rows=[]
 for layer in sorted(strata,key=lambda x:x["stratum"]):
  population=[]
  for lot in sorted(lot_records,key=lambda x:x["id"]):
   if lot["stratum"]==layer["stratum"]:
    population.extend(_population_for_lot(lot["lot"],lot["registry"]))
  rows.extend(rng.sample(population,layer["quota"]))
 return [dict(row,position=i+1) for i,row in enumerate(rows)]

def generate(db,run):
 existing=db.scalar(select(SampleDraw).where(SampleDraw.run_id==run.id))
 if existing:return existing
 if run.status!="completed" or not run.result.get("feasible"):raise HTTPException(409,"仅预算可行且已完成的运行可生成抽样")
 plan=db.get(SamplingPlan,run.plan_id);lots=[db.get(ArchiveLot,i) for i in plan.lot_ids]
 registries=registry_service.registry_map(db,plan.lot_ids)
 lot_records=[{"id":l.id,"stratum":l.stratum,"lot":l,"registry":registries.get(l.id)} for l in lots]
 row=SampleDraw(id=str(uuid4()),run_id=run.id,seed=plan.seed,manifest=manifest(lot_records,run.result["strata"],plan.seed));db.add(row);db.commit();return row

def create(db,body):
 run=db.get(AllocationRun,body.run_id)
 if not run:raise HTTPException(404,"运行不存在")
 return generate(db,run)
