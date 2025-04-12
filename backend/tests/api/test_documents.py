import pytest
import os
import tempfile
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.models.document import DocumentUpload
from app.schemas.document import DocumentUploadCreate


@pytest.fixture
def temp_pdf_file():
    """创建临时PDF文件用于测试"""
    content = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp:
        temp.write(content)
        temp_path = temp.name
    
    yield temp_path
    
    # 清理临时文件
    if os.path.exists(temp_path):
        os.remove(temp_path)


def test_get_documents_empty(client: TestClient, normal_user_token_headers: dict) -> None:
    """测试获取空文档列表"""
    response = client.get("/api/documents/", headers=normal_user_token_headers)
    
    assert response.status_code == 200
    assert response.json() == []


def test_get_documents(client: TestClient, db: Session, normal_user_token_headers: dict) -> None:
    """测试获取文档列表"""
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
    
    response = client.get("/api/documents/", headers=normal_user_token_headers)
    
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["filename"] == "test.pdf"


def test_get_document_by_id(client: TestClient, db: Session, normal_user_token_headers: dict) -> None:
    """测试通过ID获取文档"""
    # 创建测试文档
    document_in = DocumentUploadCreate(
        filename="test2.pdf",
        file_type="pdf",
        original_filename="test2.pdf",
        file_size=1024,
        upload_path="/tmp/test2.pdf",
        uploader_id=2  # 普通用户ID
    )
    document = crud.document.create(db, obj_in=document_in)
    
    response = client.get(f"/api/documents/{document.id}", headers=normal_user_token_headers)
    
    assert response.status_code == 200
    assert response.json()["filename"] == "test2.pdf"


def test_get_nonexistent_document(client: TestClient, normal_user_token_headers: dict) -> None:
    """测试获取不存在的文档"""
    response = client.get("/api/documents/999", headers=normal_user_token_headers)
    
    assert response.status_code == 404
    assert "detail" in response.json()


def test_delete_document(client: TestClient, db: Session, normal_user_token_headers: dict) -> None:
    """测试删除文档"""
    # 创建测试文档
    document_in = DocumentUploadCreate(
        filename="to_delete.pdf",
        file_type="pdf",
        original_filename="to_delete.pdf",
        file_size=1024,
        upload_path="/tmp/to_delete.pdf",
        uploader_id=2  # 普通用户ID
    )
    document = crud.document.create(db, obj_in=document_in)
    
    # 创建空文件以便删除
    with open(document.upload_path, "w") as f:
        f.write("dummy content")
    
    response = client.delete(f"/api/documents/{document.id}", headers=normal_user_token_headers)
    
    assert response.status_code == 200
    assert response.json()["filename"] == "to_delete.pdf"
    
    # 确认文档已从数据库删除
    deleted_doc = crud.document.get(db, id=document.id)
    assert deleted_doc is None 