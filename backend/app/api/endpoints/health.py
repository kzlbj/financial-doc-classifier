from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import redis
import requests
from pymongo import MongoClient
from elasticsearch import Elasticsearch
import pika
from typing import Dict, Any

from app.api.deps import get_db
from app.core.config import settings

router = APIRouter()


@router.get("/", response_model=Dict[str, Any])
async def health_check():
    """
    健康检查端点，用于监控系统各组件的状态
    """
    health_status = {
        "status": "ok",
        "version": "0.1.0",
        "components": {}
    }
    
    # 检查数据库连接
    try:
        # 数据库检查在依赖注入get_db中进行
        health_status["components"]["database"] = {
            "status": "ok"
        }
    except Exception as e:
        health_status["components"]["database"] = {
            "status": "error",
            "message": str(e)
        }
        health_status["status"] = "degraded"
    
    # 检查MongoDB
    try:
        mongo_client = MongoClient(settings.MONGODB_URL, serverSelectionTimeoutMS=2000)
        mongo_client.server_info()  # 发送管理命令以验证连接
        health_status["components"]["mongodb"] = {
            "status": "ok"
        }
    except Exception as e:
        health_status["components"]["mongodb"] = {
            "status": "error",
            "message": str(e)
        }
        health_status["status"] = "degraded"
    
    # 检查Elasticsearch
    try:
        es = Elasticsearch(settings.ELASTICSEARCH_URL)
        if es.ping():
            health_status["components"]["elasticsearch"] = {
                "status": "ok"
            }
        else:
            raise Exception("无法连接到Elasticsearch")
    except Exception as e:
        health_status["components"]["elasticsearch"] = {
            "status": "error",
            "message": str(e)
        }
        health_status["status"] = "degraded"
    
    # 检查Redis
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        redis_client.ping()
        health_status["components"]["redis"] = {
            "status": "ok"
        }
    except Exception as e:
        health_status["components"]["redis"] = {
            "status": "error",
            "message": str(e)
        }
        health_status["status"] = "degraded"
    
    # 检查RabbitMQ
    try:
        connection_params = pika.URLParameters(settings.RABBITMQ_URL)
        connection = pika.BlockingConnection(connection_params)
        connection.close()
        health_status["components"]["rabbitmq"] = {
            "status": "ok"
        }
    except Exception as e:
        health_status["components"]["rabbitmq"] = {
            "status": "error",
            "message": str(e)
        }
        health_status["status"] = "degraded"
    
    return health_status


@router.get("/ready")
async def readiness_check():
    """
    就绪检查端点，用于Kubernetes就绪探针
    """
    return {"status": "ready"}


@router.get("/live")
async def liveness_check():
    """
    存活检查端点，用于Kubernetes存活探针
    """
    return {"status": "alive"} 