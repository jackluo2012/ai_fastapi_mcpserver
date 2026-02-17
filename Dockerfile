# 多阶段构建Dockerfile
# 阶段1：构建环境
FROM python:3.11-slim as builder

WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt ./

# 安装依赖到系统路径
RUN pip install --no-cache-dir -r requirements.txt

# 阶段2：运行时环境
FROM python:3.11-slim

WORKDIR /app

# 从构建阶段复制安装好的包（系统级路径，所有用户可读）
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制应用代码
COPY app/ ./app/
COPY requirements.txt ./

# 禁用Python缓冲，确保日志实时输出
ENV PYTHONUNBUFFERED=1

# 创建非root用户运行应用（安全最佳实践）
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# 启动命令：使用生产级ASGI服务器Uvicorn
# 建议在Kubernetes中通过Deployment配置副本数，而非使用Gunicorn管理进程
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
