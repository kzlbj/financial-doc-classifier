from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import uvicorn
from typing import List
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi

from app.api.routes import router as api_router
from app.core.config import settings
from app.core.security import SecurityHeadersMiddleware, CSRFMiddleware

app = FastAPI(
    title="金融文档分类器 API",
    description="用于分类金融文档的API系统",
    version="0.1.0",
    docs_url=None,  # 禁用默认的/docs路径
    redoc_url=None,  # 禁用默认的/redoc路径
    openapi_url="/api/openapi.json"  # API模式路径
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加会话中间件（用于CSRF保护）
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    max_age=3600,  # 1小时
)

# 限制主机头以防止Host头攻击
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=settings.ALLOWED_HOSTS
)

# 添加安全头中间件
app.add_middleware(SecurityHeadersMiddleware)

# 添加CSRF保护中间件
app.add_middleware(CSRFMiddleware)

# 包含API路由
app.include_router(api_router, prefix="/api")

# 自定义OpenAPI文档配置
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="金融文档分类器 API",
        version="0.1.0",
        description="""
        ## 金融文档分类器 API

        这个API系统提供了金融文档的分类、管理和搜索功能。

        ### 主要功能:
        * 用户认证与授权
        * 文档上传与分类
        * 文档搜索
        * 用户管理
        
        ### 安全特性:
        * JWT认证
        * CSRF保护
        * 角色授权控制
        """,
        routes=app.routes,
    )
    
    # 添加安全模式
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "输入JWT令牌: Bearer {token}"
        }
    }
    
    # 应用全局安全要求
    openapi_schema["security"] = [{"bearerAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# 自定义Swagger UI和ReDoc路由
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
    )

@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.0.0/bundles/redoc.standalone.js",
    )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 