import math
from .hypergeometric import estimated_defects,minimum_sample,miss_probability
from .neyman import allocate

def calculate(lots,target,budget,void_lots=None):
 void_lots=void_lots or []
 strata={}
 for lot in lots:
  group=strata.setdefault(lot["stratum"],{"N":0,"D":0,"expected_errors":0.,"lot_count":0})
  # 容量与假设差错数均按有效档号计算；作废档号与断号不进入总体
  group["N"]+=lot["size"];group["D"]+=estimated_defects(lot["size"],lot["estimated_error_rate"]);group["expected_errors"]+=lot["size"]*lot["estimated_error_rate"];group["lot_count"]+=1
 for key,group in strata.items():
  group["stratum"]=key
  group["estimated_rate"]=group["expected_errors"]/group["N"] if group["N"]>0 else 0.
  group["minimum"]=minimum_sample(group["N"],group["D"],target) if group["N"]>0 else None
  group["weight"]=group["N"]*math.sqrt(group["estimated_rate"]*(1-group["estimated_rate"]))
 zero_strata=[k for k,g in strata.items() if g["N"]==0]
 impossible=[k for k,g in strata.items() if g["minimum"] is None and g["N"]>0]
 capacity=sum(g["N"] for g in strata.values())
 required=None if (impossible or zero_strata) else sum(g["minimum"] for g in strata.values())
 if capacity==0 and void_lots:
  reason="所选批次的逐份底册没有任何有效档号（全部作废或为空）："+"、".join(void_lots)
 elif zero_strata:
  reason="风险层 "+"、".join(zero_strata)+" 没有有效档号（相关批次全部作废或为空"+("："+"、".join(void_lots) if void_lots else "")+"），无法在该层抽样"
 elif impossible:
  reason="假设差错数D=0，非零检出目标不可达："+", ".join(impossible)
 elif budget<required:
  reason="预算低于各风险层目标检出率的精确最小样本量之和"
 elif budget>capacity:
  reason="预算超过所选档案有效总容量"
 else:
  reason=""
 result={"feasible":not bool(reason),"reason":reason,"required_budget":required,"budget":budget,"target":target,"capacity":capacity,"void_lots":void_lots,"strata":[strata[k] for k in sorted(strata)],"assumption":"每个风险层汇总所选批次的有效档号，D=sum ceil(N_lot*p_lot)，N仅计有效档号；目标按风险层判断，不保证每批分别达标。层内有效文档等概率、无放回抽取。作废档号与断号不进入总体。"}
 if reason:return result
 quotas,ideals=allocate({k:g["N"] for k,g in strata.items()},{k:g["weight"] for k,g in strata.items()},budget,{k:g["minimum"] for k,g in strata.items()})
 for key,group in strata.items():
  group["quota"]=quotas[key];group["ideal"]=ideals[key];group["miss_probability"]=miss_probability(group["N"],group["D"],quotas[key]);group["detection_probability"]=1-group["miss_probability"];group["guaranteed"]=group["D"]>0 and quotas[key]>group["N"]-group["D"]
 return result
