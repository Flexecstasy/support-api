


# Support API

API для сбора заявок в техподдержку магазина.  
Используется FastAPI + Postgres, развёртывание через Docker Compose.

## Запуск

1. Склонируйте репозиторий:

```bash
git clone https://github.com/Flexecstasy/support-api.git
cd support-api
````

2. Создайте папку для тестовых файлов:

```bash
mkdir uploads
```

3. Запустите Docker Compose:

```bash
docker-compose up --build
```

FastAPI будет доступен на `http://localhost:8000`.

## Тестирование

Используйте Python-скрипт:

```bash
python test_api.py
```

Он создаст тикеты, добавит ответ и выведет список всех тикетов.

## Структура проекта

* `backend/app/` – исходный код FastAPI (модели, схемы, маршруты)
* `backend/Dockerfile` – образ для backend
* `docker-compose.yml` – backend + Postgres
* `uploads/` – папка для загруженных файлов
* `test_api.py` – тестовый скрипт API

```


