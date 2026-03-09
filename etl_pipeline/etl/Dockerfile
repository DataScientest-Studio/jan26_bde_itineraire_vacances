FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le projet (pas seulement /etl)
COPY . .

# Lancer ton ETL
CMD ["python", "run_import.py", "--mode", "full"]

