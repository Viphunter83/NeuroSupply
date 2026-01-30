# API Documentation

Ниже описаны основные эндпоинты API. Полная интерактивная документация доступна по адресу `http://localhost:8000/docs`.

## Orders (Заказы)

### 1. Получение Черновика Заказа (Draft)
Рассчитывает потребность в товарах на основе текущих остатков и прогноза.

*   **URL**: `/api/v1/order/draft`
*   **Method**: `GET`
*   **Query Params**:
    *   `restaurant_id` (UUID): ID ресторана.
*   **Response**:
    ```json
    {
      "date": "2026-01-30",
      "restaurant_id": "...",
      "items": [
        {
          "product_id": "...",
          "product_name_ru": "Огурцы",
          "amount_needed": 10.0,
          "current_stock": 5.0,
          "forecast_sales": 15.0
        }
      ]
    }
    ```

### 2. Подтверждение Заказа (Verify)
Создает подтвержденный заказ в системе на основе данных от пользователя.

*   **URL**: `/api/v1/order/verify`
*   **Method**: `POST`
*   **Body**:
    ```json
    {
      "restaurant_id": "...",
      "items": [
        {
          "product_id": "...",
          "amount": 10.0
        }
      ]
    }
    ```
*   **Response**: Объект созданного заказа.
