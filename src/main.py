import mlflow
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from src.model import summarize_text
from src.database import SessionLocal, SummarizationHistory
import asyncio
from concurrent.futures import ThreadPoolExecutor

app = FastAPI(title="Summarization Service Pro")
executor = ThreadPoolExecutor(max_workers=1)

# Настройка MLflow
mlflow.set_tracking_uri("http://mlflow:5000")
mlflow.set_experiment("Summarization_Experiments")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/summarize")
async def summarize(text_data: dict, db: Session = Depends(get_db)):
    text = text_data.get("text", "")
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text is empty")

    loop = asyncio.get_event_loop()
    try:
        # Инференс
        summary = await loop.run_in_executor(executor, summarize_text, text)
        
        # 1. Сохранение в БД (Исправляет замечание №3)
        history_entry = SummarizationHistory(input_text=text, summary_text=summary)
        db.add(history_entry)
        db.commit()

        # 2. Логирование в MLflow (Требование ТЗ)
        with mlflow.start_run(nested=True):
            mlflow.log_param("input_len", len(text))
            mlflow.log_param("output_len", len(summary))
            # Здесь можно добавить логирование реальных метрик качества, если они считаются
        
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))