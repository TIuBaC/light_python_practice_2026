import sqlite3
from pathlib import Path

# Схема — описание структуры таблицы.
# files — таблица, в которой будет храниться информация о каждом файле из папки.
SCHEMA = """
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    relative_path TEXT UNIQUE NOT NULL,
    size INTEGER NOT NULL,
    modified_at TEXT NOT NULL,
    extension TEXT,
    file_hash TEXT,
    status TEXT NOT NULL DEFAULT 'present'
);
"""


def init_db(db_path: Path) -> sqlite3.Connection:
    # Если папки data/ еще нет — создать её.
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Подключение к базе. Если файла app.db не существует — SQLite создаст его сам.
    conn = sqlite3.connect(db_path)

    # Выполнить SQL-команду создания таблицы (если её еще нет).
    conn.execute(SCHEMA)

    # Сохранить изменения. Без commit() изменения не запишутся в файл.
    conn.commit()

    return conn