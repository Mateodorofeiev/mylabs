"""Налаштування варіанта 5: облік спрацювань засобів захисту."""

from typing import Literal

VARIANT_NUMBER = 5
DOMAIN = "Облік спрацювань засобів захисту"
UNIT = "events"
THRESHOLD = 15

# Межі value: кількість спрацювань, ціле число >= 0
VALUE_MIN = 0
# Верхньої межі в завданні немає, але SQLite зберігає цілі до 2**63 - 1.
# Без цієї межі дуже велике число спричинить OverflowError і відповідь 500.
VALUE_MAX = 2**63 - 1

# Дозволені статуси (збігаються з CHECK у schema.sql)
Status = Literal["new", "in_progress", "done"]
STATUSES = ("new", "in_progress", "done")

# Обмеження рядків (збігаються зі schema.sql)
CATEGORY_NAME_MIN, CATEGORY_NAME_MAX = 2, 40
CODE_MIN, CODE_MAX = 3, 40
TITLE_MIN, TITLE_MAX = 3, 120

# Обмеження API
SEARCH_MIN, SEARCH_MAX = 1, 120   # параметр q
LIMIT_DEFAULT, LIMIT_MAX = 20, 100
BULK_MIN, BULK_MAX = 1, 100

# Опис для Swagger
APP_TITLE = "Облік спрацювань засобів захисту"
APP_DESCRIPTION = (
    "Сервіс зберігає кількість спрацювань засобів захисту "
    "(firewall, ids, antivirus) за навчальні інтервали. "
    "Поле value — кількість спрацювань (одиниця: events, ціле число >= 0). "
    f"Поріг для аналізу: {THRESHOLD}. "
    "Статус описує стан перевірки підсумкового запису."
)