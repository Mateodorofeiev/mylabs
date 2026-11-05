"""Pydantic-моделі запитів і відповідей (варіант 5)."""

from pydantic import BaseModel, ConfigDict, Field, StrictInt

from .config import (
    CATEGORY_NAME_MAX,
    CATEGORY_NAME_MIN,
    CODE_MAX,
    CODE_MIN,
    TITLE_MAX,
    TITLE_MIN,
    VALUE_MAX,
    VALUE_MIN,
    Status,
)


class CategoryCreate(BaseModel):
    """Тіло запиту для створення категорії."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(min_length=CATEGORY_NAME_MIN, max_length=CATEGORY_NAME_MAX)


class CategoryRead(CategoryCreate):
    """Категорія у відповіді."""

    id: int


class RecordCreate(BaseModel):
    """Тіло запиту для створення запису."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    code: str = Field(min_length=CODE_MIN, max_length=CODE_MAX)
    title: str = Field(min_length=TITLE_MIN, max_length=TITLE_MAX)
    category_id: StrictInt = Field(gt=0)
    value: StrictInt = Field(ge=VALUE_MIN, le=VALUE_MAX)
    status: Status


class RecordReplace(RecordCreate):
    """Тіло запиту для PUT: усі змінювані поля обов'язкові."""


class RecordRead(RecordCreate):
    """Запис у відповіді."""

    id: int
    category_name: str