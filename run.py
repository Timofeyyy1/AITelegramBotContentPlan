import asyncio
import logging
from aiogram import Bot, Dispatcher

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Импорт конфигурации
from config import TG_TOKEN

# Импорт роутеров
from app.handlers.general_handlers import router as general_router
from app.handlers.content_plan_handlers import router as create_plan_router
from app.handlers.edit_plan_handler import router as edit_router

# Импорт инициализации БД
from app.database.models import init_db

bot = Bot(token=TG_TOKEN)
dp = Dispatcher()

async def main():
    # Инициализация БД
    logging.info("🔄 Инициализация базы данных...")
    await init_db()
    logging.info("✅ База данных инициализирована")

    # Подключение роутеров
    dp.include_router(general_router)
    dp.include_router(create_plan_router)
    dp.include_router(edit_router)

    print("🤖 Бот запущен...")
    await dp.start_polling(bot, drop_pending_updates=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Бот остановлен.")