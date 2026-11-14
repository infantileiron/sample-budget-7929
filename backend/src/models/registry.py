from sqlalchemy import String,JSON,ForeignKey,Integer
from sqlalchemy.orm import Mapped,mapped_column
from .common import RecordMixin
from ..config.database import Base
class LotRegistry(RecordMixin,Base):
 __tablename__="lot_registries"
 lot_id:Mapped[str]=mapped_column(ForeignKey("lots.id"),unique=True)
 # 当前生效的逐份条目：[{archive_no,revision,status}]，按档号排序，仅含每个档号的最高修订
 entries:Mapped[list]=mapped_column(JSON,default=list)
 # 同版状态矛盾等无法自动裁决的原始行，永久隔离并保留原因
 quarantined:Mapped[list]=mapped_column(JSON,default=list)
 # 最近一次导入的三类明细（采用/忽略/隔离）及计数，供导入页复核
 last_import:Mapped[dict]=mapped_column(JSON,default=dict)
 valid_count:Mapped[int]=mapped_column(Integer,default=0)
 void_count:Mapped[int]=mapped_column(Integer,default=0)
