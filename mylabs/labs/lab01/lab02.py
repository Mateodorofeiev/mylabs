import os
import sys

# 1. Імпорт індивідуальних параметрів студента
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER
print(
    f"Студент: {STUDENT_NAME} | Варіант: {VARIANT_NUMBER} | Група: {GROUP_NAME}\n"
)

# Вхідні дані Варіанта 5 (із зображення)
users = {
    "forensic_lead": {
        "role": "forensic_analyst",
        "clearance": 4,
        "department": "Forensics",
        "active": True,
    },
    "compliance_off": {
        "role": "compliance_officer",
        "clearance": 3,
        "department": "Compliance",
        "active": True,
    },
    "trainee_sec": {
        "role": "trainee",
        "clearance": 1,
        "department": "Training",
        "active": True,
    },
    "vendor_tech": {
        "role": "vendor_support",
        "clearance": 2,
        "department": "Vendor",
        "active": True,
    },
    "archived_usr": {
        "role": "archived",
        "clearance": 1,
        "department": "Archive",
        "active": False,
    },
}

resources = [
    ("forensic_images", 4),
    ("compliance_reports", 3),
    ("training_videos", 1),
    ("vendor_tools", 2),
    ("evidence_locker", 4),
    ("certification_docs", 1),
    ("audit_findings", 3),
    ("chain_of_custody", 4),
    ("support_tickets", 2),
    ("learning_modules", 1),
]

security_levels = ("Basic", "Standard", "Protected", "Maximum")

blocked_users = {"archived_usr", "terminated_vendor", "security_breach"}


# 2. Виведення структурованої таблиці ресурсів
print("=" * 65)
print("СПИСОК РЕСУРСІВ СИСТЕМИ ТА ЇХНІ РІВНІ ДОСТУПУ")
print("=" * 65)
print(f"{'Назва ресурсу':<22} | {'Числовий':<9} | {'Рівень безпеки'}")
print("-" * 65)

for res_name, res_level in resources:
    level_text = security_levels[res_level - 1]
    print(f"{res_name:<22} | {res_level:<9} | {level_text}")


# 3. Алгоритм перевірки доступу
def check_access(username: str, resource: tuple) -> str:
    res_name, res_level = resource

    # Перевірка наявності користувача в базі
    if username not in users:
        return "DENY (User not found)"

    # Перевірка блокування облікового запису
    if username in blocked_users:
        return "DENY (User is blocked)"

    user_info = users[username]

    # Перевірка активності акаунту
    if not user_info.get("active", False):
        return "DENY (Account inactive)"

    # Порівняння рівня допуску користувача з рівнем ресурсу
    if user_info.get("clearance", 0) >= res_level:
        return "ALLOW"
    else:
        return "DENY (Insufficient clearance)"


# 4. Виведення результатів перевірки
print("\n" + "=" * 65)
print("РЕЗУЛЬТАТИ ПЕРЕВІРКИ ДОСТУПУ")
print("=" * 65)


# Формування тестового списку (включно з неіснуючим користувачем 'ghost_user')
test_users_list = list(users.keys()) + ["ghost_user"]

for username in test_users_list:
    print(f"--- Перевірка для користувача: {username} ---")
    for res in resources:
        res_name, _ = res
        result = check_access(username, res)
        print(f"user={username} resource={res_name} -> {result}")
