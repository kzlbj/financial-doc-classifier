from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# MongoDB连接
from pymongo import MongoClient

mongo_client = MongoClient(settings.MONGODB_URL)
mongo_db = mongo_client.get_database()

# Elasticsearch连接
from elasticsearch import Elasticsearch

es_client = Elasticsearch(settings.ELASTICSEARCH_URL)

# Redis连接
import redis

redis_client = redis.Redis.from_url(settings.REDIS_URL)

# RabbitMQ连接
import pika

def get_rabbitmq_connection():
    """获取RabbitMQ连接"""
    parameters = pika.URLParameters(settings.RABBITMQ_URL)
    return pika.BlockingConnection(parameters)


def get_db():
    """
    获取数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 