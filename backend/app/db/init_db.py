import logging
from sqlalchemy.orm import Session

from app import crud, schemas
from app.core.config import settings
from app.db.session import Base, engine


# 创建初始管理员用户
def create_initial_admin(db: Session) -> None:
    """
    创建初始管理员用户
    """
    user = crud.user.get_by_email(db, email="admin@example.com")
    if not user:
        user_in = schemas.UserCreate(
            email="admin@example.com",
            username="admin",
            password="admin123",  # 在生产环境中应使用强密码
            role="admin",
            is_active=True,
        )
        user = crud.user.create(db, obj_in=user_in)
        logging.info("Created initial admin user")


# 初始化 Elasticsearch 索引
def init_elasticsearch():
    """
    初始化 Elasticsearch 索引
    """
    from app.db.session import es_client
    
    # 检查索引是否存在
    if not es_client.indices.exists(index="finance_docs"):
        # 创建索引
        es_client.indices.create(
            index="finance_docs",
            body={
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "analysis": {
                        "analyzer": {
                            "default": {
                                "type": "standard"
                            },
                            "text_analyzer": {
                                "type": "custom",
                                "tokenizer": "standard",
                                "filter": ["lowercase", "stop"]
                            }
                        }
                    }
                },
                "mappings": {
                    "properties": {
                        "content": {
                            "type": "text",
                            "analyzer": "text_analyzer"
                        },
                        "filename": {
                            "type": "keyword"
                        },
                        "uploader_id": {
                            "type": "integer"
                        },
                        "upload_time": {
                            "type": "date"
                        },
                        "file_type": {
                            "type": "keyword"
                        },
                        "category": {
                            "type": "keyword"
                        },
                        "confidence": {
                            "type": "float"
                        }
                    }
                }
            }
        )
        logging.info("Created Elasticsearch index: finance_docs")


def init_db(db: Session) -> None:
    """
    初始化数据库
    """
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    logging.info("Created database tables")
    
    # 创建初始管理员用户
    create_initial_admin(db)
    
    # 初始化 Elasticsearch
    try:
        init_elasticsearch()
    except Exception as e:
        logging.error(f"Failed to initialize Elasticsearch: {e}")
        logging.warning("Elasticsearch initialization skipped. Some search features may not work properly.")
    
    logging.info("Database initialization complete") 