FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY static ./static

ENV PORT=5001
EXPOSE 5001

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT} app:app"]
