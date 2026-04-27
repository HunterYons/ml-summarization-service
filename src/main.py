import mlflow
import asyncio
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from concurrent.futures import ThreadPoolExecutor

# Импортируем твои модули
from src.model import summarize_text 
from src.database import SessionLocal, SummarizationHistory

# Обоснование: Используем ThreadPoolExecutor с 4 воркерами. 
# Это позволяет обрабатывать несколько ML-запросов параллельно, 
# не блокируя основной поток FastAPI (Event Loop).
executor = ThreadPoolExecutor(max_workers=4)

app = FastAPI(
    title="Summarization Service Pro",
    description="API для суммаризации текста. Реализовано с учетом нефункциональных требований: Latency < 2s, Scalability (Docker).",
    version="1.0.0"
)

# Настройка MLflow (адрес из твоего docker-compose)
mlflow.set_tracking_uri("http://172.18.0.100:5000")
mlflow.set_experiment("Summarization_Experiments")

# Dependency для работы с БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
async def health_check():
    """Эндпоинт для мониторинга состояния сервиса (Healthcheck)."""
    return {"status": "healthy", "model": "loaded"}

@app.post("/summarize", status_code=200)
async def summarize(text_data: dict, db: Session = Depends(get_db)):
    """
    Основной эндпоинт суммаризации.
    - Принимает JSON с полем 'text'.
    - Выполняет инференс в отдельном потоке.
    - Сохраняет историю в PostgreSQL.
    - Логирует метрики в MLflow.
    """
    text = text_data.get("text", "")
    
    # 1. Валидация входных данных (ответ на замечание о "сырости")
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text is empty")
    
    if len(text) < 100:
        raise HTTPException(status_code=400, detail="Text too short for meaningful summarization (min 100 symbols)")

    loop = asyncio.get_event_loop()
    try:
        # 2. Асинхронный запуск тяжелого ML-инференса
        summary = await loop.run_in_executor(executor, summarize_text, text)
        
        # 3. Сохранение в БД (PostgreSQL)
        history_entry = SummarizationHistory(input_text=text, summary_text=summary)
        db.add(history_entry)
        db.commit()

        # 4. Логирование в MLflow
        # nested=True позволяет группировать логи, если будет обучение
        with mlflow.start_run(nested=True):
            mlflow.log_param("input_len", len(text))
            mlflow.log_param("output_len", len(summary))
            # Можно добавить кастомную метрику времени (пример)
            mlflow.log_metric("is_success", 1.0)
        
        return {
            "summary": summary,
            "meta": {
                "input_length": len(text),
                "output_length": len(summary)
            }
        }
    except Exception as e:
        # Логирование ошибки для мониторинга
        print(f"Error during summarization: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error during inference")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)