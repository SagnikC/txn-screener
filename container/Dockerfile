# Image for upload option U4 (Vayu Container Registry).
# Build from the repo root:  docker build -f container/Dockerfile -t <registry>/demo/txn-screener:1.0.0 .
FROM python:3.11-slim
WORKDIR /app
COPY container/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY function/__init__.py function/func.py function/screener.py ./function/
COPY container/app.py ./app.py
ENV PORT=8080
EXPOSE 8080
CMD exec gunicorn -b 0.0.0.0:$PORT -w 1 --threads 8 app:app
