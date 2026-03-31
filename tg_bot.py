import asyncio
import httpx
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

API_TOKEN = '8711847908:AAFU2bvDf8ivwoJbCW4WdQQEwlO55TRmAas'
API_URL = "http://127.0.0.1:8000/summarize"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.reply("Привет! Пришли мне длинный текст на русском, и я его сокращу.")

@dp.message()
async def handle_text(message: types.Message):
    if not message.text: return
    
    status_msg = await message.answer("🤖 Модель думает...")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(API_URL, json={"text": message.text})
            
        if response.status_code == 200:
            summary = response.json().get("summary", "Ошибка в ответе")
            await status_msg.edit_text(f"📝 **Краткое содержание:**\n\n{summary}", parse_mode="Markdown")
        else:
            await status_msg.edit_text("❌ Ошибка сервера API.")
    except Exception as e:
        await status_msg.edit_text(f"🛑 Не удалось связаться с API: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())