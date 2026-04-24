FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 1. 先把 requirements.txt 复制进去
COPY requirements.txt .

# 2. 直接安装依赖，不使用清华镜像，避免 403 错误
# 也不要搞什么 --index-url，让 pip 自动去官方源下载是最稳的
RUN pip install --no-cache-dir -r requirements.txt

# 3. 复制剩余所有代码
COPY . .

# 4. 暴露 80 端口
EXPOSE 80

# 5. 启动服务
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
