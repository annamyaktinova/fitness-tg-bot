import aiosqlite
from typing import Dict, Any

class Database:
    def __init__(self, db_path: str = "users.db"):
        self.db_path = db_path

    async def create_tables(self):
        async with aiosqlite.connect(self.db_path) as db:
            #Профили пользователей
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    weight INTEGER,
                    height INTEGER,
                    age INTEGER,
                    gender TEXT,
                    activity INTEGER,
                    city TEXT,
                    water_goal INTEGER,
                    calorie_goal REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            #Логи
            await db.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                logged_water INTEGER DEFAULT 0,
                logged_calories REAL DEFAULT 0,
                burned_calories REAL DEFAULT 0,
                date DATE DEFAULT CURRENT_DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            """)
            await db.commit()

    async def save_user(self, user_id: int, data: Dict[str, Any]):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO users 
                (user_id, weight, height, age, gender, activity, city, water_goal, calorie_goal)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    data.get('weight'),
                    data.get('height'),
                    data.get('age'),
                    data.get('gender'),
                    data.get('activity'),
                    data.get('city'),
                    data.get('water_goal'),
                    data.get('calorie_goal')
                )
            )

            await db.execute(
                """
                INSERT OR REPLACE INTO logs 
                (user_id, logged_water, logged_calories, burned_calories, date)
                VALUES (?, 0, 0, 0, date('now'))
                """, (user_id,)
            )

            await db.commit()

    async def get_user(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            #Получаем данные о пользователе
            async with db.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ) as cursor:
                user = await cursor.fetchone()
                if user is not None:
                    columns = [column[0] for column in cursor.description]
                    return dict(zip(columns, user))
        return None

    async def get_today_logs(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT logged_water, logged_calories, burned_calories FROM logs WHERE user_id = ? AND date = date('now')",
                (user_id,)
            ) as cursor:
                result = await cursor.fetchone()
                columns = [column[0] for column in cursor.description]
                return dict(zip(columns, result))

    async def log_water(self, logged_water: int, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE logs SET logged_water = ? WHERE user_id = ? AND date = date('now')", 
                (logged_water, user_id)
            )
            await db.commit()

    async def log_calories(self, logged_calories: float, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE logs SET logged_calories = ? WHERE user_id = ? AND date = date('now')",
                (logged_calories, user_id)
            )
            await db.commit()

    async def log_workout(self, burned_calories: float, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE logs SET burned_calories = ? WHERE user_id = ? AND date = date('now')",
                (burned_calories, user_id)
            )
            await db.commit()

    async def get_weekly_logs(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                """
                SELECT date, logged_water, logged_calories, burned_calories 
                FROM logs 
                WHERE user_id = ? AND date >= date('now', '-6 days') 
                ORDER BY date
                """,
                (user_id,)
            ) as cursor:
                weekly_logs = await cursor.fetchall()

            water_logs = {row[0]: row[1] for row in weekly_logs}
            calorie_logs = {row[0]: row[2] for row in weekly_logs}
            burned_logs = {row[0]: row[3] for row in weekly_logs}

            return water_logs, calorie_logs, burned_logs
