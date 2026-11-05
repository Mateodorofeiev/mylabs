"""Маршрути записів."""

import logging
import sqlite3
from typing import Annotated

from fastapi import APIRouter, Body, HTTPException, Path, Query, Response, status

from .. import repository
from ..config import (
    BULK_MAX,
    BULK_MIN,
    LIMIT_DEFAULT,
    LIMIT_MAX,
    SEARCH_MAX,
    SEARCH_MIN,
    VALUE_MAX,
    VALUE_MIN,
    Status,
)
from ..schemas import RecordCreate, RecordRead, RecordReplace

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/records", tags=["records"])

DB_ERROR = "Тимчасова помилка бази даних"

RecordId = Annotated[int, Path(gt=0, description="Ідентифікатор запису")]

NOT_FOUND = {404: {"description": "Запис або категорію не знайдено"}}
CONFLICT = {409: {"description": "Запис із таким code вже існує"}}


def _handle(exc: Exception) -> HTTPException:
    """Перетворити виняток шару даних на HTTP-помилку."""
    if isinstance(exc, repository.NotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, repository.ConflictError):
        return HTTPException(status_code=409, detail=str(exc))
    logger.error("Помилка бази даних", exc_info=exc)
    return HTTPException(status_code=500, detail=DB_ERROR)


@router.get("", response_model=list[RecordRead], summary="Список записів")
def list_records(
    category_id: Annotated[
        int | None, Query(gt=0, description="Лише записи цієї категорії")
    ] = None,
    status_filter: Annotated[
        Status | None, Query(alias="status", description="Лише записи з цим статусом")
    ] = None,
    min_value: Annotated[
        int | None,
        Query(ge=VALUE_MIN, le=VALUE_MAX, description="value >= min_value"),
    ] = None,
    q: Annotated[
        str | None,
        Query(
            min_length=SEARCH_MIN,
            max_length=SEARCH_MAX,
            description="Буквальний підрядок у title (з урахуванням регістру)",
        ),
    ] = None,
    limit: Annotated[
        int, Query(ge=1, le=LIMIT_MAX, description="Максимум записів")
    ] = LIMIT_DEFAULT,
    offset: Annotated[int, Query(ge=0, description="Скільки пропустити")] = 0,
) -> list[dict]:
    """Повернути записи з фільтрами (AND), відсортовані за id."""
    try:
        return repository.list_records(
            category_id, status_filter, min_value, q, limit, offset
        )
    except sqlite3.Error as exc:
        raise _handle(exc) from exc


@router.post(
    "/bulk",
    response_model=list[RecordRead],
    status_code=status.HTTP_201_CREATED,
    summary="Пакетне створення записів",
    responses={**NOT_FOUND, **CONFLICT},
)
def create_records_bulk(
    payload: Annotated[list[RecordCreate], Body(min_length=BULK_MIN, max_length=BULK_MAX)],
) -> list[dict]:
    """Атомарно створити від 1 до 100 записів: усі або жодного."""
    try:
        return repository.create_records_bulk([p.model_dump() for p in payload])
    except (repository.NotFoundError, repository.ConflictError, sqlite3.Error) as exc:
        raise _handle(exc) from exc


@router.post(
    "",
    response_model=RecordRead,
    status_code=status.HTTP_201_CREATED,
    summary="Створити запис",
    responses={**NOT_FOUND, **CONFLICT},
)
def create_record(payload: RecordCreate) -> dict:
    """Створити один запис."""
    try:
        return repository.create_record(payload.model_dump())
    except (repository.NotFoundError, repository.ConflictError, sqlite3.Error) as exc:
        raise _handle(exc) from exc


@router.get(
    "/{record_id}",
    response_model=RecordRead,
    summary="Отримати запис",
    responses=NOT_FOUND,
)
def get_record(record_id: RecordId) -> dict:
    """Повернути один запис за id."""
    try:
        return repository.get_record(record_id)
    except (repository.NotFoundError, sqlite3.Error) as exc:
        raise _handle(exc) from exc


@router.put(
    "/{record_id}",
    response_model=RecordRead,
    summary="Замінити запис",
    responses={**NOT_FOUND, **CONFLICT},
)
def replace_record(record_id: RecordId, payload: RecordReplace) -> dict:
    """Повністю замінити змінювані поля запису."""
    try:
        return repository.replace_record(record_id, payload.model_dump())
    except (repository.NotFoundError, repository.ConflictError, sqlite3.Error) as exc:
        raise _handle(exc) from exc


@router.delete(
    "/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити запис",
    responses=NOT_FOUND,
)
def delete_record(record_id: RecordId) -> Response:
    """Видалити запис за id."""
    try:
        repository.delete_record(record_id)
    except (repository.NotFoundError, sqlite3.Error) as exc:
        raise _handle(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)