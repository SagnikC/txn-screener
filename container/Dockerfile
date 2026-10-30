# Image for upload option U4 (Vayu Container Registry).
# Runs the same func.py with the same parliament server the function runtime uses.
# Build from the repo root:
#   docker build -f container/Dockerfile -t <registry host>/demo/txn-screener:1.0.0 .
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt constraints.txt ./
RUN pip install --no-cache-dir -r requirements.txt -c constraints.txt
COPY func.py screener.py ./
EXPOSE 8080
CMD ["python", "-m", "parliament", "."]
