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

# Используем переменные из твоего .env
API_TOKEN = os.getenv("TG_TOKEN")
API_URL = os.getenv("API_URL")
DB_URL = os.getenv("DATABASE_URL")

if not API_TOKEN:
    exit("Error: TG_TOKEN not found in .env file.")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Установка меню команд (появится кнопка "Меню" в Telegram)
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
        "👋 Привет! Я бот для суммаризации текста.\n\n"
        "Пришлите мне текст, и я сделаю краткую выжимку.\n"
        "Команда /history покажет ваши последние запросы."
    )

@dp.message(Command("help"))
async def send_help(message: types.Message):
    await message.reply(
        "📖 **Как это работает:**\n"
        "1. Отправьте любой текст (длиной от 10 символов).\n"
        "2. Бот отправит его на ML-сервер.\n"
        "3. Вы получите результат, а данные сохранятся в MLflow.\n\n"
        "С помощью /history можно увидеть статистику последних обработок."
    )

@dp.message(Command("history"))
async def show_history(message: types.Message):
    if not DB_URL:
        await message.reply("🛑 Ошибка: DATABASE_URL не настроен.")
        return

    try:
        # Подключаемся к базе по данным из .env
        conn = await asyncpg.connect(DB_URL)
        
        # SQL запрос к таблицам MLflow для получения статистики
        # Мы берем время старта и параметры длины из таблицы params
        query = """
            SELECT r.start_time, 
                   MAX(CASE WHEN p.key = 'input_len' THEN p.value END) as in_len,
                   MAX(CASE WHEN p.key = 'output_len' THEN p.value END) as out_len
            FROM runs r
            JOIN params p ON r.run_uuid = p.run_uuid
            WHERE r.status = 'FINISHED'
            GROUP BY r.run_uuid, r.start_time
            ORDER BY r.start_time DESC
            LIMIT 5;
        """
        
        rows = await conn.fetch(query)
        await conn.close()

        if not rows:
            await message.reply("История пуста. Сначала обработайте какой-нибудь текст!")
            return

        history_msg = "📜 **Последние 5 запросов из базы:**\n\n"
        for row in rows:
            # Преобразуем время из миллисекунд MLflow в человеческий формат
            date_str = datetime.fromtimestamp(row['start_time'] / 1000).strftime('%d.%m %H:%M')
            history_msg += f"🕒 {date_str} | Вход: {row['in_len']} | Выход: {row['out_len']}\n"

        await message.answer(history_msg, parse_mode="Markdown")

    except Exception as e:
        await message.answer(f"🛑 Ошибка БД: {e}")

@dp.message()
async def handle_text(message: types.Message):
    if not message.text or len(message.text) < 10:
        return

    status_msg = await message.answer("🤖 Секунду, анализирую текст...")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(API_URL, json={"text": message.text})
            
        if response.status_code == 200:
            summary = response.json().get("summary", "Нет результата.")
            await status_msg.edit_text(f"📝 **Результат:**\n\n{summary}", parse_mode="Markdown")
        else:
            await status_msg.edit_text(f"❌ Ошибка API: {response.status_code}")
            
    except Exception as e:
        await status_msg.edit_text(f"🛑 Ошибка соединения: {e}")

async def main():
    await set_main_menu(bot)
    print(f"Бот запущен. Используется API: {API_URL}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен.")