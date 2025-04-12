# 金融文档分类器

## 项目概述
金融文档分类器是一个基于机器学习的系统，用于自动分类和管理金融文档，如财务报告、合同等。该系统采用微服务架构，确保高效和可扩展性，适用于商业化环境。

## 主要功能
- **文档分类**：支持PDF、DOCX、HTML格式，使用机器学习算法进行自动分类
- **全文搜索**：基于Elasticsearch的高效文档搜索
- **用户管理**：支持不同角色（管理员、分析师、查看者）的权限控制
- **审计日志**：记录所有操作，支持合规性和安全监控
- **多语言支持**：支持英语和中文

## 技术栈
### 后端
- Python + FastAPI构建RESTful API
- PostgreSQL存储结构化数据
- MongoDB存储非结构化数据
- Elasticsearch全文搜索
- Redis缓存和会话管理
- RabbitMQ处理异步任务
- Gunicorn作为WSGI服务器

### 机器学习
- 文档解析：PyPDF2/pdfminer.six（PDF）、python-docx（DOCX）、BeautifulSoup（HTML）
- 文本预处理：NLTK/spaCy
- 特征提取：Scikit-learn的TF-IDF、Gensim的Word2Vec
- 分类模型：Scikit-learn或TensorFlow/PyTorch
- 并行处理：Joblib

### 前端
- React.js构建单页应用
- Material-UI组件库
- Jest测试框架

## 安装说明

### 前提条件
- Docker和Docker Compose
- Git

### 安装步骤
1. 克隆仓库
```bash
git clone https://github.com/kzlbj/finance-doc-classifier.git
cd finance-doc-classifier
```

2. 使用Docker Compose启动服务
```bash
cd docker
docker-compose up -d
```

3. 初始化应用
```bash
docker-compose exec api python initialize.py
```

4. 访问应用
- API: http://localhost:8000
- 前端: http://localhost:3000
- API文档: http://localhost:8000/docs
- ReDoc文档: http://localhost:8000/redoc

### 默认账户
- 管理员: admin@example.com / admin123 (请在生产环境中更改)

## 使用说明
1. 登录系统
2. 上传文档（支持PDF、DOCX、HTML格式）
3. 系统会自动处理文档并进行分类
4. 使用搜索功能查找文档
5. 查看分类结果和文档详情

## 系统架构
![系统架构图](docs/architecture.png)

## 安全特性
- **JWT认证**：使用JSON Web Token进行安全认证
- **CSRF保护**：防止跨站请求伪造攻击
- **安全HTTP头**：包括CSP, X-Content-Type-Options等
- **密码哈希**：使用bcrypt进行密码哈希
- **角色基础访问控制**：基于用户角色的访问权限控制
- **输入验证**：严格的API输入验证和过滤
- **容器安全**：使用非root用户运行容器

## 性能优化
- **机器学习优化**：
  - 模型超参数调优
  - 批量预测处理
  - 特征提取缓存
  - 预测结果缓存
- **API性能**：
  - 使用Gunicorn多工作进程
  - 异步处理长任务
  - 数据库连接池
  - Redis缓存
- **容器优化**：
  - 资源限制设置
  - 健康检查
  - 优化的Docker镜像
  - 自动重启策略

## 开发指南

### 后端开发
1. 设置虚拟环境
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

2. 运行开发服务器
```bash
uvicorn main:app --reload
```

### 前端开发
1. 安装依赖
```bash
cd frontend
npm install
```

2. 运行开发服务器
```bash
npm start
```

### 运行测试
1. 后端测试
```bash
cd backend
pytest -v
```

2. 前端测试
```bash
cd frontend
npm test
```

## 文档
- [API文档](http://localhost:8000/docs)
- [用户手册](docs/user_manual.md)
- [开发者文档](docs/developer_guide.md)

## 许可证
本项目采用MIT许可证 - 详情见[LICENSE](LICENSE)文件 
