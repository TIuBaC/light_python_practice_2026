import hashlib
from pathlib import Path
import sqlite3
from datetime import datetime


def hash_file(file_path: Path) -> str:
    """
    Считает MD5-хэш файла — уникальный отпечаток его содержимого.
    Файл читается частями, чтобы не загружать большие файлы целиком в память.
    """
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


def scan_directory(folder_path: Path) -> dict:
    """
    Сканирует папку и возвращает словарь:
    ключ — относительный путь файла, значение — его MD5-хэш.
    Используется для сравнения двух папок между собой.
    """
    folder_path = folder_path.resolve()
    result = {}

    for file in folder_path.rglob("*"):
        if file.is_file():
            try:
                relative = str(file.relative_to(folder_path))
                result[relative] = hash_file(file)
            except Exception as e:
                print(f"  Пропущен: {file} ({e})")

    return result


def compare_folders(source_path: Path, backup_path: Path, conn: sqlite3.Connection):
    """
    Сравнивает исходную папку с резервной копией.
    Три категории различий:
    - missing: файл есть в источнике, но отсутствует в бэкапе (пропал из бэкапа)
    - changed: файл есть в обоих местах, но содержимое отличается (был изменён)
    - extra:   файл есть в бэкапе, но отсутствует в источнике (лишний в бэкапе)
    Все результаты сохраняются в таблицу backup_checks.
    """
    print("Сканируем исходную папку...")
    source_files = scan_directory(source_path)
    print(f"Файлов в источнике: {len(source_files)}")

    print("Сканируем резервную копию...")
    backup_files = scan_directory(backup_path)
    print(f"Файлов в бэкапе: {len(backup_files)}\n")

    checked_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    source_str = str(source_path.resolve())
    backup_str = str(backup_path.resolve())

    missing = []  # есть в источнике, нет в бэкапе
    changed = []  # есть в обоих, но хэши разные — файл изменился
    extra = []    # есть в бэкапе, нет в источнике — лишний файл

    # Проходим по файлам источника и сравниваем с бэкапом
    for path, src_hash in source_files.items():
        if path not in backup_files:
            missing.append(path)
        elif backup_files[path] != src_hash:
            changed.append(path)

    # Ищем файлы в бэкапе, которых нет в источнике
    for path in backup_files:
        if path not in source_files:
            extra.append(path)

    # Сохраняем все результаты в базу данных
    for path in missing:
        conn.execute(
            "INSERT INTO backup_checks (checked_at, source_folder, backup_folder, status, relative_path) VALUES (?, ?, ?, ?, ?)",
            (checked_at, source_str, backup_str, "missing", path)
        )
    for path in changed:
        conn.execute(
            "INSERT INTO backup_checks (checked_at, source_folder, backup_folder, status, relative_path) VALUES (?, ?, ?, ?, ?)",
            (checked_at, source_str, backup_str, "changed", path)
        )
    for path in extra:
        conn.execute(
            "INSERT INTO backup_checks (checked_at, source_folder, backup_folder, status, relative_path) VALUES (?, ?, ?, ?, ?)",
            (checked_at, source_str, backup_str, "extra", path)
        )

    conn.commit()

    # Итоговый отчёт в консоль
    print("=" * 60)
    print("ОТЧЁТ: Сравнение с резервной копией")
    print(f"Дата проверки: {checked_at}")
    print(f"Источник:      {source_str}")
    print(f"Бэкап:         {backup_str}")
    print("=" * 60)

    print(f"\n[ОТСУТСТВУЮТ В БЭКАПЕ] ({len(missing)}):")
    if missing:
        for path in missing:
            print(f"  - {path}")
    else:
        print("  нет")

    print(f"\n[ИЗМЕНЕНЫ] ({len(changed)}):")
    if changed:
        for path in changed:
            print(f"  - {path}")
    else:
        print("  нет")

    print(f"\n[ЛИШНИЕ В БЭКАПЕ] ({len(extra)}):")
    if extra:
        for path in extra:
            print(f"  - {path}")
    else:
        print("  нет")

    print("\n" + "=" * 60)
    print(f"Итого: пропавших — {len(missing)}, изменённых — {len(changed)}, лишних — {len(extra)}")
    print("Результаты сохранены в таблицу backup_checks.")
    print("=" * 60)