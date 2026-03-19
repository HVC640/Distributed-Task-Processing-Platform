FROM python:3.11-slim

WORKDIR /app

# Copy everything (including shared)
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r recovery_service/requirements.txt

# Set working directory to app
WORKDIR /app

CMD ["python", "-m",  "recovery_service.main"]