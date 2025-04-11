from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


# 共享属性
class UserBase(BaseModel):
    email: EmailStr
    username: str
    is_active: Optional[bool] = True
    role: Optional[str] = "viewer"


# 用于创建用户
class UserCreate(UserBase):
    password: str
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "testuser",
                "password": "securepassword",
                "role": "viewer"
            }
        }


# 用于更新用户
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None


# 从数据库返回的用户
class User(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "email": "user@example.com",
                "username": "testuser",
                "is_active": True,
                "role": "viewer",
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            }
        }


# 令牌
class Token(BaseModel):
    access_token: str
    token_type: str


# 令牌数据
class TokenPayload(BaseModel):
    sub: Optional[str] = None 