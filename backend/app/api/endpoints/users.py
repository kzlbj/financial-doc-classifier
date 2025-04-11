from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.services.audit_log import log_user_action

router = APIRouter()


@router.post("/", response_model=schemas.User)
def create_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserCreate,
    current_user: models.User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    创建用户（仅限管理员）
    """
    user = crud.user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱已经被注册",
        )
    user = crud.user.create(db, obj_in=user_in)
    
    # 记录审计日志
    log_user_action(
        db=db,
        user_id=current_user.id,
        action="create",
        resource_type="user",
        resource_id=user.id,
        details=f"管理员创建用户: {user.username}"
    )
    
    return user


@router.get("/me", response_model=schemas.User)
def read_user_me(
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    获取当前用户信息
    """
    return current_user


@router.put("/me", response_model=schemas.User)
def update_user_me(
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    更新当前用户信息
    """
    user = crud.user.update(db, db_obj=current_user, obj_in=user_in)
    
    # 记录审计日志
    log_user_action(
        db=db,
        user_id=current_user.id,
        action="update",
        resource_type="user",
        resource_id=current_user.id,
        details="用户更新了个人信息"
    )
    
    return user


@router.get("/{user_id}", response_model=schemas.User)
def read_user_by_id(
    user_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    通过ID获取用户信息
    """
    user = crud.user.get(db, id=user_id)
    if user == current_user:
        return user
    if not current_user.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足",
        )
    return user


@router.get("/", response_model=List[schemas.User])
def read_users(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    获取用户列表（仅限管理员）
    """
    users = crud.user.get_multi(db, skip=skip, limit=limit)
    return users 