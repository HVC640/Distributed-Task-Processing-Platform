FROM python:3.11-slim

WORKDIR /app

# Copy everything (including shared)
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r api_service/requirements.txt

# Set working directory to API
WORKDIR /app

CMD ["python", "-m",  "worker_service.main"]