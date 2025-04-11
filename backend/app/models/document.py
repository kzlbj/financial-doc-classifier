from datetime import datetime
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Text, Enum, Float
from sqlalchemy.orm import relationship

from app.db.session import Base


class DocumentUpload(Base):
    """文档上传记录模型"""
    __tablename__ = "document_uploads"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_type = Column(Enum("pdf", "docx", "html", name="file_type"), nullable=False)
    original_filename = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)  # 以字节为单位
    upload_path = Column(String, nullable=False)
    uploader_id = Column(Integer, ForeignKey("users.id"))
    upload_time = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    uploader = relationship("User", back_populates="document_uploads")
    classifications = relationship("DocumentClassification", back_populates="document")


class DocumentClassification(Base):
    """文档分类结果模型"""
    __tablename__ = "document_classifications"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("document_uploads.id"))
    category = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    classified_at = Column(DateTime, default=datetime.utcnow)
    model_version = Column(String, nullable=False)
    
    # 关系
    document = relationship("DocumentUpload", back_populates="classifications")


class AuditLog(Base):
    """审计日志模型"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String, nullable=False)  # 如 "upload", "classify", "search", "login", etc.
    resource_type = Column(String, nullable=True)  # 如 "document", "user", etc.
    resource_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    user = relationship("User") 