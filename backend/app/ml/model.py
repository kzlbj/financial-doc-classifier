import os
import pickle
import logging
import json
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

from app.core.config import settings


class DocumentClassifier:
    """文档分类模型类"""
    
    def __init__(self, model_type: str = "naive_bayes"):
        """
        初始化文档分类器
        
        参数:
            model_type: 模型类型，可选 "naive_bayes", "svm", "random_forest"
        """
        self.model_type = model_type
        self.vectorizer = TfidfVectorizer(max_features=5000)
        
        if model_type == "naive_bayes":
            self.model = MultinomialNB()
        elif model_type == "svm":
            self.model = SVC(kernel='linear', probability=True)
        elif model_type == "random_forest":
            self.model = RandomForestClassifier(n_estimators=100)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
        
        self.classes = []
        self.version = "0.1.0"
        self.metadata = {
            "model_type": model_type,
            "version": self.version,
            "trained_at": None,
            "performance": {}
        }
    
    def train(self, texts: List[str], labels: List[str]) -> Dict[str, Any]:
        """
        训练模型
        
        参数:
            texts: 文档文本列表
            labels: 对应的类别标签列表
        
        返回:
            包含训练结果和性能指标的字典
        """
        # 划分训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(
            texts, labels, test_size=0.2, random_state=42
        )
        
        # 特征提取
        X_train_tfidf = self.vectorizer.fit_transform(X_train)
        X_test_tfidf = self.vectorizer.transform(X_test)
        
        # 训练模型
        self.model.fit(X_train_tfidf, y_train)
        
        # 评估模型
        y_pred = self.model.predict(X_test_tfidf)
        accuracy = accuracy_score(y_test, y_pred)
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_test, y_pred, average='weighted'
        )
        
        # 存储类别
        self.classes = list(set(labels))
        
        # 更新元数据
        from datetime import datetime
        self.metadata["trained_at"] = datetime.utcnow().isoformat()
        self.metadata["performance"] = {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "num_samples": len(texts),
            "num_classes": len(self.classes)
        }
        
        return self.metadata
    
    def predict(self, text: str) -> Tuple[str, float]:
        """
        预测文档类别
        
        参数:
            text: 文档文本
        
        返回:
            元组（预测类别，置信度）
        """
        if not hasattr(self, 'model') or self.model is None:
            raise ValueError("Model not trained or loaded")
        
        # 特征提取
        text_tfidf = self.vectorizer.transform([text])
        
        # 预测
        if hasattr(self.model, 'predict_proba'):
            proba = self.model.predict_proba(text_tfidf)[0]
            class_idx = np.argmax(proba)
            confidence = proba[class_idx]
        else:
            class_idx = self.model.predict(text_tfidf)[0]
            confidence = 0.8  # 对于不支持概率输出的模型，使用默认置信度
        
        # 获取类别
        if isinstance(class_idx, np.ndarray):
            class_idx = class_idx.item()
        
        if isinstance(class_idx, str):
            # 如果模型直接输出类别字符串
            predicted_class = class_idx
        else:
            # 如果模型输出类别索引
            predicted_class = self.classes[class_idx] if self.classes else str(class_idx)
        
        return predicted_class, float(confidence)
    
    def save(self, model_path: Optional[str] = None) -> str:
        """
        保存模型
        
        参数:
            model_path: 模型保存路径，如果为None则使用默认路径
        
        返回:
            模型保存的路径
        """
        if model_path is None:
            model_path = os.path.join(settings.MODEL_PATH, f"{self.model_type}_{self.version}")
        
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        # 保存模型和向量化器
        with open(f"{model_path}.pkl", 'wb') as f:
            pickle.dump({
                'model': self.model,
                'vectorizer': self.vectorizer,
                'classes': self.classes,
                'metadata': self.metadata
            }, f)
        
        # 保存元数据为JSON
        with open(f"{model_path}_metadata.json", 'w') as f:
            json.dump(self.metadata, f)
        
        return model_path
    
    @classmethod
    def load(cls, model_path: str) -> 'DocumentClassifier':
        """
        加载模型
        
        参数:
            model_path: 模型文件路径
        
        返回:
            加载的DocumentClassifier实例
        """
        try:
            with open(f"{model_path}.pkl", 'rb') as f:
                data = pickle.load(f)
            
            model_type = data['metadata']['model_type']
            classifier = cls(model_type=model_type)
            classifier.model = data['model']
            classifier.vectorizer = data['vectorizer']
            classifier.classes = data['classes']
            classifier.metadata = data['metadata']
            classifier.version = data['metadata']['version']
            
            return classifier
        
        except Exception as e:
            logging.error(f"Error loading model: {e}")
            raise 