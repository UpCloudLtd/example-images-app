FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
ARG TORCH_INDEX_URL=https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir --index-url "$TORCH_INDEX_URL" "torch>=2.4.0" \
	&& pip install --no-cache-dir -r requirements.txt

COPY generator.py .

CMD ["python", "generator.py"]
