FROM python:3.11-slim

WORKDIR /app

# Dependencias del sistema para mysqlclient
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    gcc \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# El .env NO se copia; se monta en runtime (ver docker-compose.yml)
# Los backups de q_table persisten en un volumen
VOLUME ["/app/q_table_backups"]

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]