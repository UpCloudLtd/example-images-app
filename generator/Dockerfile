FROM pytorch/pytorch:2.14.1-cuda13.2-cudnn9-runtime

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

COPY generator.py .

CMD ["python", "generator.py"]
