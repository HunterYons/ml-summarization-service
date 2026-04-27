import os
import asyncio
import httpx
import asyncpg
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import BotCommand
from dotenv import load_dotenv

load_dotenv()

# Переменные окружения
API_TOKEN = os.getenv("TG_TOKEN")
API_URL = os.getenv("API_URL")
DB_URL = os.getenv("DATABASE_URL")

if not API_TOKEN:
    exit("Error: TG_TOKEN not found in .env file.")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Установка меню команд
async def set_main_menu(bot: Bot):
    main_menu_commands = [
        BotCommand(command="/start", description="Запустить бота"),
        BotCommand(command="/history", description="Показать историю"),
        BotCommand(command="/help", description="Инструкция")
    ]
    await bot.set_my_commands(main_menu_commands)

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.reply(
        "👋 Привет! Я продвинутый бот для суммаризации.\n\n"
        "Я не просто сокращаю текст, но и оцениваю **семантическую близость** результата к оригиналу с помощью SBERT.\n"
        "Пришлите текст, и я проанализирую его."
    )

@dp.message(Command("help"))
async def send_help(message: types.Message):
    await message.reply(
        "📖 **Как это работает:**\n"
        "1. Отправьте текст (от 10 символов).\n"
        "2. API выполнит пакетную обработку (Batching).\n"
        "3. Вы получите краткую выжимку и **коэффициент точности (0.0 - 1.0)**.\n"
        "4. Все данные и метрики улетят в MLflow."
    )

@dp.message(Command("history"))
async def show_history(message: types.Message):
    if not DB_URL:
        await message.reply("🛑 Ошибка: DATABASE_URL не настроен.")
        return

    try:
        conn = await asyncpg.connect(DB_URL)
        
        # Обновленный запрос: теперь мы можем вытягивать метрику semantic_similarity
        # Примечание: названия таблиц и ключей зависят от внутренней структуры MLflow
        query = """
            SELECT r.start_time, 
                   MAX(CASE WHEN m.key = 'semantic_similarity' THEN m.value END) as precision,
                   MAX(CASE WHEN m.key = 'latency_sec' THEN m.value END) as speed
            FROM runs r
            JOIN metrics m ON r.run_uuid = m.run_uuid
            WHERE r.status = 'FINISHED'
            GROUP BY r.run_uuid, r.start_time
            ORDER BY r.start_time DESC
            LIMIT 5;
        """
        
        rows = await conn.fetch(query)
        await conn.close()

        if not rows:
            await message.reply("История пока пуста.")
            return

        history_msg = "📜 **Последние 5 анализов:**\n\n"
        for row in rows:
            date_str = datetime.fromtimestamp(row['start_time'] / 1000).strftime('%d.%m %H:%M')
            # Форматируем вывод точности
            precision = f"{row['precision']:.4f}" if row['precision'] else "н/д"
            history_msg += f"🕒 {date_str} | Точность: `{precision}` | Время: `{row['speed']:.2f}s`\n"

        await message.answer(history_msg, parse_mode="Markdown")

    except Exception as e:
        await message.answer(f"🛑 Ошибка при чтении метрик: {e}")

@dp.message()
async def handle_text(message: types.Message):
    if not message.text or len(message.text) < 10:
        return

    status_msg = await message.answer("🤖 Секунду, анализирую смысл текста...")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Отправляем запрос в API
            response = await client.post(API_URL, json={"text": message.text})
            
        if response.status_code == 200:
            data = response.json()
            summary = data.get("summary", "Нет результата.")
            # Извлекаем нашу новую семантическую метрику
            metrics = data.get("metrics", {})
            semantic_score = metrics.get("semantic_similarity", 0)
            latency = metrics.get("latency_sec", 0)

            # Формируем красивый ответ с метриками
            result_text = (
                f"📝 **Результат суммаризации:**\n\n{summary}\n\n"
                f"--- \n"
                f"🎯 **Семантическая близость:** `{semantic_score:.4f}`\n"
                f"⚡ **Скорость обработки:** `{latency:.3f} сек.`"
            )
            await status_msg.edit_text(result_text, parse_mode="Markdown")
        else:
            await status_msg.edit_text(f"❌ Ошибка API: {response.status_code}")
            
    except Exception as e:
        await status_msg.edit_text(f"🛑 Ошибка соединения: {e}")

async def main():
    await set_main_menu(bot)
    print(f"Бот запущен. Ожидание сообщений...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен.")