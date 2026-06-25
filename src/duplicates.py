import hashlib
from pathlib import Path
import sqlite3

def calculate_hash(file_path: Path) -> str:
    """
    Считает MD5-хэш файла — это уникальный "отпечаток" содержимого файла.
    Если два файла имеют одинаковый хэш — их содержимое абсолютно идентично.
    Файл читается частями (chunk), чтобы не загружать большие файлы целиком в память.
    """
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        # Читаем файл блоками по 8192 байт
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


def update_hashes(folder_path: Path, conn: sqlite3.Connection):
    """
    Проходит по всем файлам в базе данных, считает хэш каждого
    и сохраняет его в колонку file_hash таблицы files.
    Если хэш уже посчитан ранее — пропускает файл (экономия времени).
    """
    folder_path = folder_path.resolve()

    # Берём из базы все файлы, у которых хэш ещё не посчитан
    rows = conn.execute(
        "SELECT id, relative_path FROM files WHERE file_hash IS NULL"
    ).fetchall()

    print(f"Считаем хэши для {len(rows)} файлов...")

    for row in rows:
        file_id = row[0]
        relative_path = row[1]
        full_path = folder_path / relative_path

        try:
            file_hash = calculate_hash(full_path)

            # Записываем хэш в базу для этого файла
            conn.execute(
                "UPDATE files SET file_hash = ? WHERE id = ?",
                (file_hash, file_id)
            )
            print(f"  Хэш посчитан: {relative_path}")

        except Exception as e:
            print(f"  Пропущен: {relative_path} ({e})")

    conn.commit()
    print("Хэши сохранены в базу данных.\n")


def find_duplicates(conn: sqlite3.Connection):
    """
    Ищет дубликаты: файлы с одинаковым хэшем — это одинаковые файлы.
    Группирует их и выводит в консоль.
    """

    # Запрос: найти хэши, которые встречаются у двух и более файлов
    duplicate_hashes = conn.execute("""
        SELECT file_hash, COUNT(*) as cnt
        FROM files
        WHERE file_hash IS NOT NULL
        GROUP BY file_hash
        HAVING cnt >= 2
    """).fetchall()

    if not duplicate_hashes:
        print("Дубликатов не найдено.")
        return

    print(f"Найдено групп дубликатов: {len(duplicate_hashes)}")
    print("=" * 60)

    for hash_row in duplicate_hashes:
        file_hash = hash_row[0]

        # Получаем все файлы с этим хэшем
        files = conn.execute(
            "SELECT relative_path, size FROM files WHERE file_hash = ?",
            (file_hash,)
        ).fetchall()

        print(f"Хэш: {file_hash}")
        for f in files:
            print(f"  — {f[0]}  ({f[1]} байт)")
        print("-" * 60)