"""Маршрути категорій."""

import logging
import sqlite3
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Response, status

from .. import repository
from ..schemas import CategoryCreate, CategoryRead

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/categories", tags=["categories"])

DB_ERROR = "Тимчасова помилка бази даних"


@router.get("", response_model=list[CategoryRead], summary="Список категорій")
def list_categories() -> list[dict]:
    """Повернути всі категорії за зростанням id."""
    try:
        return repository.list_categories()
    except sqlite3.OperationalError as exc:
        logger.exception("Помилка читання категорій")
        raise HTTPException(status_code=500, detail=DB_ERROR) from exc


@router.post(
    "",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Створити категорію",
    responses={409: {"description": "Категорія з такою назвою вже існує"}},
)
def create_category(payload: CategoryCreate) -> dict:
    """Створити нову категорію."""
    try:
        return repository.create_category(payload.name)
    except repository.ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except sqlite3.OperationalError as exc:
        logger.exception("Помилка створення категорії")
        raise HTTPException(status_code=500, detail=DB_ERROR) from exc


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити порожню категорію",
    responses={
        404: {"description": "Категорію не знайдено"},
        409: {"description": "Категорія містить записи"},
    },
)
def delete_category(
    category_id: Annotated[int, Path(gt=0, description="Ідентифікатор категорії")],
) -> Response:
    """Видалити категорію, якщо в ній немає записів."""
    try:
        repository.delete_category(category_id)
    except repository.NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except repository.ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except sqlite3.OperationalError as exc:
        logger.exception("Помилка видалення категорії")
        raise HTTPException(status_code=500, detail=DB_ERROR) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)