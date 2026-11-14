from pydantic import BaseModel,Field
class RegistryImport(BaseModel):
 # 每行逐份容错：档号/修订号/状态的具体校验在 registry_merge.normalize_rows 完成，
 # 无法解析的行进入“隔离”明细而不是让整次导入失败。
 rows:list[dict]=Field(min_length=1,max_length=20000)
