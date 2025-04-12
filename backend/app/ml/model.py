import os
import pickle
import logging
import json
import time
from typing import List, Dict, Any, Tuple, Optional, Union, Callable
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.pipeline import Pipeline
from joblib import Memory, Parallel, delayed
import redis
from functools import lru_cache

from app.core.config import settings


# 初始化Redis连接（用于模型预测缓存）
try:
    redis_client = redis.from_url(settings.REDIS_URL)
    REDIS_AVAILABLE = True
except:
    REDIS_AVAILABLE = False
    logging.warning("Redis连接失败，将使用本地缓存")

# 配置joblib缓存
cache_dir = os.path.join(os.path.dirname(__file__), "cache")
os.makedirs(cache_dir, exist_ok=True)
memory = Memory(cache_dir, verbose=0)


class DocumentClassifier:
    """文档分类模型类"""
    
    def __init__(self, model_type: str = "naive_bayes", cache_ttl: int = 3600):
        """
        初始化文档分类器
        
        参数:
            model_type: 模型类型，可选 "naive_bayes", "svm", "random_forest"
            cache_ttl: 缓存有效期（秒）
        """
        self.model_type = model_type
        self.vectorizer = TfidfVectorizer(max_features=5000)
        self.cache_ttl = cache_ttl
        
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
        
        # 检查是否有预训练模型
        self._try_load_pretrained()
    
    def _try_load_pretrained(self):
        """尝试加载预训练模型"""
        try:
            default_path = os.path.join(settings.MODEL_PATH, f"{self.model_type}_{self.version}")
            if os.path.exists(f"{default_path}.pkl"):
                self.load(default_path)
                logging.info(f"已加载预训练模型: {default_path}")
        except Exception as e:
            logging.warning(f"加载预训练模型失败: {e}")
    
    @memory.cache
    def _process_text_batch(self, texts: List[str]) -> np.ndarray:
        """处理文本批次，进行特征提取（带缓存）"""
        return self.vectorizer.transform(texts)
    
    def _parallel_process_texts(self, texts: List[str], batch_size: int = 100) -> List[np.ndarray]:
        """并行处理多批次文本"""
        n_batches = (len(texts) + batch_size - 1) // batch_size
        batches = [texts[i*batch_size:(i+1)*batch_size] for i in range(n_batches)]
        
        results = Parallel(n_jobs=-1)(
            delayed(self._process_text_batch)(batch) for batch in batches
        )
        
        return results
    
    def train(self, texts: List[str], labels: List[str], use_hyperparameter_tuning: bool = False) -> Dict[str, Any]:
        """
        训练模型
        
        参数:
            texts: 文档文本列表
            labels: 对应的类别标签列表
            use_hyperparameter_tuning: 是否使用超参数调优
        
        返回:
            包含训练结果和性能指标的字典
        """
        start_time = time.time()
        
        # 划分训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(
            texts, labels, test_size=0.2, random_state=42
        )
        
        # 创建处理管道
        if not use_hyperparameter_tuning:
            # 特征提取
            X_train_tfidf = self.vectorizer.fit_transform(X_train)
            X_test_tfidf = self.vectorizer.transform(X_test)
            
            # 训练模型
            self.model.fit(X_train_tfidf, y_train)
        else:
            # 使用网格搜索进行超参数调优
            pipeline = Pipeline([
                ('tfidf', TfidfVectorizer()),
                ('classifier', self._get_model_for_tuning())
            ])
            
            # 设置超参数网格
            param_grid = self._get_param_grid()
            
            # 执行网格搜索
            grid_search = GridSearchCV(pipeline, param_grid, cv=5, n_jobs=-1, verbose=1)
            grid_search.fit(X_train, y_train)
            
            # 获取最佳模型
            best_params = grid_search.best_params_
            self.vectorizer = grid_search.best_estimator_.named_steps['tfidf']
            self.model = grid_search.best_estimator_.named_steps['classifier']
            
            # 评估
            X_test_tfidf = self.vectorizer.transform(X_test)
            
            # 更新元数据中的超参数
            self.metadata["hyperparameters"] = best_params
        
        # 评估模型
        y_pred = self.model.predict(X_test_tfidf)
        accuracy = accuracy_score(y_test, y_pred)
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_test, y_pred, average='weighted'
        )
        
        # 存储类别
        self.classes = list(set(labels))
        
        # 计算训练时间
        training_time = time.time() - start_time
        
        # 更新元数据
        from datetime import datetime
        self.metadata["trained_at"] = datetime.utcnow().isoformat()
        self.metadata["performance"] = {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "num_samples": len(texts),
            "num_classes": len(self.classes),
            "training_time": training_time
        }
        
        return self.metadata
    
    def _get_model_for_tuning(self):
        """获取用于超参数调优的模型"""
        if self.model_type == "naive_bayes":
            return MultinomialNB()
        elif self.model_type == "svm":
            return SVC(probability=True)
        elif self.model_type == "random_forest":
            return RandomForestClassifier()
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")
    
    def _get_param_grid(self):
        """获取超参数网格"""
        if self.model_type == "naive_bayes":
            return {
                'tfidf__max_features': [1000, 3000, 5000],
                'tfidf__ngram_range': [(1, 1), (1, 2)],
                'classifier__alpha': [0.1, 0.5, 1.0]
            }
        elif self.model_type == "svm":
            return {
                'tfidf__max_features': [3000, 5000],
                'tfidf__ngram_range': [(1, 1), (1, 2)],
                'classifier__C': [0.1, 1.0, 10.0],
                'classifier__kernel': ['linear', 'rbf']
            }
        elif self.model_type == "random_forest":
            return {
                'tfidf__max_features': [3000, 5000],
                'tfidf__ngram_range': [(1, 1), (1, 2)],
                'classifier__n_estimators': [50, 100],
                'classifier__max_depth': [None, 10, 20]
            }
        else:
            return {}
    
    def predict_batch(self, texts: List[str]) -> List[Tuple[str, float]]:
        """
        批量预测文档类别
        
        参数:
            texts: 文档文本列表
        
        返回:
            预测结果列表，每个结果为(预测类别，置信度)的元组
        """
        if not hasattr(self, 'model') or self.model is None:
            raise ValueError("Model not trained or loaded")
        
        # 并行处理文本
        batch_size = min(100, len(texts))
        processed_batches = self._parallel_process_texts(texts, batch_size)
        
        # 合并处理结果
        if len(processed_batches) == 1:
            text_features = processed_batches[0]
        else:
            text_features = np.vstack([batch for batch in processed_batches])
        
        # 预测
        predictions = []
        if hasattr(self.model, 'predict_proba'):
            probas = self.model.predict_proba(text_features)
            for i, proba in enumerate(probas):
                class_idx = np.argmax(proba)
                confidence = proba[class_idx]
                predicted_class = self.classes[class_idx]
                predictions.append((predicted_class, float(confidence)))
        else:
            class_indices = self.model.predict(text_features)
            for class_idx in class_indices:
                predicted_class = self.classes[class_idx]
                predictions.append((predicted_class, 0.8))  # 默认置信度
        
        return predictions
    
    def predict(self, text: str) -> Tuple[str, float]:
        """
        预测文档类别（单个文档）
        
        参数:
            text: 文档文本
        
        返回:
            元组（预测类别，置信度）
        """
        if not hasattr(self, 'model') or self.model is None:
            raise ValueError("Model not trained or loaded")
        
        # 尝试从缓存获取结果
        cache_key = f"model:{self.model_type}:{self.version}:{hash(text)}"
        cached_result = self._get_from_cache(cache_key)
        
        if cached_result:
            return cached_result
        
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
        
        result = (predicted_class, float(confidence))
        
        # 缓存结果
        self._save_to_cache(cache_key, result)
        
        return result
    
    def _get_from_cache(self, key: str) -> Optional[Tuple[str, float]]:
        """从缓存获取预测结果"""
        if REDIS_AVAILABLE:
            cached = redis_client.get(key)
            if cached:
                try:
                    return pickle.loads(cached)
                except:
                    pass
        return None
    
    def _save_to_cache(self, key: str, result: Tuple[str, float]) -> None:
        """保存预测结果到缓存"""
        if REDIS_AVAILABLE:
            try:
                redis_client.setex(key, self.cache_ttl, pickle.dumps(result))
            except:
                pass
    
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