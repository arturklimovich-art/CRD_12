FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    git \
    curl \
    patch \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY ./requirements.txt /app/requirements.txt

# Install Python deps
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy source
COPY . /app/
COPY init-patch-apply.py /app/init-patch-apply.py

# Install patch utility
RUN apt-get update && apt-get install -y patch && rm -rf /var/lib/apt/lists/*

# Expose port
EXPOSE 8000

# Default command (will be replaced after init script is ready)
CMD ["python3", "/app/init-patch-apply.py"]
