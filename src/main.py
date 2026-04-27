import mlflow
import asyncio
import time
import torch
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from concurrent.futures import ThreadPoolExecutor
from sentence_transformers import SentenceTransformer, util

# Импортируем обновленную функцию пакетной обработки
from src.model import summarize_batch 
from src.database import SessionLocal, SummarizationHistory

# ThreadPoolExecutor позволяет выполнять блокирующий ML-инференс в отдельных потоках
executor = ThreadPoolExecutor(max_workers=4)

app = FastAPI(
    title="Summarization Service Pro",
    description="API с поддержкой Batch Processing и семантических метрик.",
    version="1.2.0"
)

# Загружаем модель для расчета семантического сходства (SBERT)
# paraphrase-multilingual-MiniLM-L12-v2 — отличная быстрая модель с поддержкой русского языка
print("--- Загрузка модели метрик (SBERT) ---")
metric_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

# Настройка MLflow
mlflow.set_tracking_uri("http://172.18.0.100:5000")
mlflow.set_experiment("Summarization_With_Metrics")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "metrics_enabled": True}

@app.post("/summarize", status_code=200)
async def summarize(text_data: dict, db: Session = Depends(get_db)):
    """
    Эндпоинт суммаризации. Рассчитывает Cosine Similarity вместо ROUGE.
    """
    start_perf = time.perf_counter()
    input_value = text_data.get("text", "")
    
    if isinstance(input_value, str):
        texts_to_process = [input_value]
    elif isinstance(input_value, list):
        texts_to_process = input_value
    else:
        raise HTTPException(status_code=400, detail="Поле 'text' должно быть строкой или списком строк")

    if not texts_to_process or (isinstance(texts_to_process[0], str) and not texts_to_process[0].strip()):
        raise HTTPException(status_code=400, detail="Текст для обработки пуст")

    loop = asyncio.get_event_loop()
    try:
        # 1. Запуск инференса суммаризации
        summaries = await loop.run_in_executor(executor, summarize_batch, texts_to_process)
        
        # 2. Расчет семантической метрики (Cosine Similarity)
        # Мы переводим тексты в векторы и сравниваем их направление
        emb_input = metric_model.encode(texts_to_process, convert_to_tensor=True)
        emb_output = metric_model.encode(summaries, convert_to_tensor=True)
        
        # Считаем сходство между парами (оригинал-результат)
        cos_sim = util.cos_sim(emb_input, emb_output)
        # Берем диагональные элементы (сходство i-го входа с i-м выходом)
        semantic_scores = torch.diag(cos_sim).tolist()
        avg_score = sum(semantic_scores) / len(semantic_scores)

        # 3. Инженерные метрики
        end_perf = time.perf_counter()
        latency = end_perf - start_perf

        # Логирование в MLflow
        with mlflow.start_run(nested=True):
            mlflow.log_param("batch_size", len(texts_to_process))
            mlflow.log_metric("semantic_similarity", avg_score)
            mlflow.log_metric("latency_sec", latency)
        
        # Сохранение в базу
        log_input = texts_to_process[0] if len(texts_to_process) == 1 else f"Batch size: {len(texts_to_process)}"
        log_output = summaries[0] if len(summaries) == 1 else "Batch complete"
        
        history_entry = SummarizationHistory(input_text=log_input, summary_text=log_output)
        db.add(history_entry)
        db.commit()

        return {
            "summary": summaries[0] if isinstance(input_value, str) else summaries,
            "metrics": {
                "semantic_similarity": round(avg_score, 4),
                "latency_sec": round(latency, 3)
            },
            "meta": {
                "batch_size": len(texts_to_process)
            }
        }
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при обработке")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)