# Support API — Полное описание проекта

Проект: **Support API** — простой сервис поддержки магазина. Позволяет пользователю создать заявку (ticket) с опциональным файлом (фото) и позволяет специалисту добавить один ответ к заявке (response) с опциональным вложением. Реализован на FastAPI + SQLAlchemy, поддерживает локальный запуск без Docker (SQLite) и запуск в Docker Compose с PostgreSQL.


---

# 1. Структура проекта

MyProject/
├─ app/
│  ├─ __init__.py
│  ├─ main.py            # FastAPI приложение, монтирование /uploads, создание таблиц
│  ├─ config.py          # конфигурация: DATABASE_URL, UPLOAD_DIR, MAX_UPLOAD_SIZE
│  ├─ database.py        # SQLAlchemy engine, SessionLocal, Base
│  ├─ models.py          # ORM-модели Ticket и Response
│  ├─ schemas.py         # Pydantic-схемы (TicketCreate, TicketRead, ResponseCreate, ResponseRead)
│  ├─ crud.py            # функции create_ticket, get_ticket, list_tickets, create_response
│  ├─ routes.py          # все маршруты API (см. описание ниже)
│  └─ uploads/           # место хранения загруженных файлов (монтируется в docker-compose)
├─ requirements.txt
├─ Dockerfile
├─ docker-compose.yml
├─ README.md             
├─ 
└─ tests/
   └─ test_main.ps1      # простой PowerShell test script


---

# 2. Ключевые сущности и логика

### Ticket (заявка)

* Поля:

  * `id` (int, PK)
  * `full_name` (string) — ФИО пользователя
  * `contact` (string) — контакты (телефон/email)
  * `description` (text) — описание проблемы
  * `photo_filename` (string, nullable) — имя загруженного файла на диске
  * `created_at` (datetime)
* Отношения:

  * `response` — один-ко-одному (uselist=False). У тикета может быть 0 или 1 ответ.

### Response (ответ специалиста)

* Поля:

  * `id` (int, PK)
  * `ticket_id` (FK -> tickets.id), уникальное (UniqueConstraint)
  * `responder_name` (string)
  * `text` (text)
  * `media_filename` (string, nullable)
  * `status` (string) — например `open`, `pending`, `resolved`
  * `created_at` (datetime)
* Ограничение: один ответ на заявку (ticket_id уникален).

### Файлы

* Загружаются через `multipart/form-data` и сохраняются в папке `app/uploads` (или в месте, указанном `UPLOAD_DIR`).
* Ограничение размера файла задаётся переменной `MAX_UPLOAD_SIZE` (по умолчанию 10 MB).
* В ответах API в полях `photo_filename` и `media_filename` возвращается относительный URL: `/uploads/<filename>`.

---

# 3. Переменные окружения

* `DATABASE_URL` — URL базы данных SQLAlchemy.

  * Пример Postgres: `postgresql://postgres:postgres@db:5432/support_db`
  * Если не задано, приложение использует SQLite fallback: `sqlite:///../data.db` (файл `data.db` рядом с проектом).
* `UPLOAD_DIR` — путь к папке для хранения загруженных файлов. По умолчанию `app/uploads`.
* `MAX_UPLOAD_SIZE` — максимальный размер uploads в байтах (по умолчанию `10485760` = 10 MB).
* `BASE_API_URL` — опционально, для построения абсолютных ссылок (не обязателен).

---

# 4. Установка и запуск локально (без Docker)

1. Клонируйте проект и перейдите в папку:

   ```bash
   cd /path/to/MyProject
   ```

2. Создайте виртуальное окружение и установите зависимости:

   ```bash
   python -m venv .venv
   # Unix / Mac
   source .venv/bin/activate
   # Windows PowerShell
   .\.venv\Scripts\Activate.ps1

   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. (Опционально) Установить переменную окружения `DATABASE_URL` для подключения к Postgres. Если этого не делать — используется SQLite `data.db`.

4. Запустите приложение:

   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

5. Документация Swagger UI: `http://127.0.0.1:8000/docs`
   Health check: `http://127.0.0.1:8000/health`

---

# 5. Запуск с Docker Compose (Postgres + FastAPI)

Файлы `docker-compose.yml` и `Dockerfile` уже подготовлены. Порядок:

1. В корне проекта:

   ```bash
   docker-compose up --build
   ```

2. После успешного запуска:

   * API: `http://localhost:8000`
   * Swagger UI: `http://localhost:8000/docs`
   * Загруженные файлы будут в папке `app/uploads` на хосте (монтируется volume: `./app/uploads:/app/uploads`).

3. Остановить:

   ```bash
   docker-compose down
   ```

 Примечание: в `docker-compose.yml` используется `depends_on` + `healthcheck` для запуска web после того, как Postgres готов.

---

# 6. Эндпоинты (полная спецификация)

 Формат: путь — метод — параметры/тело — ответ/статусы

### `POST /tickets/` — создать заявку

* Content-Type: `multipart/form-data`
* Поля формы:

  * `full_name` (string, required)
  * `contact` (string, required)
  * `description` (string, required)
  * `photo` (file, optional)
* Успех: `201 Created`, возвращает `TicketRead` JSON.
* Ошибки:

  * `413 Payload Too Large` — файл слишком большой.
  * `500` — ошибка при сохранении файла или записи в БД.

**Пример curl:**

```bash
curl -X POST "http://localhost:8000/tickets/" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "full_name=Иван Иванов" \
  -F "contact=ivan@example.com" \
  -F "description=Неправильно работает кнопка" \
  -F "photo=@/path/to/Warframe0001.jpg;type=image/jpeg"
```

**Пример успешного ответа (201):**

```json
{
  "id": 1,
  "full_name": "Иван Иванов",
  "contact": "ivan@example.com",
  "description": "Неправильно работает кнопка",
  "photo_filename": "/uploads/8f3b2c..._Warframe0001.jpg",
  "created_at": "2026-01-01T10:34:08.255Z",
  "response": null
}
```

---

### `GET /tickets/` — список заявок

* Query params:

  * `skip` (int, default 0)
  * `limit` (int, default 100)
* Успех: `200 OK`, массив `TicketRead`.
* Каждая заявка содержит вложенный `response` (если есть).

**Пример:**

```bash
curl "http://localhost:8000/tickets/?skip=0&limit=20"
```

---

### `GET /tickets/{ticket_id}` — получить заявку по id

* Путь: `ticket_id` (int)
* Успех: `200 OK`, `TicketRead` (включая `response` если есть).
* Ошибки:

  * `404` — если заявка не найдена.

---

### `POST /tickets/{ticket_id}/response` — добавить ответ специалиста

* Content-Type: `multipart/form-data`
* Поля формы:

  * `responder_name` (string, required)
  * `status` (string, required) — например `resolved`, `pending`
  * `text` (string, optional)
  * `media` (file, optional)
* Успех: `201 Created`, возвращает `ResponseRead`.

**Пример curl:**

```bash
curl -X POST "http://localhost:8000/tickets/1/response" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "responder_name=Support Team" \
  -F "status=resolved" \
  -F "text=Проблема исправлена, перезапустите приложение" \
  -F "media=@/path/to/screenshot.png;type=image/png"
```

**Пример успешного ответа (201):**

```json
{
  "id": 1,
  "ticket_id": 1,
  "responder_name": "Support Team",
  "status": "resolved",
  "text": "Проблема исправлена, перезапустите приложение",
  "media_filename": "/uploads/4b2a..._screenshot.png",
  "created_at": "2026-01-01T11:00:00.000Z"
}
```

---

# 7. Формат схем (Pydantic)

* `TicketCreate` — вход при создании тикета: `full_name`, `contact`, `description`
* `TicketRead` — вывод: `id`, `full_name`, `contact`, `description`, `photo_filename` (или `null`), `created_at`, `response` (или `null`)
* `ResponseCreate` — вход при создании ответа: `responder_name`, `status`, `text`
* `ResponseRead` — вывод ответа: `id`, `ticket_id`, `responder_name`, `status`, `text`, `media_filename`, `created_at`

Все объекты используют `orm_mode` для преобразования SQLAlchemy-моделей в Pydantic-схемы.

---

# 8. Обработка файлов (реализация)

* Функция `save_upload_file(upload_file, upload_dir)`:

  * Создаёт уникальное имя файла: `<uuid4>_<original_basename>`.
  * Пишет файл через `shutil.copyfileobj(upload_file.file, dest)`.
  * Закрывает временный файл в блоке `finally`.
  * Проверяет размер файла через `os.path.getsize` и сравнивает с `MAX_UPLOAD_SIZE`.
  * В случае ошибки — удаляет частично записанный файл и возвращает HTTPException (500 для IO, 413 для превышения размера).

* Возвращаемые пути для клиента: `/uploads/<filename>` (статическая раздача через `app.mount("/uploads", StaticFiles(...))`).

---



# 9. Тестирование

* В `tests/test_main.ps1` есть простой PowerShell скрипт, который проверяет `/health` и `/tickets/`. Запуск на Windows PowerShell:

  ```powershell
  cd .\MyProject\tests
  .\test_main.ps1
  ```
* Для ручного тестирования используйте Swagger UI (`/docs`) — там легко отправлять multipart/form-data.

---

