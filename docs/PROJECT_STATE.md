# NeuroSupply: Project State & Handoff (Feb 2, 2026)

## 1. Project Overview
**NeuroSupply** is an AI-driven automated ordering, inventory, and forecasting system for restaurant chains.
**Goal**: Automate 90% of procurement decisions by linking Sales Plans, Recipes (TechCards), and Dynamic Checks (Stock/Transit) to generate daily orders.

---

## 2. Current Status (Stable)
The system is currently **functional in MVP state**. Key workflows are validated:
1.  **Data Ingestion**: Google Sheets (Plan) & iiko (Menu/Ingredients) -> Postgres DB.
2.  **Calculation V2**:
    -   Sales Plan (RUB) -> Dish Qty -> Ingredient Qty.
    -   Apply Safety Stock (1.1x). 
    -   Subtract Stock Balance & Goods In Transit.
    -   **Result**: Draft Order with recommended quantities.
3.  **Telegram WebApp**:
    -   Managers view Draft Orders.
    -   Managers adjust quantities (Comments are mandatory if changed).
    -   Excel file generation (with comments).
    -   Confirmation workflow.
4.  **AI Integration**:
    -   `ForecastService` implemented (Linear Regression on historical data).
    -   Integrated into Calculation Engine (Multiplies Plan Qty).
5.  **Dashboard**:
    -   Basic Web Dashboard (`/dashboard`) comparing Forecast vs Fact.

---

## 3. System Architecture & Context

### Core Components
-   **Backend**: FastAPI, SQLAlchemy (AsyncPG), Pydantic.
-   **Database**: PostgreSQL 15.
-   **Frontend**: Vue 3 + Tailwind CSS (Telegram WebApp & Dashboard).
-   **Bot**: Aiogram 3 (Entry point for users).
-   **ML**: Scikit-Learn (Simple Forecast Model).

### Key Files Logic
-   **`src/services/calculation/engine_v2.py`**: The BRAIN. Contains the math for converting money to boxes of ingredients.
-   **`src/services/order_service.py`**: Manages Order lifecycle (Draft -> Verified), Excel export, and Anomaly tracking.
-   **`src/api/v1/endpoints/orders.py`**: API Endpoints used by WebApp.
-   **`src/frontend/src/components/OrderList.vue`**: UI for order review. Includes "Changed Quantity -> Require Comment" logic.

### Environment
-   **Docker**: `docker-compose.yml` manages `db`, `api`, `bot`, `frontend`, `nginx`.
-   **Deployment**: Runs on local/server with Docker. `docker-compose up -d --build` handles updates.

---

## 4. Work Completed This Session
-   **Fixed Critical Bug**: "Empty Order List" caused by "In Transit" logic canceling out needs. (Fix: Logic now strictly checks dates/status, and we purged stale test data).
-   **Feature**: **Mandatory Comments**. If a user changes quantity in WebApp, they *must* provide a reason.
-   **Feature**: **Excel Export**. The "Comment" column in Excel downloads is now populated.
-   **Refactoring**: Standardized on `CalculationEngineV2` and cleaned up import errors.

---

## 5. Roadmap & Next Steps (From task.md)

### Immediate Priorities (Next Session)
1.  **Stabilize Scheduled Tasks**:
    -   Ensure `scheduler.py` correctly runs `calculate_daily_orders` at 23:00 daily without manual trigger.
2.  **Google Sheets Integration**:
    -   Refactor `sheets_client.py` to use UUIDs natively (Task "Google Sheets Refactoring (IDs)" is partially done but needs final verification on Prod).
3.  **Expansion**:
    -   Add support for multiple restaurants (currently optimized for DNL, groundwork laid for ARTL).

---

## 6. Development Instructions

### How to Run
```bash
# Start all services
docker-compose up -d --build

# View Logs
docker-compose logs -f api
```

### How to Debug Calculation
```bash
# Run manual trigger inside container
docker exec neurosupply_api python src/scripts/run_calc.py
```

### Database Access
-   **Host**: `localhost` (mapped port in .env, typically 5432 or 5433)
-   **User/Pass**: See `.env`
-   **DB Name**: `neurosupply`

---

## 7. Known Issues / "Watch Outs"
-   **Transit Logic**: If you create a test order today (Status: Verified/Exported), the system considers it "In Transit" for 24h. If you run calculation *again* for the same day, it will likely return 0 items because it thinks needs are covered. **Fix**: Delete the test order or backdate it if you need to re-test calculation logic.
