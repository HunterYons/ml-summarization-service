import os
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# 1. Получаем токен из переменных окружения. 
# Если Docker успешно пробросил переменную, она будет доступна здесь.
hf_token = os.getenv("HF_TOKEN")

model_name = "IlyaGusev/rut5_base_sum_gazeta"

# 2. Глобальная инициализация. 
# Эти объекты создаются один раз при первом импорте модуля и остаются в памяти.
# Параметр 'token' (или 'use_auth_token' в старых версиях) активирует авторизацию.
print(f"--- Загрузка модели {model_name} ---")

tokenizer = AutoTokenizer.from_pretrained(
    model_name, 
    token=hf_token
)

model = AutoModelForSeq2SeqLM.from_pretrained(
    model_name, 
    token=hf_token
)

print("--- Модель успешно загружена и готова к работе ---")

def summarize_text(text: str):
    """
    Функция для генерации краткого содержания.
    Использует глобально загруженные модель и токенизатор.
    """
    # Обоснование max_length=1024: это предел для архитектуры T5
    inputs = tokenizer(text, return_tensors="pt", max_length=1024, truncation=True)
    
    with torch.no_grad():
        hypotheses = model.generate(
            **inputs, 
            num_beams=5,             # Поиск по лучам для более качественного текста
            max_length=200,          # Ограничение длины суммаризации
            min_length=30,           # Гарантия того, что ответ не будет слишком коротким
            no_repeat_ngram_size=3   # Предотвращение зацикливания фраз
        )
    
    # Декодирование результата из токенов в понятный текст
    return tokenizer.decode(hypotheses[0], skip_special_tokens=True)