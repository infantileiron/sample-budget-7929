"""逐份底册导入的确定性合并规则（不依赖数据库，便于独立验证）。

规则：
- 同一档号只保留最高修订号；迟到旧版记录与重复报送不改变结果，记为“忽略”。
- 同一档号同一修订号出现相互矛盾的状态（既有效又作废）时，仅这些同版记录隔离留因，
  不写入生效条目；该档号其余不冲突修订仍按最高修订规则处理。
- 高修订号记录可覆盖低修订号，因此作废档案可被更高修订的有效记录恢复。
- 容量、差错数估计与抽样一律以状态为有效（valid）的档号为准。
"""
from ..constants.enums import RegistryStatus

REVISION_MIN=0
REVISION_MAX=10**6
ARCHIVE_NO_MAX=120

def _row_ref(index):
 return f"第{index}行" if index is not None else "未知行"

def normalize_rows(rows):
 """把外部行（中文或英文字段）校验并归一化为 (payload, error) 列表。"""
 normalized=[]
 for i,raw in enumerate(rows,start=1):
  if not isinstance(raw,dict):
   normalized.append((None,{"row":i,"archive_no":"","revision":None,"status":"","reason":f"{_row_ref(i)}：记录格式不是对象"}));continue
  archive_no=str(raw.get("archive_no",raw.get("档号",""))).strip()
  rev_raw=raw.get("revision",raw.get("修订号",None))
  status_raw=raw.get("status",raw.get("状态",raw.get("有效或作废状态","")))
  if not archive_no:
   normalized.append((None,{"row":i,"archive_no":"","revision":None,"status":"","reason":f"{_row_ref(i)}：档号为空"}));continue
  if len(archive_no)>ARCHIVE_NO_MAX:
   normalized.append((None,{"row":i,"archive_no":archive_no,"revision":None,"status":"","reason":f"{_row_ref(i)}：档号超过{ARCHIVE_NO_MAX}字符"}));continue
  try:revision=int(rev_raw)
  except (TypeError,ValueError):
   normalized.append((None,{"row":i,"archive_no":archive_no,"revision":None,"status":"","reason":f"{_row_ref(i)}：修订号须为整数，收到 {rev_raw!r}"}));continue
  if not REVISION_MIN<=revision<=REVISION_MAX:
   normalized.append((None,{"row":i,"archive_no":archive_no,"revision":revision,"status":"","reason":f"{_row_ref(i)}：修订号超出允许范围"}));continue
  status=RegistryStatus.normalize(status_raw)
  if status is None:
   normalized.append((None,{"row":i,"archive_no":archive_no,"revision":revision,"status":"","reason":f"{_row_ref(i)}：状态须为“有效/valid”或“作废/void”，收到 {status_raw!r}"}));continue
  normalized.append(({"row":i,"archive_no":archive_no,"revision":revision,"status":str(status)},None))
 return normalized

def merge_import(existing_entries,incoming_rows):
 """合并一次导入。

 existing_entries: 既有生效条目 [{archive_no,revision,status}]
 incoming_rows: 原始外部行列表
 返回 dict：entries（新的生效条目）、adopted/ignored/quarantined 三类明细、计数与原因。
 """
 adopted,ignored,quarantined=[],[],[]
 # 以档号为键复制既有结果，保证隔离记录不污染已生效数据
 current={e["archive_no"]:dict(e) for e in existing_entries}
 valid_payloads=[]
 for payload,error in normalize_rows(incoming_rows):
  if error:quarantined.append(error)
  else:valid_payloads.append(payload)
 # 本次报送内部先按档号归组；仅真正矛盾的同版记录进入隔离，
 # 该档号其余不冲突修订仍按最高修订规则正常处理（高版本可照常恢复）。
 groups={}
 for payload in valid_payloads:groups.setdefault(payload["archive_no"],[]).append(payload)
 conflict_rows=set()
 for archive_no,batch in groups.items():
  rev_status={}
  for payload in batch:rev_status.setdefault(payload["revision"],set()).add(payload["status"])
  conflicts=[rev for rev,states in rev_status.items() if len(states)>1]
  if not conflicts:continue
  for payload in batch:
   if payload["revision"] in conflicts:
    conflict_rows.add(payload["row"])
    quarantined.append({"row":payload["row"],"archive_no":archive_no,"revision":payload["revision"],"status":payload["status"],"reason":f"档号 {archive_no} 修订号 {payload['revision']} 同时报送有效与作废，同版状态矛盾，隔离留因待人工核实"})
 # 再逐条应用非矛盾记录
 for archive_no,batch in groups.items():
  seen=set()  # 同档号同修订同状态的重复报送：第一条采用，其余忽略
  for payload in sorted(batch,key=lambda p:(p["revision"],p["row"])):
   if payload["row"] in conflict_rows:continue
   key=(payload["revision"],payload["status"])
   prior=current.get(archive_no)
   if key in seen:
    ignored.append({"row":payload["row"],"archive_no":archive_no,"revision":payload["revision"],"status":payload["status"],"reason":"重复报送：与本次已处理记录完全相同，不改变结果"})
    continue
   seen.add(key)
   if prior is not None and payload["revision"]<prior["revision"]:
    ignored.append({"row":payload["row"],"archive_no":archive_no,"revision":payload["revision"],"status":payload["status"],"reason":f"迟到旧版：当前最高修订为 {prior['revision']}，修订号 {payload['revision']} 不改变结果"})
    continue
   if prior is not None and payload["revision"]==prior["revision"] and payload["status"]==prior["status"]:
    ignored.append({"row":payload["row"],"archive_no":archive_no,"revision":payload["revision"],"status":payload["status"],"reason":"重复报送：与底册现有最高修订记录一致，不改变结果"})
    continue
   # 更高修订（含首次见到的修订）采用
   revived=prior is not None and prior["status"]=="void" and payload["status"]=="valid" and payload["revision"]>prior["revision"]
   reason="高版本恢复作废档案" if revived else ("首次登记档号" if prior is None else f"高版本覆盖修订 {prior['revision']}")
   current[archive_no]={"archive_no":archive_no,"revision":payload["revision"],"status":payload["status"]}
   adopted.append({"row":payload["row"],"archive_no":archive_no,"revision":payload["revision"],"status":payload["status"],"reason":reason})
 entries=sorted((current[a] for a in current),key=lambda e:e["archive_no"])
 valid_count=sum(1 for e in entries if e["status"]=="valid")
 void_count=len(entries)-valid_count
 total=len(incoming_rows)
 counts={"input":total,"adopted":len(adopted),"ignored":len(ignored),"quarantined":len(quarantined)}
 assert counts["adopted"]+counts["ignored"]+counts["quarantined"]==total,"三类明细数量之和必须等于输入行数"
 return {"entries":entries,"adopted":adopted,"ignored":ignored,"quarantined":quarantined,"counts":counts,"valid_count":valid_count,"void_count":void_count}
