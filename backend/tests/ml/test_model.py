import pytest
import os
import tempfile
import numpy as np
from unittest.mock import patch, MagicMock

from app.ml.model import DocumentClassifier


@pytest.fixture
def test_texts():
    """测试文本数据"""
    return [
        "这是一份财务报表，包含第三季度的收入和支出情况",
        "这份合同规定了双方的权利和义务",
        "这是一份风险评估报告，分析了市场波动的风险",
        "第四季度财务数据显示利润增长5%",
        "本合同自签署之日起生效",
        "风险评估显示市场风险处于可控范围",
        "财务报表显示负债率降低",
        "合同条款包括违约赔偿",
        "风险评估建议增加资产多样性"
    ]


@pytest.fixture
def test_labels():
    """测试标签数据"""
    return [
        "财务报告",
        "合同文件",
        "风险评估",
        "财务报告",
        "合同文件",
        "风险评估",
        "财务报告",
        "合同文件",
        "风险评估"
    ]


def test_model_init():
    """测试模型初始化"""
    # 测试默认初始化
    classifier = DocumentClassifier()
    assert classifier.model_type == "naive_bayes"
    assert classifier.version == "0.1.0"
    
    # 测试指定模型类型
    classifier_svm = DocumentClassifier(model_type="svm")
    assert classifier_svm.model_type == "svm"
    
    # 测试不支持的模型类型
    with pytest.raises(ValueError):
        DocumentClassifier(model_type="unsupported_model")


def test_model_train(test_texts, test_labels):
    """测试模型训练"""
    classifier = DocumentClassifier()
    
    # 训练模型
    metadata = classifier.train(test_texts, test_labels)
    
    # 验证训练结果
    assert "performance" in metadata
    assert "accuracy" in metadata["performance"]
    assert "f1" in metadata["performance"]
    assert len(classifier.classes) == 3
    assert set(classifier.classes) == {"财务报告", "合同文件", "风险评估"}


def test_model_predict(test_texts, test_labels):
    """测试模型预测"""
    classifier = DocumentClassifier()
    
    # 先训练模型
    classifier.train(test_texts, test_labels)
    
    # 测试已知类别的文本预测
    test_text = "这是一份新的财务报表，展示了公司的收入情况"
    predicted_class, confidence = classifier.predict(test_text)
    
    # 检查预测结果
    assert predicted_class in ["财务报告", "合同文件", "风险评估"]
    assert 0 <= confidence <= 1


def test_model_save_load():
    """测试模型保存和加载"""
    # 创建临时目录用于保存模型
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建并训练模型
        classifier = DocumentClassifier()
        classifier.train(
            ["财务报告内容", "合同文件内容", "风险评估内容"],
            ["财务报告", "合同文件", "风险评估"]
        )
        
        # 保存模型
        model_path = os.path.join(temp_dir, "test_model")
        saved_path = classifier.save(model_path)
        
        # 检查文件是否被创建
        assert os.path.exists(f"{model_path}.pkl")
        assert os.path.exists(f"{model_path}_metadata.json")
        
        # 加载模型
        loaded_classifier = DocumentClassifier.load(model_path)
        
        # 验证加载的模型
        assert loaded_classifier.model_type == classifier.model_type
        assert loaded_classifier.version == classifier.version
        assert loaded_classifier.classes == classifier.classes
        
        # 测试加载的模型预测功能
        test_text = "这是一份财务报告"
        original_prediction = classifier.predict(test_text)
        loaded_prediction = loaded_classifier.predict(test_text)
        
        # 预测结果应该相同
        assert original_prediction[0] == loaded_prediction[0] 