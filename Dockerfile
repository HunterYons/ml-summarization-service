FROM python:3.10-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Обновляем pip заранее, чтобы избежать ошибок со старой версией
RUN pip install --upgrade pip

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем библиотеки с увеличенным таймаутом (1000 секунд)
# Это поможет прожевать тяжелый Torch без разрыва соединения
RUN pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

# Копируем весь остальной код
COPY . .

# Переменная окружения для корректных импортов из папки src
ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]