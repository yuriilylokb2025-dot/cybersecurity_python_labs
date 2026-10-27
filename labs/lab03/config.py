"""Налаштування лабораторної роботи №3, варіант 3."""

VARIANT_NUMBER = 3

APP_TITLE = "Реєстр вразливостей робочих станцій"

APP_DESCRIPTION = (
    "Web API для обліку навчальних знахідок перевірки "
    "робочих станцій. Категорії визначають тип програмного "
    "забезпечення, а значення value — оцінку небезпеки."
)

VALUE_UNIT = "score"
VALUE_MIN = 0.0
VALUE_MAX = 10.0
VALUE_THRESHOLD = 8.0

CATEGORIES = ("os", "browser", "office")

ALLOWED_STATUSES = ("new", "in_progress", "done")

DEFAULT_LIMIT = 20
MAX_LIMIT = 100
MAX_BULK_RECORDS = 100
