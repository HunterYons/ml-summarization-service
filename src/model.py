import torch
from transformers import MBartTokenizer, MBartForConditionalGeneration

def get_summarization(text):
    # Используем проверенную модель для русского языка
    model_name = "IlyaGusev/mbart_ru_sum_gazeta"
    
    # Загружаем токенизатор и саму модель
    tokenizer = MBartTokenizer.from_pretrained(model_name)
    model = MBartForConditionalGeneration.from_pretrained(model_name)

    # Токенизация входного текста (с ограничением длины)
    input_ids = tokenizer(
        [text],
        max_length=1024,
        padding="max_length",
        truncation=True,
        return_tensors="pt"
    )["input_ids"]

    # Генерация текста (параметры для улучшения качества)
    output_ids = model.generate(
        input_ids=input_ids,
        no_repeat_ngram_size=4,
        num_beams=5
    )[0]

    # Перевод из токенов в понятный текст
    summary = tokenizer.decode(output_ids, skip_special_tokens=True)
    return summary

if __name__ == "__main__":
    # Тестовый пример
    test_text = "Вставьте сюда любую длинную новость для проверки"
    print("Результат суммаризации:")
    print(get_summarization(test_text))