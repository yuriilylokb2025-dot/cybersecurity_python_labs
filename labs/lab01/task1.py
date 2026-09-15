import random

from shared.student import STUDENT_NAME, VARIANT_NUMBER

passwords = [
    "UserPass1!",
    "temp",
    "Cyber$ecur1ty",
    "guest",
    "P0w3rful@Pass",
    "login",
    "Defens3#2023",
    "abc123",
    "Elit3@Secur",
    "demo"
]

criteria = {
    "min_length": 9,
    "require_digits": True,
    "require_upper": True,
    "require_special": True,
}

forbidden_passwords = {
    "temp",
    "guest",
    "login",
    "demo",
    "abc123",
    "user"
}

random_indexes = random.sample(range(len(passwords)),3)


for index in random_indexes:
    passwords.append(passwords[index])

def check_password(password):
    min_length = criteria["min_length"]

    has_digit = any(symbol.isdigit() for symbol in password)
    has_upper = any(symbol.isupper() for symbol in password)
    has_lower = any(symbol.islower() for symbol in password)
    has_special = any(not symbol.isalnum() for symbol in password)

    if password.lower() in forbidden_passwords or len(password) < min_length:
        return "Заборонений"

    all_requirements = has_digit and has_upper and has_special

    if all_requirements:
        if len(password) >= min_length + 4 and passwords.count(password) == 1:
            return ("Дуже сильний")

        return "Сильний"


    completed_groups = sum([
        has_digit,
        has_upper,
        has_lower,
        has_special
    ])
    if completed_groups <= 1:
        return "Слабкий"

    return "Середній"

print(f"Студент: {STUDENT_NAME}")
print(f"Варіант: {VARIANT_NUMBER}")

print("-" * 48)
print(f"{'№':<4}{'Пароль':<22}{'Рівень надійності'}")
print("-" * 48)

for number, password in enumerate(passwords, start=1):
    reliability = check_password(password)
    print(f"{number:<4}{password:<22}{reliability}")
print("-" * 48)

