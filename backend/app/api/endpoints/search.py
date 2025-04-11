from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.services.audit_log import log_user_action
from app.services.search import search_documents
from app.db.session import redis_client

router = APIRouter()


@router.get("/", response_model=List[schemas.DocumentSearchResult])
def search(
    query: str = Query(..., description="搜索关键词"),
    category: str = Query(None, description="按类别筛选"),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    搜索文档
    """
    # 尝试从缓存获取结果
    cache_key = f"search:{query}:{category}:{current_user.id}"
    cached_results = redis_client.get(cache_key)
    
    if cached_results:
        # 记录审计日志
        log_user_action(
            db=db,
            user_id=current_user.id,
            action="search",
            details=f"用户搜索文档(缓存): {query}"
        )
        return cached_results.decode("utf-8")
    
    # 执行搜索
    results = search_documents(db, query, category, current_user)
    
    # 记录审计日志
    log_user_action(
        db=db,
        user_id=current_user.id,
        action="search",
        details=f"用户搜索文档: {query}"
    )
    
    # 缓存结果（5分钟）
    if results:
        redis_client.setex(cache_key, 300, str(results))
    
    return results


@router.get("/by-category", response_model=List[schemas.DocumentUpload])
def get_by_category(
    category: str = Query(..., description="文档类别"),
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    按类别获取文档
    """
    # 缓存键
    cache_key = f"category:{category}:{current_user.id}:{skip}:{limit}"
    cached_results = redis_client.get(cache_key)
    
    if cached_results:
        return cached_results.decode("utf-8")
    
    # 非管理员和分析师只能查看自己的文档
    if current_user.role in ["admin", "analyst"]:
        documents = crud.document.get_by_category(
            db, category=category, skip=skip, limit=limit
        )
    else:
        documents = crud.document.get_by_category_and_uploader(
            db, category=category, uploader_id=current_user.id, skip=skip, limit=limit
        )
    
    # 记录审计日志
    log_user_action(
        db=db,
        user_id=current_user.id,
        action="search",
        details=f"用户按类别查询文档: {category}"
    )
    
    # 缓存结果（5分钟）
    if documents:
        redis_client.setex(cache_key, 300, str(documents))
    
    return documents 