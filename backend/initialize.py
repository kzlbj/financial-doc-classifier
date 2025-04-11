import logging
import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.db.session import SessionLocal
from app.db.init_db import init_db


def init() -> None:
    """
    初始化应用程序数据库和依赖
    """
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    # 创建上传目录
    os.makedirs("uploads", exist_ok=True)
    logging.info("Created uploads directory")
    
    # 创建模型目录
    os.makedirs("app/ml/models", exist_ok=True)
    logging.info("Created models directory")
    
    # 初始化数据库
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()


if __name__ == "__main__":
    logging.info("Initializing application...")
    init()
    logging.info("Initialization complete") 