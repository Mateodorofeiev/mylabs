import argparse
import csv
import json
import logging
import re
import socket
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

# Налаштування логера для відстеження подій у програмі
logger = logging.getLogger(__name__)

# Словник стандартних мережевих портів та їхніх сервісів
SERVICES = {22: "SSH", 53: "DNS", 80: "HTTP", 443: "HTTPS", 3389: "RDP"}

# Регулярні вирази для перевірки валідності IP-адрес та доменів
OCTET = r"(25[0-5]|2[0-4]\d|1?\d?\d)"
IP_RE = re.compile(rf"^{OCTET}(\.{OCTET}){{3}}$")
DOMAIN_RE = re.compile(r"^([a-z0-9]([a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,}$", re.I)


@dataclass
class ScanResult:
    """Клас даних (dataclass) для зручного зберігання результату перевірки одного вузла."""

    host: str  # Хост (IP або домен)
    port: int  # Порт сервісу
    service: str  # Назва сервісу (наприклад, SSH, HTTP)
    status: str  # Статус: ONLINE, OFFLINE або INVALID
    response_time: float | None  # Час відгуку в мілісекундах (або None)
    notes: str  # Додаткові примітки (наприклад, "OK", "Timeout")


def is_valid_host(host: str) -> bool:
    """Перевіряє, чи є введений рядок коректною IP-адресою, доменом або 'localhost'."""
    return bool(
        IP_RE.match(host) or DOMAIN_RE.match(host) or host == "localhost"
    )


def load_targets(path: Path) -> list[dict]:
    """Зчитує список цілей (IP та порти) із заданого JSON-файлу."""
    if not path.exists():
        raise ValueError(f"Файл '{path}' не знайдено.")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Некоректний JSON у '{path}': {e}") from e


def check_target(host: str, port: int, timeout: float) -> ScanResult:
    """Перевіряє конкретний вузол: валідує параметри та намагається встановити TCP-з'єднання."""
    # Визначаємо назву сервісу за порт-номером (якщо немає в словнику — "Unknown")
    service = SERVICES.get(port, "Unknown")

    # Перевірка валідності хоста
    if not is_valid_host(host):
        return ScanResult(host, port, service, "INVALID", None, "Invalid host")
    # Перевірка валідності діапазону портів TCP (від 1 до 65535)
    if not isinstance(port, int) or not 1 <= port <= 65535:
        return ScanResult(host, port, service, "INVALID", None, "Invalid port")

    # Фіксуємо час перед початком підключення для вимірювання пінгу (Response Time)
    start = time.perf_counter()
    try:
        # Спроба відкрити сокет-з'єднання з заданим таймаутом
        with socket.create_connection((host, port), timeout=timeout):
            elapsed = (time.perf_counter() - start) * 1000  # Переводимо в мілісекунди
            return ScanResult(host, port, service, "ONLINE", elapsed, "OK")
    except socket.timeout:
        # Сервер не відповів вчасно
        return ScanResult(host, port, service, "OFFLINE", None, "Timeout")
    except socket.gaierror:
        # Помилка резолву доменного імені (DNS error)
        return ScanResult(host, port, service, "OFFLINE", None, "DNS error")
    except OSError as e:
        # Будь-яка інша мережева помилка (наприклад, відмова в підключенні)
        return ScanResult(host, port, service, "OFFLINE", None, e.strerror or "Error")


def print_table(results: list[ScanResult]) -> None:
    """Виводить гарно відформатовану таблицю з результатами сканування в консоль."""
    print(f"{'Target Host':<26}{'Port':<7}{'Service':<9}{'Status':<9}{'Response':<12}Notes")
    print("-" * 75)
    for r in results:
        rt = f"{r.response_time:.1f} ms" if r.response_time is not None else "-"
        print(f"{r.host:<26}{r.port!s:<7}{r.service:<9}{r.status:<9}{rt:<12}{r.notes}")


def print_stats(results: list[ScanResult]) -> None:
    """Вираховує та виводить загальну статистику сканування (відсотки онлайн/офлайн тощо)."""
    total = len(results)
    online = sum(r.status == "ONLINE" for r in results)
    offline = sum(r.status == "OFFLINE" for r in results)
    invalid = sum(r.status == "INVALID" for r in results)

    print("\n=== Scan Statistics ===")
    print(f"Total Scanned : {total}")
    print(f"Online        : {online} ({online / total * 100:.1f}%)" if total > 0 else "Online        : 0 (0.0%)")
    print(f"Offline       : {offline} ({offline / total * 100:.1f}%)" if total > 0 else "Offline       : 0 (0.0%)")
    print(f"Invalid       : {invalid} ({invalid / total * 100:.1f}%)" if total > 0 else "Invalid       : 0 (0.0%)")


def save_csv(results: list[ScanResult], out_csv: Path) -> None:
    """Зберігає результати сканування у форматі CSV-файлу."""
    # Автоматично створюємо батьківські директорії, якщо їх не існує
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        # Використовуємо поля з dataclass як заголовки стовпців у CSV
        writer = csv.DictWriter(f, fieldnames=list(asdict(results[0])))
        writer.writeheader()
        for r in results:
            writer.writerow(asdict(r))


def run_scan(targets_file: Path, timeout: float, out_csv: Path) -> None:
    """Головний бізнес-процес: зчитує цілі, запускає сканування, виводить таблицю, статистику та зберігає CSV."""
    print(f"[INFO] Starting service availability scan from {targets_file}...\n")
    targets = load_targets(targets_file)

    results = []
    for t in targets:
        # Перевіряємо кожен вузол зі списку
        r = check_target(str(t.get("host", "")), t.get("port"), timeout)
        logger.info("%s:%s -> %s (%s)", r.host, r.port, r.status, r.notes)
        results.append(r)

    if not results:
        print("[WARNING] Target list is empty.")
        return

    # Виводимо результати та записуємо звіт
    print_table(results)
    print_stats(results)
    save_csv(results, out_csv)
    print(f"\n[INFO] Detailed scan report saved to {out_csv}")


def main() -> None:
    """Точка входу в програму: обробка аргументів командного рядка та запуску сканера."""
    parser = argparse.ArgumentParser(description="Network Service Availability Scanner")
    # Аргументи командного рядка, які передає користувач
    parser.add_argument("--targets", required=True, type=Path, help="Шлях до JSON зі списком цілей")
    parser.add_argument("--timeout", default=2.0, type=float, help="Таймаут підключення (сек)")
    parser.add_argument("--out-csv", default=Path("data/scan_results.csv"), type=Path, help="CSV-файл результату")
    parser.add_argument("--verbose", action="store_true", help="Детальне логування")
    args = parser.parse_args()

    # Валідація таймауту
    if args.timeout <= 0:
        parser.error("--timeout має бути додатним числом")

    # Налаштування рівня виведення логів (INFO або WARNING)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    try:
        run_scan(args.targets, args.timeout, args.out_csv)
    except ValueError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()