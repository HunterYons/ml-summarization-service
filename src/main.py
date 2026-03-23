from fastapi import FastAPI
from pydantic import BaseModel
from src.model import get_summarization

app = FastAPI(title="Summarization Service")

class TextRequest(BaseModel):
    text: str

@app.get("/")
def read_root():
    return {"message": "Система суммаризации текста готова к работе"}

@app.post("/summarize")
def summarize(request: TextRequest):
    summary = get_summarization(request.text)
    return {"summary": summary}