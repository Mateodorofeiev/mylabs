"""Завдання 1: моделі користувачів, сеансів та аудиту."""

import hashlib
import hmac
import os
import re
from dataclasses import dataclass
from datetime import UTC, datetime

# Глобальні константи безпеки
PBKDF2_ITERATIONS = 100_000  # Кількість ітерацій для посилення хешування пароля
SESSION_TIMEOUT_SEC = 900  # Час життя сеансу без активності (15 хвилин)

# Регулярний вираз для перевірки валідності email (сувора валідація)
EMAIL_PATTERN = r"[a-zA-Z][a-zA-Z0-9_]{2,63}@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"


class User:
    """Базовий клас, що описує обліковий запис звичайного користувача."""

    def __init__(self, username, email, role="user", active=True):
        self.username = username
        self.email = (  # Викличе сеттер нижче для первинної валідації пошти
            email
        )
        self.role = role
        self.active = active

        # Приватні атрибути (name mangling: __) для захисту хешу та солі від прямого доступу
        self.__password_hash = None
        self.__password_salt = None

    @property
    def email(self):
        """Геттер: безпечно повертає поточну електронну пошту."""
        return self._email

    @email.setter
    def email(self, value):
        """Сеттер: перевіряє пошту за шаблоном перед тим, як зберегти."""
        # fullmatch гарантує, що весь рядок відповідає патерну, а не лише його частина
        if not isinstance(value, str) or not re.fullmatch(EMAIL_PATTERN, value):
            raise ValueError(f"Некоректний формат email: '{value}'")
        self._email = value

    def set_password(self, password):
        """Безпечне встановлення пароля за допомогою PBKDF2 та унікальної солі."""
        if not password:
            raise ValueError("Пароль не може бути порожнім.")

        # Генеруємо криптографічно стійку випадкову сіль (16 байт) для захисту від rainbow tables
        self.__password_salt = os.urandom(16)

        # Хешуємо пароль алгоритмом SHA-256 із сіллю та ітераціями
        self.__password_hash = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), self.__password_salt, PBKDF2_ITERATIONS
        )

    def check_password(self, password):
        """Перевірка введеного пароля (автентифікація)."""
        if self.__password_hash is None:
            return False  # Якщо пароль взагалі не був заданий

        # Повторно хешуємо введений пароль із тією ж сіллю, яка збережена для користувача
        calculated_hash = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), self.__password_salt, PBKDF2_ITERATIONS
        )

        # hmac.compare_digest захищає від timing attacks (атак за часом виконання порівняння)
        return hmac.compare_digest(self.__password_hash, calculated_hash)

    def deactivate(self):
        """М'яке блокування (деактивація) користувача."""
        self.active = False

    def __str__(self):
        """Зручне строкове представлення об'єкта для виведення в консоль."""
        return (
            f"User(username='{self.username}', email='{self.email}', "
            f"role='{self.role}', active={self.active})"
        )


class Admin(User):
    """Клас адміністратора, успадкований від User (принцип наслідування в ООП)."""

    def __init__(self, username, email, permissions=None, active=True):
        # Викликаємо конструктор батьківського класу, автоматично задаючи роль "admin"
        super().__init__(username, email, role="admin", active=active)

        # Захист від спільного мутабельного аргументу за замовчуванням (permissions=None)
        self.permissions = set(permissions) if permissions else set()

    def grant_permission(self, permission):
        """Додавання нового права адміністратору."""
        self.permissions.add(permission)

    def revoke_permission(self, permission):
        """Вилучення права (discard не викликає помилку, якщо такого права немає)."""
        self.permissions.discard(permission)

    def has_permission(self, permission):
        """Перевірка наявності конкретного права у цього адміна."""
        return permission in self.permissions

    def __str__(self):
        """Красивий вивід інформації про адміна разом із його відсортованими правами."""
        perms = ", ".join(sorted(self.permissions)) if self.permissions else "None"
        return (
            f"Admin(username='{self.username}', email='{self.email}', "
            f"active={self.active}, permissions=[{perms}])"
        )


class Session:
    """Клас для керування активним сеансом роботи користувача."""

    def __init__(self, ip):
        self.ip = ip
        # Фіксуємо час у форматі UTC, щоб уникнути конфліктів часових поясів
        self.login_time = datetime.now(UTC)
        self.last_activity = datetime.now(UTC)

    def touch(self):
        """Оновлює час останньої активності користувача (продовжує сесію)."""
        self.last_activity = datetime.now(UTC)

    def is_active(self, timeout_sec):
        """Перевіряє, чи не закінчився час сеансу через неактивність."""
        if timeout_sec <= 0:
            raise ValueError("timeout_sec повинен бути додатним числом.")
        now = datetime.now(UTC)
        # Різниця datetime у Python це timedelta; переводимо її у секунди
        return (now - self.last_activity).total_seconds() < timeout_sec


@dataclass  # Автоматично створює конструктор __init__, __repr__ та __eq__
class AuditRecord:
    """Структура даних для зберігання одного запису в системному журналі."""

    timestamp: datetime
    username: str
    action: str  # Наприклад: login_success / login_failure / logout


class AuditLog:
    """Клас для збереження та управління історією подій (аудиту безпеки)."""

    def __init__(self):
        self.records = []  # Список для зберігання об'єктів AuditRecord

    def add_log(self, username, action):
        """Створює новий запис аудиту з поточним UTC-часом і додає до списку."""
        record = AuditRecord(
            timestamp=datetime.now(UTC), username=username, action=action
        )
        self.records.append(record)

    def show_all(self):
        """Повертає всю історію подій."""
        return self.records


class UserAccount:
    """Диспетчер облікового запису (композиція: об'єднує User, Session, AuditLog)."""

    def __init__(self, user, audit_log=None):
        self.user = user
        # Якщо лог не передали ззовні, створюємо новий ізольований екземпляр
        self.audit_log = audit_log if audit_log is not None else AuditLog()
        self.session = None

    def login(self, username, password, ip):
        """Спроба входу в систему з перевіркою всіх умов безпеки."""
        if (
            self.user.username == username
            and self.user.active
            and self.user.check_password(password)
        ):
            # Успішний вхід: створюємо нову сесію, фіксуємо час та пишемо лог
            self.session = Session(ip)
            self.session.touch()
            self.audit_log.add_log(username, "login_success")
            return True

        # Невдалий вхід: фіксуємо помилку в аудит
        self.audit_log.add_log(username, "login_failure")
        return False

    def is_authenticated(self):
        """Перевіряє, чи користувач наразі автентифікований (сесія жива)."""
        if self.session is None:
            return False
        # Перевіряємо таймаут (не оновлюючи час сесії всередині перевірки)
        return self.session.is_active(SESSION_TIMEOUT_SEC)

    def logout(self):
        """Завершення сеансу користувача (вихід із системи)."""
        if self.session:
            self.audit_log.add_log(self.user.username, "logout")
            self.session = None  # Знищуємо сесію

    def __getitem__(self, key):
        """Магічний метод: дозволяє звертатися до полів акаунта через квадратні дужки (як до словника)."""
        allowed = {
            "user": self.user,
            "session": self.session,
            "audit_log": self.audit_log,
            "username": self.user.username,
            "email": self.user.email,
            "role": self.user.role,
            "active": self.user.active,
        }
        if key in allowed:
            return allowed[key]
        raise KeyError(f"Ключ '{key}' недоступний.")

    def __setitem__(self, key, value):
        """Магічний метод: безпечне оновлення параметрів через квадратні дужки з перевіркою типів."""
        if key == "user":
            if not isinstance(value, User):
                raise TypeError("Значення для 'user' має бути об'єктом User.")
            self.user = value
        elif key == "email":
            if not isinstance(value, str):
                raise TypeError("Email повинен бути рядком.")
            self.user.email = (  # Викличе сеттер класу User із перевіркою регулярним виразом
                value
            )
        elif key == "session":
            if value is not None and not isinstance(value, Session):
                raise TypeError("Значення для 'session' має бути Session або None.")
            self.session = value
        else:
            raise KeyError(f"Зміна '{key}' через [] заборонена.")
