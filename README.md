# 🤖 ML Text Summarization Service

Интеллектуальный микросервис для автоматической суммаризации (сжатия) текстов на русском языке. Система построена на базе современных нейросетевых архитектур **Transformer** и включает в себя полноценный цикл мониторинга качества модели через **MLflow**.

---

## ✨ Основные возможности

* **📝 Абстрактивная суммаризация:** Генерация кратких выжимок с помощью модели `T5`, которая перефразирует текст, сохраняя смысл.
* **🎯 Умная оценка качества:** Внедрена метрика **Semantic Similarity** (SBERT) для оценки семантического сходства (вместо простого сравнения слов).
* **🤖 Telegram Bot:** Асинхронный интерфейс для взаимодействия с пользователем в реальном времени.
* **📊 MLflow Интеграция:** Трекинг каждого запроса: точность, время обработки и параметры модели.
* **⚡ Оптимизация (Batching):** Эффективная обработка запросов в многопоточном режиме.
* **🐳 Контейнеризация:** Развертывание всей инфраструктуры одной командой через `docker-compose`.

---

## 🏗 Архитектура системы

Проект разделен на независимые микросервисы:

1.  **Summarization API (FastAPI):** Обработка нейросетевого инференса и расчет метрик.
2.  **Telegram Bot (Aiogram 3):** Клиентский интерфейс.
3.  **MLflow Server:** Платформа для мониторинга экспериментов.
4.  **PostgreSQL:** Хранилище метаданных и истории.

---

## 🧠 Используемые модели

* **Core Model:** [`IlyaGusev/rut5_base_sum_gazeta`](https://huggingface.co/IlyaGusev/rut5_base_sum_gazeta) — специализируется на русском новостном контенте.
* **Metrics Model:** [`paraphrase-multilingual-MiniLM-L12-v2`](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2) — используется для расчета косинусного сходства векторов.

---

## 📈 Мониторинг и метрики (MLflow)

Для каждого запроса в системе фиксируются:
* `semantic_similarity`: Косинусное сходство (0.0 — 1.0).
* `latency_sec`: Скорость генерации.
* `input_len` / `output_len`: Коэффициент сжатия.

> **Зачем это нужно?** Традиционные метрики (типа ROUGE) плохо оценивают перефразирование. SBERT позволяет понять, сохранила ли модель **суть**, даже если использованы другие слова.

---

## 🚀 Быстрый старт

### 1. Предварительные требования
* Установленный **Docker** и **Docker Compose**.
* Токен Telegram бота от [@BotFather](https://t.me/BotFather).

### 2. Настройка окружения
Клонируйте репозиторий и создайте файл `.env` в корне проекта:

```bash
git clone [https://github.com/ваш-аккаунт/ml-summarization-service.git](https://github.com/ваш-аккаунт/ml-summarization-service.git)
cd ml-summarization-service
touch .env
```

Добавьте в `.env` следующие параметры:
```env
# Database
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=summarization_db
DATABASE_URL=postgresql://postgres:postgres@db:5432/summarization_db

# Telegram & API
TG_TOKEN=ваш_токен_бота
API_URL=http://api:8000/summarize

# Monitoring & HF
MLFLOW_TRACKING_URI=[http://172.18.0.100:5000](http://172.18.0.100:5000)
GIT_PYTHON_REFRESH=quiet
HF_TOKEN=ваш_hf_токен (опционально)
```

### 3. Запуск
```bash
docker-compose up --build
```
> **Примечание:** Первый запуск может занять несколько минут, пока скачиваются веса нейросетей (~1.5 ГБ). Дождитесь сообщения `Application startup complete`.

---

## 🛠 Использование

| Интерфейс | Ссылка / Команда |
| :--- | :--- |
| **Telegram Bot** | Напишите боту текст > 10 символов |
| **Swagger API** | [http://localhost:8000/docs](http://localhost:8000/docs) |
| **MLflow UI** | [http://localhost:5000](http://localhost:5000) |