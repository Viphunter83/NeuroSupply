# API Documentation (v0.8.0)

## Base URL
Local: `http://localhost:8000/api/v1`
Production: `https://[SUBDOMAIN].trycloudflare.com/api/v1`

## Authentication
*(In progress)* Current API is open for internal use. RBAC (Role-Based Access Control) is enforced via `telegram_id` for WebApp and Bot sessions.

---

## 📦 Products (Продукты)

### Get Extra Products
Returns products available for manual addition to a draft.
*   **Endpoint**: `GET /products/extra`
*   **Query Params**: `q` (string, search query)
*   **Response**: List of product objects (ID, Name RU/VN, Unit, Category).

---

## 📝 Orders (Заказы)

### List All Orders
Retrieve a history of all orders for management view.
*   **Endpoint**: `GET /orders/` (Requires MANAGER/ADMIN role)
*   **Response**: List of orders with restaurant name, status, and item counts.

### Get Latest Draft Order
*   **Endpoint**: `GET /orders/latest`
*   **Query Params**: `restaurant_id` (UUID, optional)
*   **Behavior**: Returns existing DRAFT/VERIFIED order or generates a new one from Sales Plan.

### Confirm Order (Cook)
*   **Endpoint**: `POST /orders/{order_id}/confirm` (Requires COOK/ADMIN role)
*   **Status Change**: `DRAFT` -> `VERIFIED_BY_COOK`.

### Approve Order (Manager)
*   **Endpoint**: `POST /orders/{order_id}/approve` (Requires MANAGER/ADMIN role)
*   **Status Change**: `VERIFIED_BY_COOK` -> `APPROVED`. Triggers export to Google Sheets.

### Update Order Items
*   **Endpoint**: `PUT /orders/{order_id}` (Requires COOK/ADMIN role)
*   **Body**: List of items with `product_id` and `quantity`.

### Export to Excel
*   **Endpoint**: `GET /orders/{order_id}/export/excel` (Requires MANAGER/ADMIN role)
*   **Response**: Binary Excel file stream (.xlsx).

---

## 📊 Analytics (Аналитика)

### Forecast vs Fact
Comparison of planned revenue vs actual iiko sales.
*   **Endpoint**: `GET /analytics/forecast-vs-fact`
*   **Query Params**: `restaurant_id`, `date_from`, `date_to`.

### Dashboard Summary
Global key performance indicators.
*   **Endpoint**: `GET /analytics/summary`
*   **Data**: Active orders count, Total products, Anomalies today, AI Savings %.

### Prep Plan (Simulation)
Calculates needs without creating a formal order.
*   **Endpoint**: `GET /analytics/prep-plan`
*   **Query Params**: `restaurant_id`, `plan_amount`.

---

## 💓 System

### Health Check
*   **Endpoint**: `GET /health`
*   **Response**: `{"status": "ok", "env": "prod"}`
