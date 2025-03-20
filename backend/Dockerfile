FROM python:3.11-slim

WORKDIR /app

# 设置内存优化环境变量
ENV MALLOC_ARENA_MAX=2
ENV PYTHONMALLOC=malloc
ENV PYTHONHASHSEED=0
ENV PYTHONDISABLE_IMPORTLIB_METADATA_FINDER=1
ENV PYTHONgc__threshold=700
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 先安装核心包
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# 安装最新版本的boto3和botocore
RUN pip install --no-cache-dir --upgrade boto3 botocore

# 安装LangChain相关包
RUN pip install --no-cache-dir langchain>=0.1.0 langchain-community>=0.1.0 langchain-aws>=0.1.0

# 安装向量存储依赖
# 在 Python 3.11 环境下安装 FAISS
RUN pip install --no-cache-dir faiss-cpu==1.7.4 scikit-learn || \
    pip install --no-cache-dir chromadb || \
    pip install --no-cache-dir docarray

# 安装其他依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 安装gunicorn
RUN pip install --no-cache-dir --upgrade gunicorn

# 复制应用代码
COPY . .

# 设置环境变量
ENV PYTHONPATH=/app

# 创建.aws目录
RUN mkdir -p /root/.aws

# 暴露端口
EXPOSE 5000

# 使用gunicorn启动应用
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "2", "--timeout", "120", "app:create_app()"]