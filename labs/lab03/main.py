from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from labs.lab03.config import (
    APP_DESCRIPTION,
    APP_TITLE,
    VALUE_THRESHOLD,
    VALUE_UNIT,
)
from labs.lab03.database import initialize_database
from labs.lab03.routers import categories, records
from shared import student


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Ініціалізувати базу під час запуску сервера."""
    initialize_database()
    yield


app = FastAPI(
    title=APP_TITLE,
    description=(
        f"{APP_DESCRIPTION}\n\n"
        f"Одиниця вимірювання: {VALUE_UNIT}. "
        f"Поріг небезпеки: {VALUE_THRESHOLD}."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(categories.router)
app.include_router(records.router)


@app.get("/ping", tags=["System"])
def ping() -> dict:
    """Перевірити доступність API."""
    return {"status": "ok"}


@app.get("/student", tags=["System"])
def get_student() -> dict:
    """Отримати дані студента."""
    return {
        "student_name": student.STUDENT_NAME,
        "group_name": student.GROUP_NAME,
        "variant_number": student.VARIANT_NUMBER,
    }
