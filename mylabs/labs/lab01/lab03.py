import csv
import hashlib
import json
import os
import sys
from datetime import datetime

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER

print(
    f"Студент: {STUDENT_NAME} | Варіант: {VARIANT_NUMBER} | Група: {GROUP_NAME}\n"
)

# Параметри Варіанта 5 (згідно з таблицею)
min_len = 16
salt = f"{VARIANT_NUMBER:05d}"  # Сіль "00005"

# Корректний шлях: папка data створюється в цій же директорії, де лежить скрипт
Data_directory = os.path.join(os.path.dirname(__file__), "data")
CSV_Path = os.path.join(Data_directory, "users.csv")
JSON_Path = os.path.join(Data_directory, "log.json")

# База користувачів у пам'яті
users_db = []


# Власний виняток згідно з вимогою пункту 1
class ValidationError(Exception):
    pass


def generate_hash(password: str, salt: str = "00000") -> str:
    """Генерує sha3_256 хеш від пароля із сіллю з попередньою валідацією."""
    if not password or not salt:
        raise ValueError("Password and salt must not be None or empty")
    if len(password) < min_len:
        raise ValidationError(
            f"Пароль має містити щонайменше {min_len} символів"
        )

    combined = (password + salt).encode("utf-8")
    # Правильний алгоритм згідно з Варіантом 5
    return hashlib.sha3_256(combined).hexdigest()


def log_event(func):
    """Декоратор для запису спроб входу у файл log.json."""

    def wrapper(*args, **kwargs):
        username = kwargs.get("username")
        if not username and len(args) > 0:
            username = args[0]

        result = "failure"
        try:
            res = func(*args, **kwargs)
            if res:
                result = "success"
            return res
        except Exception:
            result = "failure"
            raise
        finally:
            os.makedirs(Data_directory, exist_ok=True)
            log_data = {
                "event": "login",
                "user": str(username) if username else "",
                "result": result,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "args": list(args),
                "kwargs": kwargs,
            }
            logs = []
            if os.path.exists(JSON_Path):
                try:
                    with open(JSON_Path, "r", encoding="utf-8") as f:
                        logs = json.load(f)
                except Exception:
                    logs = []

            logs.append(log_data)
            with open(JSON_Path, "w", encoding="utf-8") as f:
                json.dump(logs, f, indent=4, ensure_ascii=False)

    return wrapper


def create_user(username, password):
    """Створює запис користувача з гешованим паролем."""
    return (username, generate_hash(password, salt=salt))


def create_users(users_list):
    """Створює CSV-файл users.csv та записує список облікових записів."""
    os.makedirs(Data_directory, exist_ok=True)
    with open(CSV_Path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for user, pwd in users_list:
            writer.writerow(create_user(user, pwd))


def read_users():
    """Зчитує облікові дані з CSV у users_db та виводить їх у вигляді таблиці."""
    global users_db
    users_db = []
    with open(CSV_Path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if row:
                users_db.append((row[0], row[1]))

    print(f"\n{'Користувач':<15} | {'Хеш (sha3_256)':<64}")
    print("-" * 82)
    for u, h in users_db:
        print(f"{u:<15} | {h:<64}")
    print("-" * 82 + "\n")


@log_event
def login(username: str, password: str) -> bool:
    """Автентифікує користувача шляхом порівняння обчисленого хешу з базою."""
    if not username or not password:
        raise ValueError("Логін і пароль обов'язкові")

    user_hash = generate_hash(password, salt=salt)

    for db_user, db_hash in users_db:
        if db_user == username and db_hash == user_hash:
            return True
    return False


def main():
    # 10 облікових записів з паролями довжиною >= 16 символів
    users_to_register = (
        ("developer_alex", "DevCode#202621345"),
        ("dmytro_admin", "MasterKey9872131!"),
        ("roman_sec", "CyberGuard#443123"),
        ("audit_expert", "AuditorSafe$13131"),
        ("lead_designer", "CreativeUI8812313!"),
        ("qa_engineer", "TestRunner#091231"),
        ("net_sysadmin", "RouterCore$261234"),
        ("data_analyst", "DataVault771341!"),
        ("cloud_support", "AWSCloud#50012345"),
        ("service_bot", "AutoBotKey#121234"),
    )

    try:
        create_users(users_to_register)
        read_users()

        # Тестування автентифікації з відповідними правильними паролями
        print(
            "[+] Спроба 1 (успіх):",
            login("developer_alex", "DevCode#202621345"),
        )
        print(
            "[-] Спроба 2 (невірний пароль):",
            login("dmytro_admin", "CyberGuard#443123"),
        )
        print(
            "[-] Спроба 3 (невідомий юзер):",
            login("unknown", "DataVault771341!"),
        )

    except (FileNotFoundError, PermissionError, IOError) as e:
        print(f"Помилка файлової системи: {e}")
    except (ValueError, ValidationError) as e:
        print(f"Помилка валідації даних: {e}")


if __name__ == "__main__":
    main()