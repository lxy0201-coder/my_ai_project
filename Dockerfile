FROM python:3.10-slim

# 设置清华源，加快安装速度
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /app
COPY . .

# 关键优化：先单独安装 torch，再安装其他依赖（避免一次构建体积过大）
# 并且强制指定只安装 CPU 版本，减小体积
RUN pip install torch==2.0.1 --index-url https://download.pytorch.org/whl/cpu \
    && pip install fastapi uvicorn

EXPOSE 80

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
