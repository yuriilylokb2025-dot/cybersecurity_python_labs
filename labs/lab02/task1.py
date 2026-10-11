import hashlib
import hmac
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

PBKDF2_ITERATIONS = 100_000


class User:
    def __init__(
        self,
        username: str,
        email: str,
        role: str,
        active: bool = True,
    ):
        self.username = username
        self.email = email
        self.role = role
        self.active = active

        self.__password_hash = None
        self.__password_salt = None

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        pattern = r"^[A-Za-z][A-Za-z0-9_]{2,63}@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"

        if not re.fullmatch(pattern, value):
            raise ValueError("Неправильний формат email")

        self._email = value

    def set_password(self, password: str) -> None:
        self.__password_salt = os.urandom(16)

        self.__password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            self.__password_salt,
            PBKDF2_ITERATIONS,
        )

    def check_password(self, password: str) -> bool:
        if self.__password_hash is None or self.__password_salt is None:
            return False

        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            self.__password_salt,
            PBKDF2_ITERATIONS,
        )

        return hmac.compare_digest(
            self.__password_hash,
            password_hash,
        )

    def deactivate(self) -> None:
        self.active = False

    def __str__(self) -> str:
        return (
            f"User(username={self.username}, "
            f"email={self.email}, "
            f"role={self.role}, "
            f"active={self.active})"
        )


class Admin(User):
    def __init__(
        self,
        username: str,
        email: str,
        role: str = "admin",
        active: bool = True,
        permissions=None,
    ):
        super().__init__(username, email, role, active)

        if permissions is None:
            permissions = set()

        self.permissions = set(permissions)

    def grant_permission(self, permission: str) -> None:
        self.permissions.add(permission)

    def revoke_permission(self, permission: str) -> None:
        self.permissions.discard(permission)

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions

    def __str__(self) -> str:
        return (
            f"Admin(username={self.username}, "
            f"email={self.email}, "
            f"role={self.role}, "
            f"active={self.active}, "
            f"permissions={sorted(self.permissions)})"
        )


class Session:
    def __init__(self, ip: str):
        self.ip = ip
        self.login_time = datetime.now(timezone.utc)
        self.last_activity = self.login_time

    def touch(self) -> None:
        self.last_activity = datetime.now(timezone.utc)

    def is_active(self, timeout_sec: int) -> bool:
        if timeout_sec <= 0:
            raise ValueError("timeout_sec має бути більше 0")

        current_time = datetime.now(timezone.utc)
        timeout = timedelta(seconds=timeout_sec)

        return current_time - self.last_activity <= timeout


@dataclass
class AuditRecord:
    timestamp: datetime
    username: str
    action: str


class AuditLog:
    def __init__(self):
        self.records = []

    def add_log(self, username: str, action: str) -> None:
        record = AuditRecord(
            timestamp=datetime.now(timezone.utc),
            username=username,
            action=action,
        )
        self.records.append(record)

    def show_all(self) -> None:
        for record in self.records:
            print(f"{record.timestamp} | {record.username} | {record.action}")


SESSION_TIMEOUT_SEC = 900


class UserAccount:
    def __init__(
        self,
        user: User,
        audit_log: AuditLog | None = None,
    ):
        self.user = user
        self.session = None
        self.audit_log = audit_log if audit_log is not None else AuditLog()

    def login(self, username: str, password: str, ip: str) -> bool:
        if not self.user.active:
            self.audit_log.add_log(self.user.username, "login_failure")
            return False

        if username != self.user.username:
            self.audit_log.add_log(username, "login_failure")
            return False

        if not self.user.check_password(password):
            self.audit_log.add_log(username, "login_failure")
            return False

        self.session = Session(ip)
        self.session.touch()

        self.audit_log.add_log(username, "login_success")
        return True

    def is_authenticated(self) -> bool:
        if self.session is None:
            return False

        return self.session.is_active(SESSION_TIMEOUT_SEC)

    def logout(self) -> None:
        if self.session is not None:
            self.session = None
            self.audit_log.add_log(self.user.username, "logout")

    def __getitem__(self, key: str):
        if key == "user":
            return self.user

        if key == "session":
            return self.session

        if key == "audit_log":
            return self.audit_log

        raise KeyError(f"Невідомий ключ: {key}")

    def __setitem__(self, key: str, value) -> None:
        if key == "user":
            if not isinstance(value, User):
                raise TypeError("user має бути об'єктом User")

            self.user = value
            return

        if key == "session":
            if value is not None and not isinstance(value, Session):
                raise TypeError("session має бути об'єктом Session або None")

            self.session = value
            return

        if key == "audit_log":
            if not isinstance(value, AuditLog):
                raise TypeError("audit_log має бути об'єктом AuditLog")

            self.audit_log = value
            return

        raise KeyError(f"Невідомий ключ: {key}")
