import os
import io
import json
import logging
from typing import Dict, List, Any, Tuple, Optional

import PyPDF2
from docx import Document
from bs4 import BeautifulSoup
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

from app import crud, schemas
from app.core.config import settings
from app.db.session import mongo_db, es_client

# 初始化NLTK资源
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

# 加载spaCy模型
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logging.warning("spaCy model not found. Downloading...")
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# 中文支持
try:
    nlp_zh = spacy.load("zh_core_web_sm")
except OSError:
    logging.warning("spaCy Chinese model not found. Using English model instead.")
    nlp_zh = nlp

# 停用词
stop_words_en = set(stopwords.words('english'))


def extract_text_from_pdf(file_path: str) -> str:
    """从PDF文件中提取文本"""
    text = ""
    try:
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text()
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {e}")
    return text


def extract_text_from_docx(file_path: str) -> str:
    """从DOCX文件中提取文本"""
    text = ""
    try:
        doc = Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        logging.error(f"Error extracting text from DOCX: {e}")
    return text


def extract_text_from_html(file_path: str) -> str:
    """从HTML文件中提取文本"""
    text = ""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        soup = BeautifulSoup(html_content, 'html.parser')
        # 移除脚本和样式元素
        for script in soup(["script", "style"]):
            script.extract()
        text = soup.get_text()
    except Exception as e:
        logging.error(f"Error extracting text from HTML: {e}")
    return text


def preprocess_text(text: str, language: str = "en") -> str:
    """文本预处理：分词、去除停用词等"""
    if not text:
        return ""
    
    # 简单的语言检测
    if any('\u4e00' <= char <= '\u9fff' for char in text):
        language = "zh"
    
    if language == "zh":
        # 中文处理
        doc = nlp_zh(text)
        tokens = [token.text for token in doc if not token.is_stop and not token.is_punct]
    else:
        # 英文处理
        tokens = word_tokenize(text.lower())
        tokens = [word for word in tokens if word.isalnum() and word not in stop_words_en]
    
    return " ".join(tokens)


def classify_document(text: str, file_type: str) -> Tuple[str, float]:
    """
    使用预训练模型对文档进行分类
    
    返回：
        元组（类别，置信度）
    """
    # TODO: 实现实际的分类逻辑，目前返回模拟数据
    
    # 模拟金融文档类别
    categories = [
        "财务报告", 
        "投资分析", 
        "风险评估", 
        "市场研究", 
        "监管合规", 
        "贷款申请",
        "保险合同",
        "审计报告"
    ]
    
    # 在实际应用中，这里应该加载模型并进行预测
    # 目前仅返回随机类别和置信度作为示例
    import random
    category = random.choice(categories)
    confidence = random.uniform(0.7, 0.99)
    
    return category, confidence


def store_document_content(document_id: int, text: str, metadata: Dict[str, Any]) -> None:
    """
    将文档内容存储到MongoDB
    """
    mongo_db.documents.insert_one({
        "document_id": document_id,
        "content": text,
        "metadata": metadata,
        "created_at": metadata.get("upload_time")
    })


def index_document(document_id: int, text: str, metadata: Dict[str, Any]) -> None:
    """
    将文档索引到Elasticsearch
    """
    try:
        es_client.index(
            index="finance_docs",
            id=document_id,
            body={
                "content": text,
                "filename": metadata.get("filename"),
                "uploader_id": metadata.get("uploader_id"),
                "upload_time": metadata.get("upload_time"),
                "file_type": metadata.get("file_type"),
                "category": metadata.get("category"),
                "confidence": metadata.get("confidence")
            }
        )
    except Exception as e:
        logging.error(f"Error indexing document in Elasticsearch: {e}")


def process_document(document_id: int, file_path: str, file_type: str, db) -> Dict[str, Any]:
    """
    处理上传的文档
    
    步骤:
    1. 根据文件类型提取文本
    2. 预处理文本
    3. 使用模型分类文档
    4. 将分类结果存入数据库
    5. 将文档内容存入MongoDB
    6. 将文档索引到Elasticsearch
    """
    # 获取文档记录
    document = crud.document.get(db, id=document_id)
    if not document:
        logging.error(f"Document with ID {document_id} not found")
        return {"success": False, "error": "Document not found"}
    
    # 提取文本
    if file_type == "pdf":
        text = extract_text_from_pdf(file_path)
    elif file_type == "docx":
        text = extract_text_from_docx(file_path)
    elif file_type == "html":
        text = extract_text_from_html(file_path)
    else:
        return {"success": False, "error": "Unsupported file type"}
    
    if not text:
        return {"success": False, "error": "Failed to extract text from document"}
    
    # 预处理文本
    processed_text = preprocess_text(text)
    
    # 分类文档
    category, confidence = classify_document(processed_text, file_type)
    
    # 创建分类记录
    classification_in = schemas.DocumentClassificationCreate(
        category=category,
        confidence=confidence,
        model_version="0.1.0"  # 当前模型版本
    )
    
    # 存储分类结果
    classification = crud.document_classification.create_with_document(
        db, obj_in=classification_in, document_id=document_id
    )
    
    # 准备元数据
    metadata = {
        "document_id": document_id,
        "filename": document.filename,
        "file_type": document.file_type,
        "uploader_id": document.uploader_id,
        "upload_time": document.upload_time.isoformat(),
        "category": category,
        "confidence": confidence
    }
    
    # 存储文档内容到MongoDB
    store_document_content(document_id, text, metadata)
    
    # 索引文档到Elasticsearch
    index_document(document_id, text, metadata)
    
    return {
        "success": True,
        "document_id": document_id,
        "category": category,
        "confidence": confidence
    } 