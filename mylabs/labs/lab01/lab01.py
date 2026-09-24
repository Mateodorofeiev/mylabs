import os
import random
import sys

# Підключення спільного модуля даних
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER
print(
    f"Студент: {STUDENT_NAME} | Варіант: {VARIANT_NUMBER}\n| Група: {GROUP_NAME}\n"
)

# Початковий список паролів для перевірки
passwords = [
    "DataS3cur3!",
    "123",
    "Crypt0@Analysis",
    "test123",
    "Quantum#2023",
    "access",
    "Secur1ty@Pro",
    "password1",
    "Adv@nced123",
    "guest123",
]

# Критерії складності пароля
criteria = {
    "min_length": 12,
    "require_digits": True,
    "require_upper": True,
    "require_special": True,
}

# Множина заборонених паролів
forbidden_passwords = {
    "123",
    "test123",
    "access",
    "password1",
    "guest123",
    "admin",
}

#  Генерація 3 випадкових індексів та додавання дублікатів
initial_len = len(passwords)
for i in range(3):
    rand_idx = random.randint(0, initial_len - 1)
    passwords.append(passwords[rand_idx])

min_length = criteria["min_length"]
result = []

#  Перевірка паролів у циклі
for a in passwords:
    has_digit = any(c.isdigit() for c in a)
    has_upper = any(c.isupper() for c in a)
    has_lower = any(c.islower() for c in a)
    has_special = any(not c.isalnum() and not c.isspace() for c in a)

    # Перевірка виконання базових вимог безпеки
    safe_criteria = (
        len(a) >= min_length
        and (not criteria["require_digits"] or has_digit)
        and (not criteria["require_upper"] or has_upper)
        and (not criteria["require_special"] or has_special)
    )
    # Класифікація рівня надійності пароля
    if a in forbidden_passwords or len(a)< min_length:
        strenght= "Заборонений!"
    elif safe_criteria and len(a)>= min_length +4 and passwords.count(a) ==1:
        strenght= "потужний пароль"
    elif safe_criteria:
        strenght ="сильний пароль"
    elif len(a)>= min_length and (has_digit or has_upper or has_lower or has_special ):
        strenght = "Задовільнено"
    else:
        strenght ="слабий пароль"

    is_unique = "Так" if passwords.count(a) == 1 else "Ні"
    result.append((a, len(a), is_unique, strenght))

# Форматоване виведення результатів оцінки

print(
    f"{'№':<3} | {'Пароль':<18} | {'Довжина':<8} | {'Унікальний':<10} | {'Категорія':<15}"
)
print("-" * 65)

for idx, (pwd, length, is_unique, strength) in enumerate(result, start=1):
    print(
        f"{idx:<3} | {pwd:<18} | {length:<8} | {is_unique:<10} | {strength:<15}"
    )

print("=" * 65)


