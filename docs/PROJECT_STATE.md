# NeuroSupply: Project State & Technical Handoff (March 2026)

## 1. Project Overview & Current State
**NeuroSupply** is a fully integrated, automated inventory and ordering system for restaurant chains. The core value proposition is stripping away the mental load of ordering from the cooks by predicting needs using AI (Linear Regression on historical iiko sales), Google Sheets integrations for master data, and both Telegram Mini Apps and Web-Dashboards for execution.

**Status:** The system is **PRODUCTION-READY (v0.8.0-beta)**. The architecture has been hardened against external risks (Telegram blocking) and localized for Vietnamese staff.

---

## 2. Key Accomplishments (March 2026 - Production Hardening)

### 2.1 Iiko Resto API Native Integration
*   **Centralized Nomenclature:** Migrated from iiko Cloud to **iiko resto (Chain Server)** to resolve UUID discrepancies.
*   **Automated Sync:** Implemented a multi-stage daily pipeline (`01:30 - 06:00`) for Products, SalesFacts, Recipes, and StockBalances.
*   **Data Integrity:** Added `UNIQUE` constraints across `products`, `stock_balances`, and `sales_plans` tables.

### 2.2 Vietnamese Localization (AI-Driven)
*   **Mass Translation:** 100% of the nomenclature (1,126 items) translated from Russian to Vietnamese using LLM (GPT-4o).
*   **Dual-Language UI:** All interfaces (Web & Bot) now display names in both languages, ensuring operational clarity for multi-ethnic teams.

### 2.3 Web-Dashboard & PWA (Stability Layer)
*   **Next.js 15+ Frontend:** Created a premium management dashboard in `/web` using **shadcn/ui** and **Glassmorphism** design.
*   **PWA Support:** Implemented "Add to Home Screen" (manifest.json). The system now works as a standalone mobile app, mitigating risks of Telegram blocking in Russia (April 2026 forecast).
*   **Modules:** 
    *   `Dashboard`: Real-time stats and health check.
    *   `Stock`: Detailed inventory tracking.
    *   `Orders`: Professional procurement interface for managers.

### 2.4 Cloudflare Tunneling
*   **Live Access:** System is served via `trycloudflare.com` for instant client demonstration.
*   **URL:** `https://nova-hundreds-her-peoples.trycloudflare.com`

---

## 3. Architecture Context

*   **Backend:** FastAPI + SQLAlchemy.
*   **Calculation Engine:** `engine_v2.py`. Formula: `Sales Plan -> Dish Qty -> Ingredient Qty`.
*   **Frontend A:** Vue 3 (Legacy Telegram Bot).
*   **Frontend B:** Next.js 15+ (Production Web Dashboard / PWA).
*   **Database:** PostgreSQL 15 + Alembic.

---

## 4. Development & Maintenance Guide

### How to Run Locally
```bash
# Start all services
docker-compose up -d --build --force-recreate

# Manual Data Sync (if needed)
docker exec neurosupply_api python3 -m src.scripts.sync_products
docker exec neurosupply_api python3 -m src.scripts.sync_stock_balances
```

### Manual Nomenclature Translation
If new products are added in iiko:
```bash
docker exec neurosupply_api python3 -m src.scripts.translate_nomenclature
```

---

## 5. Security & Risk Mitigation
*   **Telegram Blocking (Russia):** The Web Dashboard is the primary fallback. 
*   **Authentication:** RBAC implemented via Telegram ID and verified sessions.
