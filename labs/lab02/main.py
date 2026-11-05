from datetime import timedelta
import sys

from task1 import Admin, User, UserAccount


def run_demo() -> None:
    print("=== Демонстрація системи безпеки (Завдання 1) ===\n")

    # Створюємо користувача і задаємо пароль
    user = User("olena_sec", "olena_sec@secmail.org")
    user.set_password("Qwerty#2026")

    account = UserAccount(user)

    print(f"Створено користувача: {user}")

    print("\n--- Тест автентифікації ---")
    # Спочатку невірний пароль, потім правильний
    if account.login("olena_sec", "wrong_pass", "172.16.0.7"):
        print("[+] Вхід успішний!")
    else:
        print("[-] Помилка входу (невірний пароль)!")

    if account.login("olena_sec", "Qwerty#2026", "172.16.0.7"):
        print("[+] Вхід успішний!")
    else:
        print("[-] Помилка входу!")

    print(f"Статус авторизації: {account.is_authenticated()}")

    print("\n--- Зміна email ---")
    user.email = "olena_new@secmail.org"
    print(f"Новий email: {user.email}")
    try:
        user.email = "bad@mail"  # немає крапки в домені
    except ValueError as err:
        print(f"[-] {err}")

    print("\n--- Права адміністратора ---")
    admin = Admin("admin_ivan", "ivan_admin@secmail.org")
    admin.grant_permission("read_logs")
    admin.grant_permission("delete_users")
    admin.revoke_permission("delete_users")
    print(admin)
    print(f"Може читати логи: {admin.has_permission('read_logs')}")

    print("\n--- Таймаут сеансу ---")
    # Не чекаємо 15 хвилин, а зсуваємо час останньої активності на 1000 с назад
    account["session"].last_activity -= timedelta(seconds=1000)
    print(f"Статус після простою: {account.is_authenticated()}")

    print("\n--- Вихід із системи ---")
    account.login("olena_sec", "Qwerty#2026", "172.16.0.7")
    account.logout()
    print(f"Статус після виходу: {account.is_authenticated()}")

    print("\n--- Записи аудиту ---")
    for record in account.audit_log.show_all():
        print(f"[{record.timestamp}] {record.username}: {record.action}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        run_demo()
    else:
        print("Використання: python -m labs.lab02.main demo")
