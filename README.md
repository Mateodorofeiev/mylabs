# Лабораторна робота №2. Консольні утиліти для задач кібербезпеки

**Варіант 5:** Сканер доступності мережевих сервісів та перевірка портів.

## Встановлення залежностей

Виконуйте з кореня репозиторію в активованому віртуальному середовищі:

```
pip install -r requirements.txt
```

## Структура файлів

```
labs/lab02/
├── __init__.py
├── main.py        # команди demo та analyze
├── task1.py       # класи User, Admin, Session, AuditLog, UserAccount
├── task2.py       # сканер доступності сервісів (варіант 5)
├── README.md
└── data/
    └── data_v05/
        └── targets.json   # вхідний список хостів і портів
```

## Вхідні дані

Файл `data/data_v05/targets.json` — JSON-список об'єктів з полями `host` та `port`:

```json
[
  {"host": "127.0.0.1", "port": 22},
  {"host": "localhost", "port": 443},
  {"host": "bad host name", "port": 80}
]
```

## Приклади запуску

Демонстрація Завдання 1:

```
python -m labs.lab02.main demo
```

Аналіз (Завдання 2):

```
python -m labs.lab02.main analyze --targets labs/lab02/data/data_v05/targets.json --timeout 2 --out-csv labs/lab02/data/scan_results.csv --verbose
```

Те саме напряму через модуль:

```
python -m labs.lab02.task2 --targets labs/lab02/data/data_v05/targets.json
```

## Параметри CLI (Завдання 2)

| Параметр | Обов'язковий | Опис |
|---|---|---|
| `--targets` | так | шлях до JSON-файлу з цілями |
| `--timeout` | ні (2.0) | таймаут підключення в секундах, має бути > 0 |
| `--out-csv` | ні (`data/scan_results.csv`) | шлях до CSV-звіту |
| `--verbose` | ні | детальне логування (рівень INFO) |

## Статуси вузлів

- `ONLINE` — TCP-підключення успішне, показано час відповіді в мс.
- `OFFLINE` — підключення не вдалося (Timeout, Connection refused, DNS error).
- `INVALID` — некоректне ім'я хоста/IP або порт поза діапазоном 1–65535.

## Поведінка при помилках

- Файл не знайдено або некоректний JSON: повідомлення `[ERROR]` і завершення з кодом 1.
- Некоректний хост чи порт: запис не перевіряється мережею, отримує статус `INVALID`.
- Таймаут, відмова з'єднання, помилка DNS: статус `OFFLINE` з поясненням у колонці Notes.
- `--timeout` ≤ 0: `argparse` повідомляє про помилку.
- Порожній список цілей: попередження `[WARNING]`, звіт не створюється.

## Перевірка коду

```
ruff check .
ruff format --check .
```# mylabs