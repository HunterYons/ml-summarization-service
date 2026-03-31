# Используем легкий образ Python
FROM python:3.10-slim

# Устанавливаем системные зависимости для работы с текстом
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/apt/lists/*

WORKDIR /app

# Сначала копируем только requirements, чтобы закэшировать установку библиотек
COPY requirements.txt .

# Устанавливаем библиотеки (используем CPU версию torch для экономии места)
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальной код
COPY . .

# Создаем пустой файл логов, чтобы контейнер не падал при записи
RUN touch api_history.log && chmod 666 api_history.log

# Открываем порт
EXPOSE 8000

# Запуск через uvicorn
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]