from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

# Загружаем модель глобально (один раз при импорте)
model_name = "IlyaGusev/rut5_base_sum_gazeta"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

def summarize_text(text: str):
    # Обоснование max_length: ограничение архитектуры T5
    inputs = tokenizer(text, return_tensors="pt", max_length=1024, truncation=True)
    
    with torch.no_grad():
        hypotheses = model.generate(
            **inputs, 
            num_beams=5, 
            max_length=200, 
            min_length=30, 
            no_repeat_ngram_size=3
        )
    
    return tokenizer.decode(hypotheses[0], skip_special_tokens=True)