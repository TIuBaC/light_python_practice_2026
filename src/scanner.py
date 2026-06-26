from pathlib import Path
from datetime import datetime
import sqlite3


def collect_files(folder_path: Path) -> list:
    """
    Рекурсивно обходит папку вручную и возвращает список всех файлов.
    Используем iterdir() — он показывает содержимое папки (один уровень).
    Если встречаем подпапку — вызываем функцию снова для неё (рекурсия).
    Если встречаем файл — добавляем в список.
    """
    result = []
    for item in folder_path.iterdir():
        if item.is_dir():
            # Это папка — заходим в неё и добавляем всё что нашли внутри
            result.extend(collect_files(item))
        elif item.is_file():
            # Это файл — добавляем в список
            result.append(item)
    return result


def scan_folder(folder_path: Path, conn: sqlite3.Connection, ext_filter: str = None):
    """
    Главная функция сканирования.
    folder_path — папка, которую нужно обойти.
    conn — подключение к базе данных.
    ext_filter — необязательный фильтр по расширению, например ".txt"
    """
    folder_path = folder_path.resolve()
    count = 0

    # Получаем список всех файлов через нашу рекурсивную функцию
    all_files = collect_files(folder_path)

    for full_path in all_files:
        # Если задан фильтр — пропускаем файлы с другим расширением
        if ext_filter and full_path.suffix.lower() != ext_filter.lower():
            continue

        try:
            # Относительный путь — без корневой папки
            relative_path = str(full_path.relative_to(folder_path))

            # Размер файла в байтах
            size = full_path.stat().st_size

            # Дата последнего изменения в читаемом формате
            modified_at = datetime.fromtimestamp(
                full_path.stat().st_mtime
            ).strftime("%Y-%m-%d %H:%M:%S")

            # Расширение файла (.txt, .jpg и т.д.)
            extension = full_path.suffix.lower() or None

            # Сохраняем в базу. INSERT OR IGNORE — не дублируем если уже есть
            conn.execute("""
                INSERT OR IGNORE INTO files
                    (relative_path, size, modified_at, extension)
                VALUES (?, ?, ?, ?)
            """, (relative_path, size, modified_at, extension))

            count += 1
            print(f"  [{extension or 'без расш.'}] {relative_path} — {size} байт")

        except Exception as e:
            print(f"  Пропущен: {full_path} ({e})")

    conn.commit()
    print(f"\nСканирование завершено. Найдено файлов: {count}")