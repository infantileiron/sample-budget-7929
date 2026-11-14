from enum import StrEnum
class Role(StrEnum):
 ADMIN="admin"
 ANALYST="analyst"
 VIEWER="viewer"
class RunStatus(StrEnum):
 QUEUED="queued"
 RUNNING="running"
 COMPLETED="completed"
 INFEASIBLE="infeasible"
 FAILED="failed"
class Stratum(StrEnum):
 LOW="low"
 MODERATE="moderate"
 HIGH="high"
 CRITICAL="critical"
class RegistryStatus(StrEnum):
 VALID="valid"
 VOID="void"
 # 中文底册状态到枚举值的归一化映射
 @classmethod
 def normalize(cls,value):
  text=str(value).strip().lower()
  aliases={"有效":"valid","作废":"void","valid":"valid","void":"void","active":"valid","cancelled":"void","canceled":"void"}
  return cls(aliases[text]) if text in aliases else None
