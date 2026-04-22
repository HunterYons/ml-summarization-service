import os
import asyncio
import httpx
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv

# 1. Загружаем переменные из .env
load_dotenv()

# 2. Получаем токен и URL из окружения
# Если в .env нет TG_TOKEN, программа выдаст понятную ошибку
API_TOKEN = os.getenv("TG_TOKEN")
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/summarize")

if not API_TOKEN:
    exit("Error: TG_TOKEN not found in .env file. Please check your configuration.")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.reply(
        "👋 Привет! Я бот для суммаризации текста.\n"
        "Пришли мне длинный текст на русском, и я сделаю его краткую выжимку."
    )

@dp.message()
async def handle_text(message: types.Message):
    if not message.text or len(message.text) < 10:
        return

    # Индикация работы для пользователя
    status_msg = await message.answer("🤖 Модель обрабатывает текст, пожалуйста, подождите...")
    
    try:
        # Устанавливаем увеличенный таймаут, так как ML-модель на CPU может думать долго
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                API_URL, 
                json={"text": message.text}
            )
            
        if response.status_code == 200:
            summary = response.json().get("summary", "Не удалось получить результат.")
            # Отправляем итоговый результат
            await status_msg.edit_text(f"📝 **Краткое содержание:**\n\n{summary}", parse_mode="Markdown")
        else:
            await status_msg.edit_text(f"❌ Ошибка API: Сервер вернул код {response.status_code}")
            
    except Exception as e:
        await status_msg.edit_text(f"🛑 Не удалось связаться с сервером ML: {str(e)}")

async def main():
    print(f"Бот запущен и обращается к API по адресу: {API_URL}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен.")