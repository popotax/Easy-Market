FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=7860

WORKDIR /app

COPY requirements-web.txt ./
RUN pip install --no-cache-dir -r requirements-web.txt

COPY . .

EXPOSE 7860

CMD ["sh", "-c", "gunicorn web.app:app --bind 0.0.0.0:${PORT} --workers 1 --threads 8 --timeout 120"]
