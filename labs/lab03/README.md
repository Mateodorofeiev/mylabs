# Лабораторна робота №3. Варіант 5

## Облік спрацювань засобів захисту

Сервіс зберігає підсумки спрацювань засобів захисту за навчальні інтервали.

- **categories**: джерело спрацювання (`firewall`, `ids`, `antivirus`).
- **records**: запис із полями `id`, `code`, `title`, `category_id`, `value`, `status`.
- **value**: кількість спрацювань, ціле число не менше 0 (одиниця: `events`).
- **status**: `new`, `in_progress`, `done`.
- **Поріг**: 15 events (лише довідково, логіки реагування немає).

Усі дані навчальні.

## Встановлення

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Початкове заповнення (з кореня репозиторію)

```bash
python -m labs.lab03.seed
```

Повторний запуск не змінює дані.

## Запуск API

```bash
uvicorn labs.lab03.main:app --reload --host 127.0.0.1 --port 8000
```

Документація: http://127.0.0.1:8000/docs

## Приклади запитів

```bash
curl -i "http://127.0.0.1:8000/ping"
curl -i "http://127.0.0.1:8000/records?category_id=1&status=new&limit=5&offset=0"
curl -i -X POST "http://127.0.0.1:8000/records" \
  -H "Content-Type: application/json" \
  -d '{"code":"V05-TEST","title":"Тестовий підсумок","category_id":1,"value":12,"status":"new"}'
```

## Перевірка коду

```bash
ruff check .
ruff format --check .
```