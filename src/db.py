import sqlite3
from pathlib import Path

# Схема базы данных — две таблицы:
# files — индекс файлов из отсканированной папки
# backup_checks — история сравнений с резервной копией
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

CREATE TABLE IF NOT EXISTS backup_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    checked_at TEXT NOT NULL,
    source_folder TEXT NOT NULL,
    backup_folder TEXT NOT NULL,
    status TEXT NOT NULL,
    relative_path TEXT NOT NULL
);
"""

def init_db(db_path: Path) -> sqlite3.Connection:
    # Если папки data/ ещё нет — создать её
    db_path.parent.mkdir(parents=True, exist_ok=True)
    # Подключение к базе. Если файла нет — SQLite создаст его сам
    conn = sqlite3.connect(db_path)
    # Создаём таблицы если их ещё нет
    conn.executescript(SCHEMA)
    conn.commit()
    return conn