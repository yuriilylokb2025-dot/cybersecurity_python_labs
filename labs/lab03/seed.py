import json
import sqlite3
from contextlib import closing
from pathlib import Path

from labs.lab03.database import get_connection, initialize_database

SEED_PATH = Path(__file__).resolve().parent / "data" / "seed.json"


def load_seed_data() -> tuple[list[dict], list[dict]]:
    """Зчитати та перевірити початкові дані."""
    data = json.loads(SEED_PATH.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise TypeError("Коренем JSON має бути об'єкт.")

    if set(data) != {"categories", "records"}:
        raise ValueError("JSON повинен містити categories і records.")

    categories = data["categories"]
    records = data["records"]

    if not isinstance(categories, list) or len(categories) != 3:
        raise ValueError("Потрібно рівно 3 категорії.")

    if not isinstance(records, list) or len(records) != 8:
        raise ValueError("Потрібно рівно 8 записів.")

    for category in categories:
        if not isinstance(category, dict) or set(category) != {"id", "name"}:
            raise ValueError("Некоректна структура категорії.")
        if type(category["id"]) is not int or category["id"] <= 0:
            raise ValueError("Некоректний id категорії.")
        if not isinstance(category["name"], str):
            raise TypeError("Некоректна назва категорії.")

    for record in records:
        required = {"code", "title", "category_id", "value", "status"}
        if not isinstance(record, dict) or set(record) != required:
            raise ValueError("Некоректна структура запису.")
        if not isinstance(record["code"], str):
            raise TypeError("Некоректний код запису.")
        if not isinstance(record["title"], str):
            raise TypeError("Некоректна назва запису.")
        if type(record["category_id"]) is not int:
            raise ValueError("Некоректна категорія запису.")
        if type(record["value"]) not in (int, float):
            raise ValueError("Некоректне числове значення.")
        if not 0 <= record["value"] <= 10:
            raise ValueError("Значення має бути від 0 до 10.")
        if record["status"] not in ("new", "in_progress", "done"):
            raise ValueError("Некоректний статус.")

    return categories, records


def seed_database() -> None:
    """Додати початкові дані однією транзакцією."""
    initialize_database()
    categories, records = load_seed_data()

    with closing(get_connection()) as connection:
        existing_categories = connection.execute(
            "SELECT COUNT(*) FROM categories"
        ).fetchone()[0]
        existing_records = connection.execute(
            "SELECT COUNT(*) FROM records"
        ).fetchone()[0]

        if existing_categories or existing_records:
            print("База вже містить дані. Повторне заповнення пропущено.")
            return

        try:
            with connection:
                connection.executemany(
                    "INSERT INTO categories (id, name) VALUES (?, ?)",
                    [(item["id"], item["name"]) for item in categories],
                )

                connection.executemany(
                    """
                    INSERT INTO records
                        (code, title, category_id, value, status)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            item["code"],
                            item["title"],
                            item["category_id"],
                            item["value"],
                            item["status"],
                        )
                        for item in records
                    ],
                )

        except sqlite3.IntegrityError as error:
            raise ValueError("Початкові дані порушують обмеження бази.") from error

    print("Базу заповнено: 3 категорії та 8 записів.")


if __name__ == "__main__":
    try:
        seed_database()
    except (OSError, TypeError, ValueError, sqlite3.Error) as error:
        print(f"Помилка заповнення бази: {error}")
        raise SystemExit(1) from None
