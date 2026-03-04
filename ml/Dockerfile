FROM python:3.11-slim

WORKDIR /ml

# Dépendances système utiles pour ML
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copier les dépendances Python
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copier le code ML
COPY . .

# Commande par défaut (modifiable)
CMD ["python", "train.py"]
