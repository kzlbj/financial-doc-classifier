from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class DocumentClassificationBase(BaseModel):
    category: str
    confidence: float
    model_version: str


class DocumentClassificationCreate(DocumentClassificationBase):
    pass


class DocumentClassification(DocumentClassificationBase):
    id: int
    document_id: int
    classified_at: datetime

    class Config:
        orm_mode = True


class DocumentUploadBase(BaseModel):
    filename: str
    file_type: str
    original_filename: str
    file_size: int
    upload_path: str


class DocumentUploadCreate(DocumentUploadBase):
    uploader_id: int


class DocumentUpload(DocumentUploadBase):
    id: int
    uploader_id: int
    upload_time: datetime
    classifications: List[DocumentClassification] = []

    class Config:
        orm_mode = True


class DocumentSearchResult(BaseModel):
    document_id: int
    score: float
    filename: str
    original_filename: str
    upload_time: datetime
    category: str
    confidence: float
    
    class Config:
        orm_mode = True


class AuditLogBase(BaseModel):
    user_id: int
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None


class AuditLogCreate(AuditLogBase):
    pass


class AuditLog(AuditLogBase):
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True 