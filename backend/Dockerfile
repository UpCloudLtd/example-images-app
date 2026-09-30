FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 5000
CMD ["gunicorn", "--workers", "1", "--threads", "4", "--timeout", "1800", "--bind", "0.0.0.0:5000", "--log-level", "info", "--access-logfile", "-", "app:app"]
