import os
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.services.audit_log import log_user_action
from app.services.document_processor import process_document
from app.services.rabbitmq_tasks import submit_document_for_processing
from app.core.config import settings

router = APIRouter()


@router.post("/upload", response_model=schemas.DocumentUpload)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    上传文档进行分类
    """
    # 检查文件类型
    filename = file.filename
    file_extension = os.path.splitext(filename)[1].lower()
    
    if file_extension not in [".pdf", ".docx", ".html"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不支持的文件格式，仅支持PDF、DOCX和HTML格式"
        )
    
    # 创建上传路径
    upload_dir = os.path.join("uploads", str(current_user.id))
    os.makedirs(upload_dir, exist_ok=True)
    
    # 保存文件
    file_path = os.path.join(upload_dir, filename)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    # 确定文件类型
    if file_extension == ".pdf":
        file_type = "pdf"
    elif file_extension == ".docx":
        file_type = "docx"
    elif file_extension == ".html":
        file_type = "html"
    else:
        file_type = "unknown"
    
    # 创建文档记录
    document_in = schemas.DocumentUploadCreate(
        filename=filename,
        file_type=file_type,
        original_filename=filename,
        file_size=len(content),
        upload_path=file_path,
        uploader_id=current_user.id
    )
    document = crud.document.create(db, obj_in=document_in)
    
    # 记录审计日志
    log_user_action(
        db=db,
        user_id=current_user.id,
        action="upload",
        resource_type="document",
        resource_id=document.id,
        details=f"用户上传文档: {filename}"
    )
    
    # 在后台处理文档分类
    background_tasks.add_task(
        submit_document_for_processing,
        document_id=document.id,
        file_path=file_path,
        file_type=file_type
    )
    
    return document


@router.get("/{document_id}", response_model=schemas.DocumentUpload)
def get_document(
    document_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    获取文档信息
    """
    document = crud.document.get(db, id=document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在"
        )
    
    # 检查权限
    if document.uploader_id != current_user.id and current_user.role not in ["admin", "analyst"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问该文档"
        )
    
    return document


@router.get("/", response_model=List[schemas.DocumentUpload])
def get_documents(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    获取文档列表
    """
    # 普通用户只能看自己的文档，管理员和分析师可以看所有文档
    if current_user.role in ["admin", "analyst"]:
        documents = crud.document.get_multi(db, skip=skip, limit=limit)
    else:
        documents = crud.document.get_by_uploader(
            db, uploader_id=current_user.id, skip=skip, limit=limit
        )
    
    return documents


@router.delete("/{document_id}", response_model=schemas.DocumentUpload)
def delete_document(
    document_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    删除文档
    """
    document = crud.document.get(db, id=document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在"
        )
    
    # 检查权限
    if document.uploader_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除该文档"
        )
    
    # 删除文件
    try:
        os.remove(document.upload_path)
    except OSError:
        pass  # 文件可能已经不存在
    
    # 删除数据库记录
    document = crud.document.remove(db, id=document_id)
    
    # 记录审计日志
    log_user_action(
        db=db,
        user_id=current_user.id,
        action="delete",
        resource_type="document",
        resource_id=document_id,
        details=f"用户删除文档: {document.filename}"
    )
    
    return document 