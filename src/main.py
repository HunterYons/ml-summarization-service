import mlflow
import asyncio
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from concurrent.futures import ThreadPoolExecutor

# Импортируем обновленную функцию пакетной обработки
from src.model import summarize_batch 
from src.database import SessionLocal, SummarizationHistory

# ThreadPoolExecutor позволяет выполнять блокирующий ML-инференс в отдельных потоках
executor = ThreadPoolExecutor(max_workers=4)

app = FastAPI(
    title="Summarization Service Pro",
    description="API с поддержкой пакетной обработки (Batch Processing).",
    version="1.1.0"
)

# Настройка MLflow
mlflow.set_tracking_uri("http://172.18.0.100:5000")
mlflow.set_experiment("Summarization_Experiments")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "mode": "batch"}

@app.post("/summarize", status_code=200)
async def summarize(text_data: dict, db: Session = Depends(get_db)):
    """
    Эндпоинт суммаризации. Поддерживает одиночный текст (str) и батчи (list).
    """
    input_value = text_data.get("text", "")
    
    # Определяем, работаем мы с одиночным текстом или списком
    if isinstance(input_value, str):
        texts_to_process = [input_value]
    elif isinstance(input_value, list):
        texts_to_process = input_value
    else:
        raise HTTPException(status_code=400, detail="Поле 'text' должно быть строкой или списком строк")

    # Валидация входных данных
    if not texts_to_process or (isinstance(texts_to_process[0], str) and not texts_to_process[0].strip()):
        raise HTTPException(status_code=400, detail="Текст для обработки пуст")

    loop = asyncio.get_event_loop()
    try:
        # Запуск инференса в пуле потоков
        summaries = await loop.run_in_executor(executor, summarize_batch, texts_to_process)
        
        # Сохранение в базу (для простоты сохраняем первый результат из батча)
        # Если это батч, помечаем это в базе
        log_input = texts_to_process[0] if len(texts_to_process) == 1 else f"Batch size: {len(texts_to_process)}"
        log_output = summaries[0] if len(summaries) == 1 else "Batch summary complete"
        
        history_entry = SummarizationHistory(input_text=log_input, summary_text=log_output)
        db.add(history_entry)
        db.commit()

        # Логирование в MLflow
        with mlflow.start_run(nested=True):
            mlflow.log_param("batch_size", len(texts_to_process))
            mlflow.log_metric("is_success", 1.0)
        
        # Возвращаем результат в том же формате, в котором получили (строка или список)
        return {
            "summary": summaries[0] if isinstance(input_value, str) else summaries,
            "meta": {
                "batch_size": len(texts_to_process),
                "is_batch": isinstance(input_value, list)
            }
        }
    except Exception as e:
        print(f"Error during batch inference: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при обработке нейросетью")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)