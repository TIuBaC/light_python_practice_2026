import sys
from pathlib import Path
from db import init_db
from scanner import scan_folder
from duplicates import update_hashes, find_duplicates
from backup import compare_folders

# Путь к файлу базы данных: папка data/ в корне проекта
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "app.db"

def main():
    # sys.argv[1] — путь к папке (обязательный)
    # sys.argv[2] — путь к бэкапу (необязательный)
    # sys.argv[3] — фильтр по расширению, например .txt (необязательный)
    if len(sys.argv) < 2:
        print("Использование: python main.py <путь_к_папке> [путь_к_бэкапу] [расширение]")
        sys.exit(1)

    folder_path = Path(sys.argv[1])

    if not folder_path.exists() or not folder_path.is_dir():
        print(f"Папка не найдена: {folder_path}")
        sys.exit(1)

    # Разбираем необязательные аргументы
    # Если аргумент начинается с точки — это фильтр расширения (.txt)
    # Если нет — это путь к бэкапу
    backup_path = None
    ext_filter = None

    for arg in sys.argv[2:]:
        if arg.startswith("."):
            ext_filter = arg
        else:
            backup_path = Path(arg)

    print(f"Папка для сканирования: {folder_path}")
    if ext_filter:
        print(f"Фильтр по расширению: {ext_filter}")

    # Инициализируем базу данных
    conn = init_db(DB_PATH)
    print(f"База данных готова: {DB_PATH}\n")

    # Этап 2: сканируем папку и сохраняем файлы в базу
    scan_folder(folder_path, conn, ext_filter)

    # Выводим данные из базы для проверки
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

    # Этап 4: сравнение с резервной копией (если указан бэкап)
    if backup_path:
        if not backup_path.exists() or not backup_path.is_dir():
            print(f"\nПапка бэкапа не найдена: {backup_path}")
        else:
            print("\n--- Сравнение с резервной копией ---\n")
            compare_folders(folder_path, backup_path, conn)
    else:
        print("\nПодсказка: укажи второй аргумент — путь к бэкапу — чтобы запустить сравнение.")

    conn.close()

if __name__ == "__main__":
    main()