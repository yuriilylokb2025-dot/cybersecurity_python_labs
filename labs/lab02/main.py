import argparse
from datetime import timedelta

from labs.lab02.task1 import Admin, UserAccount
from labs.lab02.task2 import analyze_rules


def run_demo() -> None:
    admin = Admin(
        username="admin1",
        email="admin123@gmail.com",
    )

    admin.set_password("StrongPassword123!")

    admin.grant_permission("read_logs")
    admin.grant_permission("manage_users")

    account = UserAccount(admin)

    print("=== Користувач ===")
    print(admin)

    print("\n=== Успішний вхід ===")
    result = account.login(
        "admin1",
        "StrongPassword123!",
        "192.168.1.10",
    )
    print("Login result:", result)
    print("Authenticated:", account.is_authenticated())

    print("\n=== Невдалий вхід ===")
    account.logout()

    result = account.login(
        "admin1",
        "wrong_password",
        "192.168.1.10",
    )
    print("Login result:", result)

    print("\n=== Перевірка email ===")
    try:
        admin.email = "new_admin@gmail.com"
        print("Новий email:", admin.email)

        admin.email = "12@gmail.com"
    except ValueError as error:
        print("Помилка email:", error)

    print("\n=== Права адміністратора ===")
    print("read_logs:", admin.has_permission("read_logs"))
    print("manage_users:", admin.has_permission("manage_users"))

    admin.revoke_permission("read_logs")
    print("read_logs після видалення:", admin.has_permission("read_logs"))

    print("\n=== Перевірка таймауту ===")
    account.login(
        "admin1",
        "StrongPassword123!",
        "192.168.1.10",
    )

    account.session.last_activity -= timedelta(seconds=901)

    print("Authenticated після таймауту:", account.is_authenticated())

    print("\n=== Logout ===")
    account.logout()
    print("Authenticated:", account.is_authenticated())

    print("\n=== Audit Log ===")
    account.audit_log.show_all()


def main() -> None:
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    subparsers.add_parser("demo")

    analyze_parser = subparsers.add_parser("analyze")

    analyze_parser.add_argument(
        "--rules-file",
        required=True,
    )

    analyze_parser.add_argument(
        "--output",
        required=True,
    )

    analyze_parser.add_argument(
        "--check-conflicts",
        action="store_true",
    )

    analyze_parser.add_argument(
        "--log-level",
        default="INFO",
    )

    args = parser.parse_args()

    if args.command == "demo":
        run_demo()

    elif args.command == "analyze":
        analyze_rules(
            rules_file=args.rules_file,
            output=args.output,
            check_conflicts=args.check_conflicts,
            log_level=args.log_level,
        )


if __name__ == "__main__":
    main()
