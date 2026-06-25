import sys
from pathlib import Path

from db import init_db

# Путь к файлу базы данных: папка data/ в корне проекта (рядом с src/)
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "app.db"


def main():
    # sys.argv — это список того, что было написано при запуске программы.
    # sys.argv[0] — это сам файл main.py, а sys.argv[1] — первый аргумент (путь к папке).
    if len(sys.argv) < 2:
        print("Использование: python main.py <путь_к_папке>")
        sys.exit(1)

    folder_path = Path(sys.argv[1])

    if not folder_path.exists() or not folder_path.is_dir():
        print(f"Папка не найдена: {folder_path}")
        sys.exit(1)

    print(f"Папка для сканирования: {folder_path}")

    conn = init_db(DB_PATH)
    print(f"База данных готова: {DB_PATH}")
    conn.close()


if __name__ == "__main__":
    main()