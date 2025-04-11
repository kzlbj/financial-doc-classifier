from fastapi import APIRouter

from app.api.endpoints import users, auth, documents, search, admin

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["认证"])
router.include_router(users.router, prefix="/users", tags=["用户"])
router.include_router(documents.router, prefix="/documents", tags=["文档"])
router.include_router(search.router, prefix="/search", tags=["搜索"])
router.include_router(admin.router, prefix="/admin", tags=["管理员"]) 