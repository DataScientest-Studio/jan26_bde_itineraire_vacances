FROM python:3.11-slim

WORKDIR /app

RUN chmod -R 777 /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "app.main:app_iv", "--host", "0.0.0.0", "--port", "8000"]
