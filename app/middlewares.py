from aiogram import BaseMiddleware
from aiogram.types import Message
from database import Database

class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data: dict):
        print(f"Получено сообщение: {event.text}")
        return await handler(event, data)

class DatabaseMiddleware(BaseMiddleware):
    def __init__(self, database: Database):
        self.database = database

    async def __call__(self, handler, event, data):
        data["db"] = self.database
        return await handler(event, data)