"""Параметризовані SQL-запити до бази даних."""

import sqlite3
from contextlib import closing

from .database import get_connection

RECORD_SELECT = """
SELECT r.id, r.code, r.title, r.category_id, r.value, r.status,
       c.name AS category_name
FROM records AS r
JOIN categories AS c ON c.id = r.category_id
"""


class NotFoundError(Exception):
    """Запис або категорія не існує."""


class ConflictError(Exception):
    """Порушення унікальності або спроба видалити непорожню категорію."""


def _row_to_dict(row: sqlite3.Row | tuple) -> dict:
    keys = ("id", "code", "title", "category_id", "value", "status", "category_name")
    return dict(zip(keys, row, strict=True))


def _category_exists(connection: sqlite3.Connection, category_id: int) -> bool:
    row = connection.execute(
        "SELECT 1 FROM categories WHERE id = ?", (category_id,)
    ).fetchone()
    return row is not None


def _fetch_record(connection: sqlite3.Connection, record_id: int) -> dict | None:
    row = connection.execute(
        RECORD_SELECT + " WHERE r.id = ?", (record_id,)
    ).fetchone()
    return _row_to_dict(row) if row else None


# ---------- Категорії ----------

def list_categories() -> list[dict]:
    """Усі категорії за зростанням id."""
    with closing(get_connection()) as connection:
        rows = connection.execute(
            "SELECT id, name FROM categories ORDER BY id"
        ).fetchall()
    return [{"id": r[0], "name": r[1]} for r in rows]


def create_category(name: str) -> dict:
    """Створити категорію; дублікат назви дає ConflictError."""
    with closing(get_connection()) as connection:
        try:
            with connection:
                cursor = connection.execute(
                    "INSERT INTO categories (name) VALUES (?)", (name,)
                )
        except sqlite3.IntegrityError as exc:
            raise ConflictError("Категорія з такою назвою вже існує") from exc
        return {"id": cursor.lastrowid, "name": name}


def delete_category(category_id: int) -> None:
    """Видалити порожню категорію."""
    with closing(get_connection()) as connection:
        try:
            with connection:
                cursor = connection.execute(
                    "DELETE FROM categories WHERE id = ?", (category_id,)
                )
        except sqlite3.IntegrityError as exc:
            raise ConflictError("Категорія містить записи") from exc
        if cursor.rowcount == 0:
            raise NotFoundError("Категорію не знайдено")


# ---------- Записи ----------

def get_record(record_id: int) -> dict:
    """Отримати запис за id."""
    with closing(get_connection()) as connection:
        record = _fetch_record(connection, record_id)
    if record is None:
        raise NotFoundError("Запис не знайдено")
    return record


def list_records(
    category_id: int | None,
    status: str | None,
    min_value: int | None,
    q: str | None,
    limit: int,
    offset: int,
) -> list[dict]:
    """Список записів з фільтрами (AND) і пагінацією."""
    conditions: list[str] = []
    params: list = []
    if category_id is not None:
        conditions.append("r.category_id = ?")
        params.append(category_id)
    if status is not None:
        conditions.append("r.status = ?")
        params.append(status)
    if min_value is not None:
        conditions.append("r.value >= ?")
        params.append(min_value)
    if q is not None:
        conditions.append("instr(r.title, ?) > 0")
        params.append(q)

    sql = RECORD_SELECT
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY r.id LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with closing(get_connection()) as connection:
        rows = connection.execute(sql, params).fetchall()
    return [_row_to_dict(r) for r in rows]


def create_record(data: dict) -> dict:
    """Створити запис."""
    return create_records_bulk([data])[0]


def create_records_bulk(items: list[dict]) -> list[dict]:
    """Додати всі записи в одній транзакції або жодного."""
    with closing(get_connection()) as connection:
        try:
            with connection:
                new_ids: list[int] = []
                for item in items:
                    if not _category_exists(connection, item["category_id"]):
                        raise NotFoundError("Категорію не знайдено")
                    cursor = connection.execute(
                        "INSERT INTO records (code, title, category_id, value, status) "
                        "VALUES (?, ?, ?, ?, ?)",
                        (
                            item["code"],
                            item["title"],
                            item["category_id"],
                            item["value"],
                            item["status"],
                        ),
                    )
                    new_ids.append(cursor.lastrowid)
        except sqlite3.IntegrityError as exc:
            raise ConflictError("Запис з таким code вже існує") from exc
        return [_fetch_record(connection, record_id) for record_id in new_ids]


def replace_record(record_id: int, data: dict) -> dict:
    """Повністю замінити змінювані поля запису."""
    with closing(get_connection()) as connection:
        try:
            with connection:
                if _fetch_record(connection, record_id) is None:
                    raise NotFoundError("Запис не знайдено")
                if not _category_exists(connection, data["category_id"]):
                    raise NotFoundError("Категорію не знайдено")
                connection.execute(
                    "UPDATE records SET code = ?, title = ?, category_id = ?, "
                    "value = ?, status = ? WHERE id = ?",
                    (
                        data["code"],
                        data["title"],
                        data["category_id"],
                        data["value"],
                        data["status"],
                        record_id,
                    ),
                )
        except sqlite3.IntegrityError as exc:
            raise ConflictError("Запис з таким code вже існує") from exc
        return _fetch_record(connection, record_id)


def delete_record(record_id: int) -> None:
    """Видалити запис."""
    with closing(get_connection()) as connection:
        with connection:
            cursor = connection.execute(
                "DELETE FROM records WHERE id = ?", (record_id,)
            )
        if cursor.rowcount == 0:
            raise NotFoundError("Запис не знайдено")