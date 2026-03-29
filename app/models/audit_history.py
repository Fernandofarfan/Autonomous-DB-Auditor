from sqlalchemy import Column, Integer, String, Text, DateTime
import datetime
from app.core.database import Base

class AuditRecord(Base):
    __tablename__ = "audit_records"
    
    id = Column(Integer, primary_key=True, index=True)
    engine = Column(String, index=True)
    category = Column(String)
    severity = Column(String)
    description = Column(Text)
    remediation_sql = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
