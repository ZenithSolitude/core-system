FROM python:3.9-slim

WORKDIR /app

# Установка git для загрузки модулей
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Создаем папку для модулей если нет
RUN mkdir -p modules

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
