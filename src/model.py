import os
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from typing import List

# 1. Получаем токен из переменных окружения
hf_token = os.getenv("HF_TOKEN")
model_name = "IlyaGusev/rut5_base_sum_gazeta"

print(f"--- Загрузка модели {model_name} (Batch Mode) ---")

# Загружаем модель и токенизатор один раз
tokenizer = AutoTokenizer.from_pretrained(
    model_name, 
    token=hf_token
)

model = AutoModelForSeq2SeqLM.from_pretrained(
    model_name, 
    token=hf_token
)

print("--- Модель успешно загружена и готова к батчингу ---")

def summarize_batch(texts: List[str]) -> List[str]:
    """
    Функция для пакетной генерации краткого содержания.
    Принимает список строк, возвращает список строк.
    """
    if not texts:
        return []

    # padding=True добавляет специальные токены заполнения, 
    # чтобы все тексты в пакете имели одинаковую длину для матрицы тензора.
    inputs = tokenizer(
        texts, 
        return_tensors="pt", 
        max_length=1024, 
        truncation=True, 
        padding=True
    )
    
    with torch.no_grad():
        hypotheses = model.generate(
            **inputs, 
            num_beams=5, 
            max_length=200, 
            min_length=30, 
            no_repeat_ngram_size=3
        )
    
    # batch_decode преобразует весь пакет тензоров обратно в список строк
    return tokenizer.batch_decode(hypotheses, skip_special_tokens=True)