# Руководство по Настройке и Запуску

## Требования
*   Git
*   Docker & Docker Compose (для контейнеризации)
*   Python 3.11+ (если запускаете без Docker)
*   PostgreSQL 15+ (если запускаете без Docker)

## 1. Конфигурация (.env)
Все настройки хранятся в переменных окружения.

| Переменная | Описание | Пример |
|------------|----------|--------|
| `POSTGRES_SERVER` | Хост БД | `localhost` |
| `POSTGRES_USER` | Пользователь БД | `postgres` |
| `POSTGRES_PASSWORD` | Пароль БД | `changethis` |
| `POSTGRES_DB` | Имя БД | `neurosupply` |
| `IIKO_API_LOGIN` | Логин API iikoTransport | `demo_user` |
| `TELEGRAM_BOT_TOKEN` | Токен от BotFather | `123:ABC...` |
| `OPENAI_API_KEY` | Ключ для перевода товаров | `sk-...` |
| `OPENAI_BASE_URL` | Прокси/Base URL для OpenAI | `https://api.proxyapi.ru/v1` |

## 2. Развертывание в Docker (Production-ready)
Это самый простой способ запустить систему целиком (БД + API + Бот).

1.  Клонируйте репозиторий.
2.  Создайте `.env`.
3.  Запустите:
    ```bash
    docker-compose up -d --build
    ```
    *Эта команда скачает образы Postgres, Redis (будущее), соберет образ Backend и запустит все сервисы.*

## 3. Миграции Базы Данных
При первом запуске (или обновлении схемы) необходимо применить миграции Alembic.
В Docker это часто делается автоматически (через entrypoint), но можно и вручную:

```bash
# Внутри контейнера или локально
alembic upgrade head
```

## 4. Загрузка Начальных Данных
Для работы системы нужны справочники (Товары, Рестораны).
Мы подготовили скрипт, загружающий данные из Excel (папка `data_samples`) и создающий тестовый Ресторан.

```bash
# Синхронизация товаров и остатков из iiko RESTO
docker exec neurosupply_api python3 -m src.scripts.sync_products
docker exec neurosupply_api python3 -m src.scripts.sync_stock_balances

# Массовый перевод на вьетнамский (ИИ)
docker exec neurosupply_api python3 -m src.scripts.translate_nomenclature
```

## 5. Проверка Работоспособности
1.  Откройте Telegram, найдите своего бота.
2.  Нажмите `/start`.
3.  Нажмите `/check`.
4.  Если заказ не найден, запустите расчет принудительно:
    ```bash
    python src/scripts/verify_engine.py
    ```
5.  Снова нажмите `/check` в боте. Должен появиться черновик заказа с кнопкой подтверждения.
6.  **Dashboard:** Откройте в браузере предоставленную ссылку (Cloudflare или localhost:3000). Убедитесь, что отображаются карточки статистики и таблица склада.
7.  **PWA:** На мобильном устройстве откройте URL в Safari/Chrome и выберите "На экран Домой". Появится иконка NeuroSupply.
