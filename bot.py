import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import setup_handlers
from database import Database
from middlewares import LoggingMiddleware, DatabaseMiddleware

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    db = Database()
    await db.create_tables()

    dp.message.middleware(LoggingMiddleware())
    dp.message.middleware(DatabaseMiddleware(db))
    setup_handlers(dp)

    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())