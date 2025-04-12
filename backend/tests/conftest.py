import os
import sys
import pytest
from typing import Dict, Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.db.session import Base, get_db
from app.api.deps import get_current_admin_user, get_current_user
from app.models.user import User
from main import app


# 使用内存数据库进行测试
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 测试用的依赖覆盖
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# 模拟管理员用户
def override_get_current_admin_user():
    return User(
        id=1,
        email="admin@example.com",
        username="admin",
        hashed_password="hashed_password",
        role="admin",
        is_active=True
    )


# 模拟普通用户
def override_get_current_user():
    return User(
        id=2,
        email="user@example.com",
        username="user",
        hashed_password="hashed_password",
        role="viewer",
        is_active=True
    )


# 替换依赖
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_admin_user] = override_get_current_admin_user
app.dependency_overrides[get_current_user] = override_get_current_user


@pytest.fixture(scope="function")
def db() -> Generator:
    """每个测试函数使用的数据库会话"""
    # 创建数据库表
    Base.metadata.create_all(bind=engine)
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    # 清理测试数据
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client() -> Generator:
    """测试客户端"""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function")
def superuser_token_headers(client: TestClient) -> Dict[str, str]:
    """创建超级用户并获取token header"""
    return {"Authorization": f"Bearer {settings.SECRET_KEY}"}


@pytest.fixture(scope="function")
def normal_user_token_headers(client: TestClient) -> Dict[str, str]:
    """创建普通用户并获取token header"""
    return {"Authorization": f"Bearer {settings.SECRET_KEY}_user"} 