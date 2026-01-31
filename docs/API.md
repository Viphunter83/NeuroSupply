# API Documentation

## Base URL
Local: `http://localhost:8000/api/v1`

## Authentication
*(В разработке)* В данный момент API открыт. В будущем будет использоваться JWT Bearer Token.

---

## Orders (Заказы)

### Get Latest Draft Order
Получает последний черновик заказа для указанного ресторана.

*   **Endpoint**: `GET /order/latest`
*   **Query Params**:
    *   `restaurant_id` (UUID): ID ресторана (обязательно).
*   **Response (200 OK)**:
    ```json
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "restaurant_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "created_at": "2026-01-31T10:00:00Z",
      "status": "DRAFT",
      "items": [
        {
          "product_id": "uuid",
          "product_name": "Milk",
          "quantity": 5,
          "stock": 2
        }
      ]
    }
    ```

### Confirm Order
Подтверждает заказ (переводит статус в `VERIFIED_BY_COOK`).

*   **Endpoint**: `POST /order/{order_id}/confirm`
*   **Path Params**:
    *   `order_id` (UUID): ID заказа.
*   **Response (200 OK)**:
    *   Возвращает обновленный объект Order с новым статусом.

---

## Health Check

### Service Health
*   **Endpoint**: `GET /health`
*   **Response**: `{"status": "ok", "env": "dev"}`
