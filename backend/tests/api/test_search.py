import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.models.document import DocumentUpload, DocumentClassification
from app.schemas.document import DocumentUploadCreate, DocumentClassificationCreate


def test_search_documents(client: TestClient, normal_user_token_headers: dict) -> None:
    """测试搜索文档"""
    # 模拟search_documents函数的返回值
    with patch("app.services.search.search_documents") as mock_search:
        mock_search.return_value = [
            {
                "document_id": 1,
                "score": 0.95,
                "filename": "test.pdf",
                "original_filename": "test.pdf",
                "upload_time": "2023-01-01T00:00:00",
                "category": "财务报告",
                "confidence": 0.92
            }
        ]
        
        response = client.get(
            "/api/search/?query=财务报告", 
            headers=normal_user_token_headers
        )
        
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["category"] == "财务报告"


def test_search_documents_with_category(client: TestClient, normal_user_token_headers: dict) -> None:
    """测试按类别过滤搜索文档"""
    # 模拟search_documents函数的返回值
    with patch("app.services.search.search_documents") as mock_search:
        mock_search.return_value = [
            {
                "document_id": 1,
                "score": 0.95,
                "filename": "test.pdf",
                "original_filename": "test.pdf",
                "upload_time": "2023-01-01T00:00:00",
                "category": "财务报告",
                "confidence": 0.92
            }
        ]
        
        response = client.get(
            "/api/search/?query=财务报告&category=财务报告", 
            headers=normal_user_token_headers
        )
        
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["category"] == "财务报告"
        # 验证mock函数被正确调用，传入了类别参数
        mock_search.assert_called_once()
        args, kwargs = mock_search.call_args
        assert kwargs["category"] == "财务报告"


def test_search_by_category(client: TestClient, db: Session, normal_user_token_headers: dict) -> None:
    """测试按类别获取文档"""
    # 创建测试文档
    document_in = DocumentUploadCreate(
        filename="test.pdf",
        file_type="pdf",
        original_filename="test.pdf",
        file_size=1024,
        upload_path="/tmp/test.pdf",
        uploader_id=2  # 普通用户ID
    )
    document = crud.document.create(db, obj_in=document_in)
    
    # 创建分类结果
    classification_in = DocumentClassificationCreate(
        category="财务报告",
        confidence=0.95,
        model_version="0.1.0"
    )
    classification = crud.document_classification.create_with_document(
        db, obj_in=classification_in, document_id=document.id
    )
    
    # 模拟Redis get方法返回None，表示缓存未命中
    with patch("app.db.session.redis_client.get", return_value=None):
        # 模拟Redis setex方法
        with patch("app.db.session.redis_client.setex"):
            response = client.get(
                "/api/search/by-category?category=财务报告", 
                headers=normal_user_token_headers
            )
            
            assert response.status_code == 200 