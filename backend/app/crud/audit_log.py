from typing import List, Optional
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.crud.base import CRUDBase
from app.models.document import AuditLog
from app.schemas.document import AuditLogCreate, AuditLog as AuditLogSchema


class CRUDAuditLog(CRUDBase[AuditLog, AuditLogCreate, AuditLogSchema]):
    """审计日志CRUD操作类"""
    
    def get_by_user(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[AuditLog]:
        """获取用户的审计日志"""
        return (
            db.query(self.model)
            .filter(AuditLog.user_id == user_id)
            .order_by(desc(AuditLog.timestamp))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_action(
        self, db: Session, *, action: str, skip: int = 0, limit: int = 100
    ) -> List[AuditLog]:
        """按操作类型获取审计日志"""
        return (
            db.query(self.model)
            .filter(AuditLog.action == action)
            .order_by(desc(AuditLog.timestamp))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_date_range(
        self, db: Session, *, start_date: datetime, end_date: datetime, skip: int = 0, limit: int = 100
    ) -> List[AuditLog]:
        """按日期范围获取审计日志"""
        return (
            db.query(self.model)
            .filter(AuditLog.timestamp >= start_date, AuditLog.timestamp <= end_date)
            .order_by(desc(AuditLog.timestamp))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_recent(
        self, db: Session, *, days: int = 7, skip: int = 0, limit: int = 100
    ) -> List[AuditLog]:
        """获取最近的审计日志"""
        recent_date = datetime.utcnow() - timedelta(days=days)
        return (
            db.query(self.model)
            .filter(AuditLog.timestamp >= recent_date)
            .order_by(desc(AuditLog.timestamp))
            .offset(skip)
            .limit(limit)
            .all()
        )


audit_log = CRUDAuditLog(AuditLog) 