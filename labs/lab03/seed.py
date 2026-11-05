"""Початкове заповнення бази з data/seed.json."""

import json
import sqlite3
from contextlib import closing
from pathlib import Path

from labs.lab03.database import get_connection, initialize_database

SEED_PATH = Path(__file__).resolve().parent / "data" / "seed.json"
STATUSES = {"new", "in_progress", "done"}


def load_seed() -> dict:
    """Прочитати й перевірити початкові дані."""
    data = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    categories = data.get("categories")
    records = data.get("records")
    if not isinstance(categories, list) or len(categories) != 3:
        raise ValueError("Очікується рівно 3 категорії")
    if not isinstance(records, list) or len(records) != 8:
        raise ValueError("Очікується рівно 8 записів")
    category_ids = set()
    for item in categories:
        if not isinstance(item.get("id"), int) or isinstance(item["id"], bool):
            raise ValueError("id категорії має бути цілим числом")
        if not isinstance(item.get("name"), str):
            raise ValueError("name категорії має бути рядком")
        category_ids.add(item["id"])
    for item in records:
        value = item.get("value")
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f"Некоректне value у {item.get('code')}")
        if item.get("category_id") not in category_ids:
            raise ValueError(f"Невідома категорія у {item.get('code')}")
        if item.get("status") not in STATUSES:
            raise ValueError(f"Некоректний статус у {item.get('code')}")
        if not isinstance(item.get("code"), str) or not isinstance(
            item.get("title"), str
        ):
            raise ValueError("code і title мають бути рядками")
    return data


def seed_database() -> None:
    """Заповнити порожню базу в одній транзакції."""
    try:
        data = load_seed()
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"Помилка початкових даних: {error}")
        return

    initialize_database()
    with closing(get_connection()) as connection:
        categories_count = connection.execute(
            "SELECT COUNT(*) FROM categories"
        ).fetchone()[0]
        records_count = connection.execute("SELECT COUNT(*) FROM records").fetchone()[0]
        if categories_count or records_count:
            print("База вже заповнена, зміни не виконувалися.")
            return
        try:
            with connection:
                connection.executemany(
                    "INSERT INTO categories (id, name) VALUES (?, ?)",
                    [(c["id"], c["name"]) for c in data["categories"]],
                )
                connection.executemany(
                    "INSERT INTO records (code, title, category_id, value, status) "
                    "VALUES (?, ?, ?, ?, ?)",
                    [
                        (r["code"], r["title"], r["category_id"], r["value"], r["status"])
                        for r in data["records"]
                    ],
                )
        except sqlite3.Error as error:
            print(f"Помилка заповнення, зміни скасовано: {error}")
            return
    print("Додано 3 категорії та 8 записів.")


if __name__ == "__main__":
    seed_database()