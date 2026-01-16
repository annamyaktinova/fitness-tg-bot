import aiosqlite
from typing import Dict, Any

class Database:
    def __init__(self, db_path: str = "users.db"):
        self.db_path = db_path

    async def create_table(self):
        async with aiosqlite.connect(self.db_path) as db:
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
                    logged_water INTEGER DEFAULT 0,
                    logged_calories REAL DEFAULT 0,
                    burned_calories REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            await db.commit()

    async def get_user(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ) as cursor:
                user = await cursor.fetchone()
                if user is not None:
                    columns = [column[0] for column in cursor.description]
                    return dict(zip(columns, user))
                return None

    async def log_water(self, logged_water: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE users SET logged_water = ?", (logged_water,))
            await db.commit()

    async def log_calories(self, logged_calories: float):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET logged_calories = ?",
                (logged_calories,)
            )
            await db.commit()

    async def log_workout(self, burned_calories: float, water_goal: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET burned_calories = ?, water_goal = ?",
                (burned_calories, water_goal)
            )
            await db.commit()