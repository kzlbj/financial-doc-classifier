import os
import argparse
import logging
import json
from typing import List, Dict, Any
import pandas as pd
from datetime import datetime

from app.db.session import SessionLocal, mongo_db
from app.ml.model import DocumentClassifier


def load_training_data_from_mongodb() -> tuple:
    """
    从MongoDB加载训练数据
    
    返回:
        元组(texts, labels)
    """
    logging.info("Loading training data from MongoDB...")
    
    # 从MongoDB获取所有已分类的文档
    documents = list(mongo_db.documents.find(
        {"metadata.category": {"$exists": True}},
        {"content": 1, "metadata.category": 1}
    ))
    
    texts = [doc["content"] for doc in documents]
    labels = [doc["metadata"]["category"] for doc in documents]
    
    logging.info(f"Loaded {len(texts)} documents with {len(set(labels))} unique categories")
    return texts, labels


def load_training_data_from_csv(csv_path: str) -> tuple:
    """
    从CSV文件加载训练数据
    
    参数:
        csv_path: CSV文件路径
    
    返回:
        元组(texts, labels)
    """
    logging.info(f"Loading training data from CSV: {csv_path}")
    
    df = pd.read_csv(csv_path)
    if "text" not in df.columns or "category" not in df.columns:
        raise ValueError("CSV must contain 'text' and 'category' columns")
    
    texts = df["text"].tolist()
    labels = df["category"].tolist()
    
    logging.info(f"Loaded {len(texts)} documents with {len(set(labels))} unique categories")
    return texts, labels


def train_model(model_type: str, data_source: str, output_path: str = None) -> DocumentClassifier:
    """
    训练文档分类模型
    
    参数:
        model_type: 模型类型，可选 "naive_bayes", "svm", "random_forest"
        data_source: 数据源，"mongodb" 或 CSV文件路径
        output_path: 模型输出路径
    
    返回:
        训练好的DocumentClassifier实例
    """
    # 加载训练数据
    if data_source == "mongodb":
        texts, labels = load_training_data_from_mongodb()
    else:
        texts, labels = load_training_data_from_csv(data_source)
    
    # 检查数据
    if len(texts) < 10:
        logging.warning("Very small training dataset. Model may not perform well.")
    
    # 创建并训练模型
    classifier = DocumentClassifier(model_type=model_type)
    
    logging.info(f"Training {model_type} model...")
    performance = classifier.train(texts, labels)
    
    logging.info(f"Training complete. Model performance: "
                f"Accuracy: {performance['performance']['accuracy']:.4f}, "
                f"F1: {performance['performance']['f1']:.4f}")
    
    # 保存模型
    if output_path:
        model_path = classifier.save(output_path)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_path = classifier.save(f"app/ml/models/{model_type}_{timestamp}")
    
    logging.info(f"Model saved to {model_path}")
    
    return classifier


if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="Train document classification model")
    parser.add_argument(
        "--model", type=str, default="naive_bayes",
        choices=["naive_bayes", "svm", "random_forest"],
        help="Model type to train"
    )
    parser.add_argument(
        "--data", type=str, default="mongodb",
        help="Data source: 'mongodb' or path to CSV file"
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output path for the trained model"
    )
    
    args = parser.parse_args()
    
    # 训练模型
    train_model(args.model, args.data, args.output) 