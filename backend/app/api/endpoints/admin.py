from typing import Any, List
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.services.audit_log import log_user_action
from app.core.config import settings

router = APIRouter()


@router.get("/audit-logs", response_model=List[schemas.AuditLog])
def get_audit_logs(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_admin_user),
    user_id: int = Query(None, description="按用户ID筛选"),
    action: str = Query(None, description="按操作类型筛选"),
    days: int = Query(7, description="最近的天数"),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    获取审计日志（仅限管理员）
    """
    # 记录审计日志
    log_user_action(
        db=db,
        user_id=current_user.id,
        action="view",
        resource_type="audit_logs",
        details="管理员查看审计日志"
    )
    
    # 根据筛选条件获取审计日志
    if user_id:
        logs = crud.audit_log.get_by_user(db, user_id=user_id, skip=skip, limit=limit)
    elif action:
        logs = crud.audit_log.get_by_action(db, action=action, skip=skip, limit=limit)
    else:
        logs = crud.audit_log.get_recent(db, days=days, skip=skip, limit=limit)
    
    return logs


@router.get("/stats/users", response_model=dict)
def get_user_stats(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    获取用户统计信息（仅限管理员）
    """
    # 获取总用户数
    total_users = db.query(models.User).count()
    
    # 获取活跃用户数
    active_users = db.query(models.User).filter(models.User.is_active == True).count()
    
    # 按角色分组统计
    role_counts = {}
    roles = ["admin", "analyst", "viewer"]
    for role in roles:
        role_counts[role] = db.query(models.User).filter(models.User.role == role).count()
    
    # 最近7天新增用户
    week_ago = datetime.utcnow() - timedelta(days=7)
    new_users = db.query(models.User).filter(models.User.created_at >= week_ago).count()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "by_role": role_counts,
        "new_users_last_7days": new_users
    }


@router.get("/stats/documents", response_model=dict)
def get_document_stats(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    获取文档统计信息（仅限管理员）
    """
    # 获取总文档数
    total_documents = db.query(models.DocumentUpload).count()
    
    # 按类型分组统计
    type_counts = {}
    file_types = ["pdf", "docx", "html"]
    for file_type in file_types:
        type_counts[file_type] = db.query(models.DocumentUpload).filter(
            models.DocumentUpload.file_type == file_type
        ).count()
    
    # 最近7天上传的文档
    week_ago = datetime.utcnow() - timedelta(days=7)
    new_documents = db.query(models.DocumentUpload).filter(
        models.DocumentUpload.upload_time >= week_ago
    ).count()
    
    # 按分类统计
    category_counts = {}
    categories = db.query(models.DocumentClassification.category).distinct().all()
    for category in categories:
        category_name = category[0]
        category_counts[category_name] = db.query(models.DocumentClassification).filter(
            models.DocumentClassification.category == category_name
        ).count()
    
    return {
        "total_documents": total_documents,
        "by_type": type_counts,
        "by_category": category_counts,
        "new_documents_last_7days": new_documents
    } 