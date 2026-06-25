import sys
from pathlib import Path
from db import init_db
from scanner import scan_folder
from duplicates import update_hashes, find_duplicates

# Путь к файлу базы данных: папка data/ в корне проекта (рядом с src/)
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "app.db"

def main():
    # sys.argv[0] — сам файл main.py
    # sys.argv[1] — путь к папке (обязательный)
    # sys.argv[2] — фильтр по расширению (необязательный, например .txt)
    if len(sys.argv) < 2:
        print("Использование: python main.py <путь_к_папке> [расширение]")
        print("Пример: python main.py C:\\Users\\Мат\\Desktop .txt")
        sys.exit(1)

    folder_path = Path(sys.argv[1])

    # Проверяем, что папка существует и это действительно папка, а не файл
    if not folder_path.exists() or not folder_path.is_dir():
        print(f"Папка не найдена: {folder_path}")
        sys.exit(1)

    # Читаем фильтр по расширению, если он был передан (необязательно)
    ext_filter = sys.argv[2] if len(sys.argv) >= 3 else None

    print(f"Папка для сканирования: {folder_path}")
    if ext_filter:
        print(f"Фильтр по расширению: {ext_filter}")

    # Инициализируем базу данных (создаём файл и таблицу, если их нет)
    conn = init_db(DB_PATH)
    print(f"База данных готова: {DB_PATH}\n")

    # Этап 2: сканируем папку и сохраняем файлы в базу
    scan_folder(folder_path, conn, ext_filter)

    # Читаем из базы и выводим сохранённые данные для проверки
    print("\nДанные в базе данных:")
    print("-" * 60)
    for row in conn.execute("SELECT relative_path, size, modified_at, extension FROM files"):
        print(f"Файл:      {row[0]}")
        print(f"Размер:    {row[1]} байт")
        print(f"Изменён:   {row[2]}")
        print(f"Расш.:     {row[3] or '—'}")
        print("-" * 60)

    # Этап 3: считаем хэши и ищем дубликаты
    print("\n--- Поиск дубликатов ---\n")
    update_hashes(folder_path, conn)
    find_duplicates(conn)

    conn.close()

if __name__ == "__main__":
    main()