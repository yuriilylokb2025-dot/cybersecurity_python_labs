import logging
import sqlite3
from typing import Annotated, Literal

from fastapi import APIRouter, Body, HTTPException, Path, Query
from starlette import status

from labs.lab03 import repository
from labs.lab03.schemas import RecordCreate, RecordRead, RecordReplace

router = APIRouter(prefix="/records", tags=["Records"])
logger = logging.getLogger(__name__)

RecordStatus = Literal["new", "in_progress", "done"]


def ensure_category_exists(category_id: int) -> None:
    """Перевірити існування категорії."""
    categories = repository.get_categories()
    if not any(item["id"] == category_id for item in categories):
        raise HTTPException(
            status_code=404,
            detail="Категорію не знайдено",
        )


def handle_integrity_error(error: sqlite3.IntegrityError) -> None:
    """Перетворити порушення обмежень SQLite на HTTP-помилку."""
    message = str(error).lower()

    if "foreign key" in message:
        raise HTTPException(
            status_code=404,
            detail="Категорію не знайдено",
        ) from None

    raise HTTPException(
        status_code=409,
        detail="Дублікат коду або порушення обмежень бази даних",
    ) from None


@router.get(
    "",
    response_model=list[RecordRead],
    summary="Отримати список записів",
)
def list_records(
    category_id: Annotated[int | None, Query(gt=0)] = None,
    status_filter: Annotated[
        RecordStatus | None,
        Query(alias="status"),
    ] = None,
    min_value: Annotated[float | None, Query(ge=0, le=10)] = None,
    q: Annotated[str | None, Query(min_length=1, max_length=120)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[dict]:
    """Отримати записи з фільтрацією та пагінацією."""
    try:
        return repository.get_records(
            category_id=category_id,
            status=status_filter,
            min_value=min_value,
            q=q,
            limit=limit,
            offset=offset,
        )
    except sqlite3.Error:
        logger.exception("Помилка отримання списку записів")
        raise HTTPException(
            status_code=500,
            detail="Помилка роботи з базою даних",
        ) from None


@router.post(
    "/bulk",
    response_model=list[RecordRead],
    status_code=status.HTTP_201_CREATED,
    responses={
        404: {"description": "Категорію не знайдено"},
        409: {"description": "Дублікат коду"},
    },
    summary="Пакетне створення записів",
)
def create_bulk(
    records: Annotated[list[RecordCreate], Body(min_length=1, max_length=100)],
) -> list[dict]:
    """Додати від 1 до 100 записів однією транзакцією."""
    try:
        for record in records:
            ensure_category_exists(record.category_id)

        return repository.create_records_bulk(
            [record.model_dump() for record in records]
        )
    except HTTPException:
        raise
    except sqlite3.IntegrityError as error:
        handle_integrity_error(error)
        raise
    except sqlite3.Error:
        logger.exception("Помилка пакетного створення")
        raise HTTPException(
            status_code=500,
            detail="Помилка роботи з базою даних",
        ) from None


@router.get(
    "/{record_id}",
    response_model=RecordRead,
    responses={404: {"description": "Запис не знайдено"}},
    summary="Отримати запис за id",
)
def read_record(record_id: Annotated[int, Path(gt=0)]) -> dict:
    """Повернути один запис."""
    try:
        record = repository.get_record(record_id)
    except sqlite3.Error:
        logger.exception("Помилка отримання запису")
        raise HTTPException(
            status_code=500,
            detail="Помилка роботи з базою даних",
        ) from None

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Запис не знайдено",
        )

    return record


@router.post(
    "",
    response_model=RecordRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        404: {"description": "Категорію не знайдено"},
        409: {"description": "Дублікат коду"},
    },
    summary="Створити запис",
)
def create_record(data: RecordCreate) -> dict:
    """Додати новий запис."""
    try:
        ensure_category_exists(data.category_id)

        return repository.create_record(**data.model_dump())
    except HTTPException:
        raise
    except sqlite3.IntegrityError as error:
        handle_integrity_error(error)
        raise
    except sqlite3.Error:
        logger.exception("Помилка створення запису")
        raise HTTPException(
            status_code=500,
            detail="Помилка роботи з базою даних",
        ) from None


@router.put(
    "/{record_id}",
    response_model=RecordRead,
    responses={
        404: {"description": "Запис або категорію не знайдено"},
        409: {"description": "Дублікат коду"},
    },
    summary="Повністю оновити запис",
)
def replace_record(
    record_id: Annotated[int, Path(gt=0)],
    data: RecordReplace,
) -> dict:
    """Замінити всі змінювані поля запису."""
    try:
        if repository.get_record(record_id) is None:
            raise HTTPException(
                status_code=404,
                detail="Запис не знайдено",
            )

        ensure_category_exists(data.category_id)

        result = repository.update_record(
            record_id,
            **data.model_dump(),
        )
    except HTTPException:
        raise
    except sqlite3.IntegrityError as error:
        handle_integrity_error(error)
        raise
    except sqlite3.Error:
        logger.exception("Помилка оновлення запису")
        raise HTTPException(
            status_code=500,
            detail="Помилка роботи з базою даних",
        ) from None

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Запис не знайдено",
        )

    return result


@router.delete(
    "/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"description": "Запис не знайдено"}},
    summary="Видалити запис",
)
@router.delete(
    "/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"description": "Запис не знайдено"}},
    summary="Видалити запис",
)
def delete_record(
    record_id: Annotated[int, Path(gt=0)],
) -> None:
    """Видалити запис за id."""
    try:
        deleted = repository.delete_record(record_id)
    except sqlite3.Error:
        logger.exception("Помилка видалення запису")
        raise HTTPException(
            status_code=500,
            detail="Помилка роботи з базою даних",
        ) from None

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Запис не знайдено",
        )
