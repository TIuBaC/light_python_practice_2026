import os
from pathlib import Path
from datetime import datetime
import sqlite3

def scan_folder(folder_path: Path, conn: sqlite3.Connection, ext_filter: str = None):
    """
    Главная функция сканирования.
    folder_path — папка, которую нужно обойти.
    conn — подключение к базе данных.
    ext_filter — необязательный фильтр по расширению, например ".txt"
    """

    # Получаем абсолютный путь к папке (без ./ и ../)
    folder_path = folder_path.resolve()
    count = 0  # Счётчик найденных файлов

    # os.walk обходит папку рекурсивно — заходит во все вложенные папки
    # root — текущая папка, dirs — список подпапок, files — список файлов
    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            # Собираем полный путь к файлу
            full_path = Path(root) / filename

            # Если задан фильтр по расширению — пропускаем файлы, которые не подходят
            if ext_filter and full_path.suffix.lower() != ext_filter.lower():
                continue

            try:
                # relative_path — путь относительно корневой папки сканирования
                # Например: "подпапка\файл.txt" вместо полного пути
                relative_path = str(full_path.relative_to(folder_path))

                # Размер файла в байтах
                size = full_path.stat().st_size

                # Дата последнего изменения файла, переведённая в читаемый формат
                modified_at = datetime.fromtimestamp(
                    full_path.stat().st_mtime
                ).strftime("%Y-%m-%d %H:%M:%S")

                # Расширение файла (.txt, .jpg и т.д.), или None если его нет
                extension = full_path.suffix.lower() or None

                # INSERT OR IGNORE — если файл уже есть в базе (по relative_path),
                # он не добавится повторно, просто пропустится
                conn.execute("""
                    INSERT OR IGNORE INTO files
                        (relative_path, size, modified_at, extension)
                    VALUES (?, ?, ?, ?)
                """, (relative_path, size, modified_at, extension))

                count += 1

                # Выводим информацию о каждом файле в консоль
                print(f"  [{extension or 'без расш.'}] {relative_path} — {size} байт")

            except Exception as e:
                # Если файл недоступен (нет прав и т.д.) — пропускаем и сообщаем
                print(f"  Пропущен: {full_path} ({e})")

    # Сохраняем все изменения в базу данных
    conn.commit()
    print(f"\nСканирование завершено. Найдено файлов: {count}")