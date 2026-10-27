import logging
import sqlite3

from fastapi import APIRouter, HTTPException, Path, Response, status

from labs.lab03 import repository
from labs.lab03.schemas import CategoryCreate, CategoryRead

router = APIRouter(prefix="/categories", tags=["Categories"])

logger = logging.getLogger(__name__)


@router.get(
    "",
    response_model=list[CategoryRead],
    summary="Отримати список категорій",
)
def list_categories() -> list[dict]:
    """Повернути категорії за зростанням id."""
    try:
        return repository.get_categories()
    except sqlite3.Error:
        logger.exception("Помилка отримання категорій")
        raise HTTPException(
            status_code=500,
            detail="Помилка роботи з базою даних",
        ) from None


@router.post(
    "",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"description": "Категорія вже існує"}},
    summary="Створити категорію",
)
def create_category(data: CategoryCreate) -> dict:
    """Створити нову категорію."""
    try:
        return repository.create_category(data.name)
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Категорія з такою назвою вже існує або дані некоректні",
        ) from None
    except sqlite3.Error:
        logger.exception("Помилка створення категорії")
        raise HTTPException(
            status_code=500,
            detail="Помилка роботи з базою даних",
        ) from None


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"description": "Категорію не знайдено"},
        409: {"description": "Категорія містить записи"},
    },
    summary="Видалити порожню категорію",
)
def delete_category(
    category_id: int = Path(gt=0),
) -> Response:
    """Видалити категорію, якщо вона не містить записів."""
    try:
        deleted = repository.delete_category(category_id)
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Неможливо видалити категорію, яка містить записи",
        ) from None
    except sqlite3.Error:
        logger.exception("Помилка видалення категорії")
        raise HTTPException(
            status_code=500,
            detail="Помилка роботи з базою даних",
        ) from None

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Категорію не знайдено",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
