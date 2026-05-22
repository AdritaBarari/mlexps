import sqlite3
from config import DB_PATH


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS profile (
            id INTEGER PRIMARY KEY DEFAULT 1,
            name TEXT DEFAULT 'User',
            daily_calorie_goal INTEGER DEFAULT 2000,
            protein_goal INTEGER DEFAULT 150,
            carbs_goal INTEGER DEFAULT 250,
            fat_goal INTEGER DEFAULT 65,
            whatsapp_number TEXT
        );

        INSERT OR IGNORE INTO profile (id) VALUES (1);

        CREATE TABLE IF NOT EXISTS meals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            meal_type TEXT DEFAULT 'meal',
            food_name TEXT NOT NULL,
            quantity TEXT,
            calories REAL DEFAULT 0,
            protein REAL DEFAULT 0,
            carbs REAL DEFAULT 0,
            fat REAL DEFAULT 0,
            fiber REAL DEFAULT 0,
            sugar REAL DEFAULT 0,
            logged_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            activity_type TEXT,
            steps INTEGER DEFAULT 0,
            duration_minutes INTEGER DEFAULT 0,
            calories_burned REAL DEFAULT 0,
            logged_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            ingredients_raw TEXT,
            servings INTEGER DEFAULT 1,
            calories_per_serving REAL DEFAULT 0,
            protein REAL DEFAULT 0,
            carbs REAL DEFAULT 0,
            fat REAL DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    conn.close()
