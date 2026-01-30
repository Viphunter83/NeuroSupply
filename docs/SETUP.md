# Установка и Конфигурация

## Предварительные требования
*   Docker & Docker Compose
*   Python 3.11+ (для локального запуска)
*   PostgreSQL 16 (для локального запуска)
*   Redis (для локального запуска)

## Переменные Окружения
Создайте файл `.env` в корне проекта. Пример содержимого:

```ini
# Приложение
APP_ENV=development
LOG_LEVEL=INFO

# PostgreSQL (Docker Internal)
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=neurosupply
POSTGRES_HOST=db
POSTGRES_PORT=5432

# PostgreSQL Connection String
# Для Docker контейнеров (используется host 'db')
# PG_DSN=postgresql+asyncpg://user:password@db:5432/neurosupply
# Для локального запуска скриптов (используется host 'localhost' и порт 5433)
PG_DSN=postgresql+asyncpg://user:password@localhost:5433/neurosupply

# Redis
REDIS_URL=redis://redis:6379/0

# Iiko Cloud API
IIKO_API_LOGIN=ваш_логин_api
IIKO_API_KEY=ваш_ключ_api

# Telegram
BOT_TOKEN=ваш_токен_бота
WEBAPP_URL=https://your-webapp-domain.com
```

## Запуск в Docker (Рекомендуется)
Полный стек (БД, Redis, API, Worker, Bot) запускается одной командой:

```bash
docker-compose up -d --build
```
*   **API**: `http://localhost:8000`
*   **DB**: Порт `5433` (снаружи), `5432` (внутри)
*   **Redis**: Порт `6379`

## Локальная Разработка
1.  Создайте виртуальное окружение:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
2.  Установите зависимости:
    ```bash
    pip install -e .
    ```
3.  Запустите необходимые сервисы (БД, Redis) через Docker (если нет локальных):
    ```bash
    docker-compose up -d db redis
    ```
4.  Примените миграции:
    ```bash
    alembic upgrade head
    ```
5.  Запустите API:
    ```bash
    uvicorn src.main:app --reload --port 8000
    ```

## Полезные Команды

### Миграции БД
*   Создать новую миграцию:
    ```bash
    alembic revision --autogenerate -m "описание_изменений"
    ```
*   Применить миграции:
    ```bash
    alembic upgrade head
    ```

### Загрузка начальных данных
Загрузка товаров из Excel файла:
```bash
python src/scripts/load_initial_products.py
```
**Примечание:** Убедитесь, что `PG_DSN` в `.env` настроен на `localhost` при запуске скрипта локально.
