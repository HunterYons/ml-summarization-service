from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.model import summarize_text
import asyncio
from concurrent.futures import ThreadPoolExecutor
import datetime

app = FastAPI(title="Summarization Service", version="1.1.0")

# Пул для выполнения тяжелых расчетов модели (чтобы не вешать сервер)
executor = ThreadPoolExecutor(max_workers=1)

class SummarizeRequest(BaseModel):
    text: str

@app.post("/summarize")
async def summarize(request: SummarizeRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text is empty")
    
    # Асинхронный вызов модели (исправляет замечание №4)
    loop = asyncio.get_event_loop()
    try:
        summary = await loop.run_in_executor(executor, summarize_text, request.text)
        
        # Имитация взаимодействия/БД (исправляет замечание №3)
        with open("api_history.log", "a", encoding="utf-8") as f:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] Запрос: {len(request.text)} симв. -> Ответ получен.\n")
            
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))