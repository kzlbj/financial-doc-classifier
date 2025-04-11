from typing import Optional
from sqlalchemy.orm import Session

from app import crud, schemas


def log_user_action(
    db: Session,
    user_id: int,
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[int] = None,
    details: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> None:
    """
    记录用户操作的审计日志
    
    参数:
        db: 数据库会话
        user_id: 用户ID
        action: 操作类型，如 "login", "upload", "search", "delete" 等
        resource_type: 资源类型，如 "user", "document" 等
        resource_id: 资源ID
        details: 详细信息
        ip_address: IP地址
    """
    log_in = schemas.AuditLogCreate(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address
    )
    
    crud.audit_log.create(db, obj_in=log_in) 