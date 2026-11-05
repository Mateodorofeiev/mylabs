"""FastAPI-застосунок: облік спрацювань засобів захисту (варіант 5)."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from shared import student

from .config import APP_DESCRIPTION, APP_TITLE
from .database import initialize_database
from .routers import categories, records


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Створити відсутні таблиці під час запуску (дані не змінюються)."""
    initialize_database()
    yield


app = FastAPI(title=APP_TITLE, description=APP_DESCRIPTION, lifespan=lifespan)

app.include_router(categories.router)
app.include_router(records.router)


@app.get("/ping", summary="Перевірка доступності API", tags=["service"])
def ping() -> dict[str, str]:
    """Повернути статус сервісу."""
    return {"status": "ok"}


@app.get("/student", summary="Дані студента", tags=["service"])
def get_student() -> dict[str, str | int]:
    """Повернути ПІБ, групу та номер варіанта."""
    return {
        "student_name": student.STUDENT_NAME,
        "group_name": student.GROUP_NAME,
        "variant_number": student.VARIANT_NUMBER,
    }