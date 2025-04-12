from datetime import datetime, timedelta
from typing import Any, Union, Dict, Optional

from jose import jwt
from passlib.context import CryptContext
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import secrets
import string

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    """
    创建JWT访问令牌
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码是否匹配哈希值
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    获取密码的哈希值
    """
    return pwd_context.hash(password)


def generate_random_password(length: int = 12) -> str:
    """
    生成随机强密码
    """
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    添加安全相关的HTTP头
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        
        if settings.SECURITY_HEADERS:
            # 防止点击劫持
            response.headers["X-Frame-Options"] = "DENY"
            # XSS保护
            response.headers["X-XSS-Protection"] = "1; mode=block"
            # 防止MIME类型嗅探
            response.headers["X-Content-Type-Options"] = "nosniff"
            # 引用策略
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            # 内容安全策略 (CSP)
            response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data:; script-src 'self'; style-src 'self'; font-src 'self'; frame-ancestors 'none'; form-action 'self'"
            # HTTP严格传输安全 (HSTS)
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            # 权限策略
            response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
            
        return response


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF保护中间件
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        # 跳过GET, HEAD, OPTIONS and TRACE请求
        if request.method in ("GET", "HEAD", "OPTIONS", "TRACE"):
            return await call_next(request)
            
        # 检查CSRF token
        token_in_header = request.headers.get("X-CSRF-Token")
        token_in_cookies = request.cookies.get("csrf_token")
        
        if not token_in_cookies or not token_in_header or token_in_cookies != token_in_header:
            return Response(
                content={"detail": "CSRF令牌无效或缺失"},
                status_code=403,
            )
            
        return await call_next(request)


def create_csrf_token() -> str:
    """
    创建CSRF令牌
    """
    return secrets.token_hex(32) 