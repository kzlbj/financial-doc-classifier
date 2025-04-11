from typing import List, Optional

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.document import DocumentClassification
from app.schemas.document import DocumentClassificationCreate, DocumentClassification as DocumentClassificationSchema


class CRUDDocumentClassification(CRUDBase[DocumentClassification, DocumentClassificationCreate, DocumentClassificationSchema]):
    """文档分类CRUD操作类"""
    
    def create_with_document(
        self, db: Session, *, obj_in: DocumentClassificationCreate, document_id: int
    ) -> DocumentClassification:
        """创建文档分类记录"""
        obj_in_data = obj_in.dict()
        db_obj = DocumentClassification(**obj_in_data, document_id=document_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_by_document(
        self, db: Session, *, document_id: int
    ) -> List[DocumentClassification]:
        """获取文档的分类结果"""
        return (
            db.query(self.model)
            .filter(DocumentClassification.document_id == document_id)
            .all()
        )
    
    def get_latest_by_document(
        self, db: Session, *, document_id: int
    ) -> Optional[DocumentClassification]:
        """获取文档的最新分类结果"""
        return (
            db.query(self.model)
            .filter(DocumentClassification.document_id == document_id)
            .order_by(DocumentClassification.classified_at.desc())
            .first()
        )


document_classification = CRUDDocumentClassification(DocumentClassification) 