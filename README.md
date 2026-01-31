# NeuroSupply - Автономная Система Управления Запасами

## Обзор
**NeuroSupply** - это интеллектуальная система для автоматизации управления запасами ресторанов, интегрированная с iikoCloud. Система анализирует продажи, рассчитывает потребности в закупках, формирует черновики заказов и позволяет управляющим подтверждать их через Telegram-бота.

## ✨ Ключевые Возможности
*   **Интеграция с iikoCloud**: Автоматический импорт меню, продаж и остатков (OLAP, Stock Balances).
*   **Умный Расчет Заказа**: Алгоритм на основе прогноза расхода (среднее за 7 дней) и текущих остатков с учетом страхового запаса (Safety Stock).
*   **Telegram Бот**:
    *   Просмотр актуального черновика заказа (`/check`).
    *   Подтверждение заказа в один клик.
*   **API & Админка**: REST API для верификации и управления заказами.
*   **Тестовый Режим**: Генерация мок-данных продаж для тестирования логики без "живой" кассы.

## 🛠 Технологический Стек
*   **Язык**: Python 3.11+
*   **Web Framework**: FastAPI (Async)
*   **Database**: PostgreSQL 16 + SQLAlchemy (Async) + Alembic
*   **Bot**: Aiogram 3.x
*   **Infrastructure**: Docker, Docker Compose

## 🚀 Быстрый Старт

### 1. Предварительные требования
*   Docker & Docker Compose
*   (Опционально) Python 3.11+ для локального запуска

### 2. Настройка окружения
Создайте файл `.env` в корне проекта (см. `.env.example`):
```bash
cp .env.example .env
```
Заполните ключи:
*   `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`...
*   `IIKO_API_LOGIN` - Логин API iiko (или оставьте пустым для Mock-режима)
*   `TELEGRAM_BOT_TOKEN` - Токен от @BotFather

### 3. Запуск в Docker (Рекомендуется)
```bash
docker-compose up -d --build
```
*   **API**: `http://localhost:8000/docs`
*   **DB**: `localhost:5432`

### 4. Локальный Запуск (Для разработки)
```bash
# Активация окружения
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Запуск базы (если не в Docker)
docker-compose up -d postgres

# Применение миграций
alembic upgrade head

# Запуск API
./venv/bin/python src/main.py

# Запуск Бота (в отдельном терминале)
./venv/bin/python src/run_bot.py
```

## 📚 Документация
*   [🛠 Руководство по установке и настройке (Setup)](docs/SETUP.md)
*   [🏗 Архитектура системы (Architecture)](docs/ARCHITECTURE.md)
*   [🔌 API Reference](docs/API.md)

## ✅ Текущий Статус
Система находится в активной разработке. Реализованы базовые сценарии (MVP):
- [x] Импорт данных
- [x] Расчет заказа
- [x] Сохранение в БД
- [x] Подтверждение через Бота

Подробный лог задач: `task.md`
