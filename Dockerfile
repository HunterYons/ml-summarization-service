# 1. Базовый образ
FROM python:3.10-slim

# 2. Установка системных утилит (нужны для некоторых библиотек)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 3. Кэширование зависимостей (самый важный этап!)
# Копируем только файл со списком библиотек
COPY requirements.txt .
# Устанавливаем их. Если файл не менялся, Docker пропустит этот шаг при следующей сборке
RUN pip install --no-cache-dir -r requirements.txt

# 4. Копирование кода
COPY . .

# 5. Подготовка среды
# Создаем файл логов, чтобы Docker мог в него писать
RUN touch api_history.log && chmod 666 api_history.log

# 6. Проброс порта для FastAPI
EXPOSE 8000

# Команда по умолчанию (будет переопределена в docker-compose для бота)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]