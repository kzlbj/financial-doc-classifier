from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.crud.base import CRUDBase
from app.models.document import DocumentUpload
from app.schemas.document import DocumentUploadCreate, DocumentUpload as DocumentUploadSchema


class CRUDDocument(CRUDBase[DocumentUpload, DocumentUploadCreate, DocumentUploadSchema]):
    """文档CRUD操作类"""
    
    def get_by_uploader(
        self, db: Session, *, uploader_id: int, skip: int = 0, limit: int = 100
    ) -> List[DocumentUpload]:
        """获取用户上传的文档"""
        return (
            db.query(self.model)
            .filter(DocumentUpload.uploader_id == uploader_id)
            .order_by(desc(DocumentUpload.upload_time))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_category(
        self, db: Session, *, category: str, skip: int = 0, limit: int = 100
    ) -> List[DocumentUpload]:
        """通过类别获取文档"""
        return (
            db.query(self.model)
            .join(self.model.classifications)
            .filter(self.model.classifications.any(category=category))
            .order_by(desc(DocumentUpload.upload_time))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_category_and_uploader(
        self, db: Session, *, category: str, uploader_id: int, skip: int = 0, limit: int = 100
    ) -> List[DocumentUpload]:
        """通过类别和上传者获取文档"""
        return (
            db.query(self.model)
            .join(self.model.classifications)
            .filter(
                self.model.classifications.any(category=category),
                DocumentUpload.uploader_id == uploader_id
            )
            .order_by(desc(DocumentUpload.upload_time))
            .offset(skip)
            .limit(limit)
            .all()
        )


document = CRUDDocument(DocumentUpload) 