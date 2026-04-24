FROM python:3.10-slim
WORKDIR /app
COPY . .
# 这一行让它自动安装你的依赖
RUN pip install --no-cache-dir fastapi uvicorn torch -i https://mirrors.cloud.tencent.com/pypi/simple
# 告诉云托管运行这一行命令
CMD ["python", "main.py"]