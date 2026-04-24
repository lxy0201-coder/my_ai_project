FROM python:3.10-slim

WORKDIR /app

# 先拷贝 requirements.txt
COPY requirements.txt .

# 关键在这里：指定额外的 index-url 给 torch
RUN pip install --no-cache-dir -r requirements.txt --index-url https://download.pytorch.org/whl/cpu

# 拷贝你的源代码
COPY . .

EXPOSE 80
CMD ["python", "main.py"]
