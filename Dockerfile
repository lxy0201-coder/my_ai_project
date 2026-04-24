FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

# 修正点：使用 --extra-index-url，意思是：先在默认官方源找，找不到再去 PyTorch 源找
RUN pip install --no-cache-dir -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

COPY . .

EXPOSE 80

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
