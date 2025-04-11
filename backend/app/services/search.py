import logging
from typing import List, Dict, Any, Optional
from elasticsearch import Elasticsearch
from sqlalchemy.orm import Session

from app import models, schemas
from app.db.session import es_client


def search_documents(
    db: Session,
    query: str,
    category: Optional[str] = None,
    current_user: Optional[models.User] = None
) -> List[schemas.DocumentSearchResult]:
    """
    在Elasticsearch中搜索文档
    
    参数:
        db: 数据库会话
        query: 搜索查询
        category: 可选的类别过滤
        current_user: 当前用户，用于权限控制
    
    返回:
        符合条件的文档搜索结果列表
    """
    try:
        # 构建搜索查询
        search_body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "content": query
                            }
                        }
                    ],
                    "filter": []
                }
            },
            "sort": [
                {"_score": {"order": "desc"}}
            ],
            "size": 50  # 限制结果数量
        }
        
        # 添加类别过滤
        if category:
            search_body["query"]["bool"]["filter"].append({
                "term": {"category": category}
            })
        
        # 添加权限过滤，非管理员和分析师只能搜索自己的文档
        if current_user and current_user.role not in ["admin", "analyst"]:
            search_body["query"]["bool"]["filter"].append({
                "term": {"uploader_id": current_user.id}
            })
        
        # 执行搜索
        response = es_client.search(
            index="finance_docs",
            body=search_body
        )
        
        # 处理搜索结果
        results = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            result = schemas.DocumentSearchResult(
                document_id=int(hit["_id"]),
                score=hit["_score"],
                filename=source.get("filename", ""),
                original_filename=source.get("filename", ""),
                upload_time=source.get("upload_time", ""),
                category=source.get("category", ""),
                confidence=source.get("confidence", 0.0)
            )
            results.append(result)
        
        return results
    
    except Exception as e:
        logging.error(f"Error searching documents: {e}")
        return []


def get_similar_documents(document_id: int, limit: int = 5) -> List[Dict[str, Any]]:
    """
    获取与给定文档相似的文档
    
    参数:
        document_id: 文档ID
        limit: 返回结果数量限制
    
    返回:
        相似文档列表
    """
    try:
        # 先获取文档
        document = es_client.get(index="finance_docs", id=document_id)
        
        # 构建相似性查询
        search_body = {
            "query": {
                "more_like_this": {
                    "fields": ["content"],
                    "like": [
                        {
                            "_index": "finance_docs",
                            "_id": document_id
                        }
                    ],
                    "min_term_freq": 1,
                    "max_query_terms": 25,
                    "min_doc_freq": 1
                }
            },
            "size": limit
        }
        
        # 执行搜索
        response = es_client.search(
            index="finance_docs",
            body=search_body
        )
        
        # 处理搜索结果
        results = []
        for hit in response["hits"]["hits"]:
            if hit["_id"] != str(document_id):  # 排除自身
                source = hit["_source"]
                result = {
                    "document_id": int(hit["_id"]),
                    "score": hit["_score"],
                    "filename": source.get("filename", ""),
                    "category": source.get("category", ""),
                    "similarity": hit["_score"] / 10  # 归一化相似度分数
                }
                results.append(result)
        
        return results
    
    except Exception as e:
        logging.error(f"Error finding similar documents: {e}")
        return [] 