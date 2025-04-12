import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.user import UserCreate


def test_login_access_token(client: TestClient, db: Session) -> None:
    """测试登录获取token"""
    # 创建测试用户
    user_in = UserCreate(
        email="test@example.com",
        username="testuser",
        password="testpassword",
        role="viewer"
    )
    user = crud.user.create(db, obj_in=user_in)
    
    login_data = {
        "username": "test@example.com",
        "password": "testpassword"
    }
    
    response = client.post("/api/auth/login", data=login_data)
    tokens = response.json()
    
    assert response.status_code == 200
    assert "access_token" in tokens
    assert tokens["token_type"] == "bearer"


def test_login_incorrect_password(client: TestClient, db: Session) -> None:
    """测试密码错误的情况"""
    # 创建测试用户
    user_in = UserCreate(
        email="test2@example.com",
        username="testuser2",
        password="testpassword",
        role="viewer"
    )
    user = crud.user.create(db, obj_in=user_in)
    
    login_data = {
        "username": "test2@example.com",
        "password": "wrongpassword"
    }
    
    response = client.post("/api/auth/login", data=login_data)
    
    assert response.status_code == 401
    assert "detail" in response.json()


def test_login_nonexistent_user(client: TestClient) -> None:
    """测试不存在的用户登录"""
    login_data = {
        "username": "nonexistent@example.com",
        "password": "testpassword"
    }
    
    response = client.post("/api/auth/login", data=login_data)
    
    assert response.status_code == 401
    assert "detail" in response.json()


def test_logout(client: TestClient, normal_user_token_headers: dict) -> None:
    """测试用户登出"""
    response = client.post("/api/auth/logout", headers=normal_user_token_headers)
    
    assert response.status_code == 200
    assert response.json() == {"msg": "登出成功"} 