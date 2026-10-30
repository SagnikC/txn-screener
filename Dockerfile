# Image for upload option U4 (Vayu Container Registry)
FROM python:3.11-slim
WORKDIR /app
COPY requirements-container.txt ./
RUN pip install --no-cache-dir -r requirements-container.txt
COPY screener.py app.py ./
ENV PORT=8080
EXPOSE 8080
CMD exec gunicorn -b 0.0.0.0:$PORT -w 1 --threads 8 app:app
