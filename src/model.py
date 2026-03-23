import torch
from transformers import T5ForConditionalGeneration, T5Tokenizer

def get_summarization(text):
    # Модель Rut5-base (намного легче mBART)
    model_name = "IlyaGusev/rut5_base_sum_gazeta"
    
    # Загружаем токенизатор и модель напрямую
    tokenizer = T5Tokenizer.from_pretrained(model_name)
    model = T5ForConditionalGeneration.from_pretrained(model_name)

    # Подготовка входного текста
    # Для T5 важно добавить префикс (хотя для этой модели он опционален)
    inputs = tokenizer(
        [text], 
        max_length=600, 
        add_special_tokens=True, 
        truncation=True, 
        return_tensors="pt"
    )

    # Генерация
    output_ids = model.generate(
        input_ids=inputs["input_ids"],
        attention_mask=inputs["attention_mask"],
        num_beams=5,
        max_length=200,
        no_repeat_ngram_size=4
    )[0]

    # Декодирование
    summary = tokenizer.decode(output_ids, skip_special_tokens=True)
    return summary

if __name__ == "__main__":
    test_text = """
    Сегодня в Москве прошла конференция по искусственному интеллекту. 
    Специалисты обсуждали внедрение нейросетей в образовательный процесс. 
    Особое внимание уделили МТУСИ, где запускается новая магистерская программа 
    по проектированию интеллектуальных систем.
    """
    
    print("--- Запуск модели T5 (Direct Load) ---")
    try:
        result = get_summarization(test_text)
        print("\nРезультат суммаризации:")
        print(result)
    except Exception as e:
        print(f"Критическая ошибка: {e}")