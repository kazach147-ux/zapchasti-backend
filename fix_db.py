import sqlite3
import os

db_path = "app/database.db"

if not os.path.exists(db_path):
    print(f"Файл базы не найден по пути: {os.path.abspath(db_path)}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE categories ADD COLUMN image TEXT")
        conn.commit()
        print("Колонка image успешно добавлена")
    except sqlite3.OperationalError as e:
        print(f"Ошибка или уже есть: {e}")
    finally:
        conn.close()