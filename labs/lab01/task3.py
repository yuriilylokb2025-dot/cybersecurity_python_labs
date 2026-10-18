import csv
import hashlib
import json
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path

from shared.student import VARIANT_NUMBER

MIN_PASSWORD_LENGTH = 8

PERSONAL_SALT = str(VARIANT_NUMBER).zfill(5)

DATA_FOLDER = Path(__file__).parent / "data"
USERS_FILE = DATA_FOLDER / "users.csv"
LOG_FILE = DATA_FOLDER / "log.json"


class ValidationError(Exception):
    pass


def generate_hash(password: str, salt: str = "00000") -> str:
    if password is None or password == "":
        raise ValueError("Пароль не може бути порожнім")

    if salt is None or salt == "":
        raise ValueError("Сіль не може бути порожньою")

    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(
            f"Пароль повинен містити мінімум {MIN_PASSWORD_LENGTH} символів"
        )

    text = password + salt

    return hashlib.sha1(text.encode("utf-8")).hexdigest()


users_to_register = (
    ("admin", "Admin123!"),
    ("yura", "Yura2026!"),
    ("student", "Study123"),
    ("user1", "Password1!"),
    ("olena", "Olena456#"),
    ("taras", "Taras789$"),
    ("andrii", "Andrii321!"),
    ("maria", "Maria2026@"),
    ("guest", "Guest1234"),
    ("tester", "Test5678#"),
)


def create_user(username, password):
    if username is None or username == "":
        raise ValueError("Логін не може бути порожнім")

    password_hash = generate_hash(password, PERSONAL_SALT)

    return username, password_hash


def create_users(users_list):
    try:
        DATA_FOLDER.mkdir(parents=True, exist_ok=True)

        with USERS_FILE.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)

            for username, password in users_list:
                user = create_user(username, password)
                writer.writerow(user)

    except PermissionError:
        print("Помилка: немає дозволу на запис у users.csv")
        raise

    except OSError as error:
        print(f"Помилка запису users.csv: {error}")
        raise


def read_users():
    users = []

    try:
        with USERS_FILE.open("r", newline="", encoding="utf-8") as file:
            reader = csv.reader(file)

            for row in reader:
                if len(row) == 2:
                    users.append((row[0], row[1]))

    except FileNotFoundError:
        print("Помилка: файл users.csv не знайдено")
        raise

    except PermissionError:
        print("Помилка: немає дозволу на читання users.csv")
        raise

    except OSError as error:
        print(f"Помилка читання users.csv: {error}")
        raise

    return users


def print_users(users):
    print("\nБаза користувачів:")
    print("-" * 60)
    print(f"{'Логін':<12} | Хеш пароля")
    print("-" * 60)

    for username, password_hash in users:
        print(f"{username:<12} | {password_hash}")

    print("-" * 60)


def save_log(event):
    try:
        DATA_FOLDER.mkdir(parents=True, exist_ok=True)

        try:
            with LOG_FILE.open("r", encoding="utf-8") as file:
                events = json.load(file)

        except (FileNotFoundError, json.JSONDecodeError):
            events = []

        events.append(event)

        with LOG_FILE.open("w", encoding="utf-8") as file:
            json.dump(events, file, ensure_ascii=False, indent=4)

    except PermissionError:
        print("Помилка: немає дозволу на роботу з log.json")
        raise

    except OSError as error:
        print(f"Помилка роботи з log.json: {error}")
        raise


def log_event(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if len(args) > 0:
            username = args[0]
        else:
            username = kwargs.get("username", "")

        try:
            result = function(*args, **kwargs)

            if result:
                login_result = "success"
            else:
                login_result = "failure"

            event = {
                "event": "login",
                "user": username,
                "result": login_result,
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                "args": [],
                "kwargs": {},
            }

            save_log(event)

            return result

        except (ValidationError, ValueError):
            event = {
                "event": "login",
                "user": username,
                "result": "failure",
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                "args": [],
                "kwargs": {},
            }

            save_log(event)

            raise

    return wrapper


users_db = []


@log_event
def login(username: str, password: str) -> bool:
    if username is None or username == "":
        raise ValueError("Логін не може бути порожнім")

    if password is None or password == "":
        raise ValueError("Пароль не може бути порожнім")

    password_hash = generate_hash(password, PERSONAL_SALT)

    for saved_username, saved_hash in users_db:
        if username == saved_username and password_hash == saved_hash:
            return True

    return False


def main():
    global users_db

    try:
        create_users(users_to_register)
        users_db = read_users()

    except (OSError, FileNotFoundError, PermissionError):
        return

    print_users(users_db)

    login_attempts = (
        ("yura", "Yura2026!"),
        ("admin", "WrongPass1!"),
        ("unknown", "Unknown123!"),
    )

    print("\nРезультати входу:")

    for username, password in login_attempts:
        try:
            if login(username, password):
                print(f"{username}: вхід успішний")
            else:
                print(f"{username}: неправильний логін або пароль")

        except ValueError as error:
            print(f"{username}: {error}")

        except ValidationError as error:
            print(f"{username}: {error}")


if __name__ == "__main__":
    main()
