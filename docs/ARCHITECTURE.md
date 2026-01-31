# Архитектура NeuroSupply

Система построена по микросервисной (в будущем) архитектуре, но на данном этапе является модульным монолитом.

## Компоненты

### 1. Core API (FastAPI)
Центральный узел системы.
*   **Responsibilities**:
    *   Принимает запросы от фронтенда (в будущем) и внешних систем.
    *   Управляет циклом жизни заказа (Draft -> Verified -> Sent).
    *   Предоставляет данные для Telegram Бота.
*   **Location**: `src/api`

### 2. Calculation Engine
Модуль бизнес-логики для расчета потребностей.
*   **Algorithm**:
    1.  Запрашивает план продаж (или 7-дневную историю).
    2.  Запрашивает текущие остатки (iiko/Mock).
    3.  Вычисляет прогноз расхода: `Predicted = AvgDailyUsage * SalesPlanMultiplier`.
    4.  Вычисляет потребность: `Need = (Predicted * SafetyStock) - CurrentStock`.
    5.  Округляет до упаковок поставщика.
*   **DataSource**: `SalesPlan` (DB), `StockBalance` (DB/Iiko).
*   **Location**: `src/services/calculation`

### 3. Iiko Client
Адаптер для взаимодействия с iikoTransport API.
*   **Capabilities**:
    *   Auth (Token refresh).
    *   Fetch Products (Nomenclature).
    *   Fetch Sales (OLAP Reports).
*   **Location**: `src/services/iiko`

### 4. Telegram Bot (Aiogram)
Интерфейс для персонала ресторана.
*   **Features**:
    *   Polling-режим (запускается отдельно).
    *   Использует `OrderService` для доступа к данным (Shared Codebase).
*   **Location**: `src/bot`, `src/run_bot.py`

### 5. Database (PostgreSQL)
Основное хранилище данных.
*   **Schema**:
    *   `products`: Справочник товаров (связь с iiko_id).
    *   `restaurants`: Справочник точек.
    *   `orders`: Заказы (JSONB items).
    *   `sales_plans`: Планы выручки.

## Поток Данных (Data Flow)

1.  **Sync**: Скрипт (или Celery task) загружает Nomenclatures, Sales, Stocks из iiko -> DB.
2.  **Calculation**: `CalculationEngine` читает DB -> Создает `Order` (status=DRAFT).
3.  **Notification**: Менеджер получает уведомление (или сам пишет `/check`).
4.  **Confirmation**: Менеджер жмет "Confirm" -> API обновляет статус на `VERIFIED_BY_COOK`.
5.  **Export** (Future): Система отправляет заказ поставщику (Email/API).
