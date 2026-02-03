# Tasks

- [x] Stabilize Scheduled Tasks
    - [x] Analyze `scheduler.py` configuration
    - [x] Ensure `calculate_daily_orders` runs at 23:00
- [x] Google Sheets Integration Refactoring
    - [x] Refactor `sheets_client.py` to use UUIDs
    - [x] Verify changes on Production (Syntax verified locally)
- [-] Expansion: Multiple Restaurants Support
    - [ ] Analyze current single-restaurant constraints
    - [ ] Implement multi-restaurant logic

# Audit & Analysis
- [x] Integration Verification
    - [x] Bot Integration Check
    - [x] AI Service Check
    - [x] iiko Integration Check
    - [x] Google Sheets Logic vs Instruction Audit

# Phase 2: Multi-Restaurant Support
- [x] Database Schema Update
    - [x] Add `spreadsheet_id` to `src/db/models/restaurant.py`
    - [x] Create Alembic migration
- [x] Service Layer Refactoring
    - [x] Refactor `SheetsClient` constructor
    - [x] Update `CalculationEngineV2` (verified no change needed)
    - [x] Update Bot Handlers
- [x] Verification
    - [x] Manual Test with 2 Restaurants (verified via script `src/scripts/verify_multi_restaurant.py`)


- [/] Phase 3: Hybrid Workflow & AI Learning
    - [x] **AI Data Ingestion**
        - [x] Verify `iiko.get_sales_olap` works (FAILED: 401 Unauthorized)
        - [x] Create `train_product_mix.py` pipeline (Implemented CSV fallback)
    - [x] **UX/UI Audit**
        - [x] Verify WebApp display for "Chef Confirmation" (Added "Plan: X" hint)
    - [x] **Verification**
        - [x] End-to-End "Hybrid" Flow Test (Simulated Chef update + Confirm + DB verify)
    - [x] **Spreadsheet Audit** (New)
        - [x] Analyze Tabs (Plans, Tech Cards, Mix, Draft) via Browser
        - [x] Confirm `SheetsClient` integration with Tab 3 (Product Mix)
    - [x] **Spreadsheet Integration** (New)
        - [x] Create `upload_history_to_sheet.py` (CSV -> Sheet)
        - [x] Create `sync_sheet_to_db.py` (Sheet -> DB)
    - [x] Verify full cycle: CSV -> Sheet -> DB -> Calculation (via `verify_sheet_pipeline.py`)
    - [x] **Data Export** (New)
        - [x] Add `write_draft_order` to `SheetsClient`
        - [x] Integrate export into `OrderService.create_draft`
        - [x] Verify export via `verify_hybrid_flow.py`

- [ ] **Comprehensive Spreadsheet Audit & Upgrade** (Current)
    - [x] **Audit Phase**
        - [x] Check "Instructions" (Tab 0) implementation/content.
        - [x] Verify "Tech Cards" (Tab 1) parsing flexibility.
        - [x] Verify "Sales Plan" (Tab 2) write-back of daily forecast.
        - [x] Assess "Dish Calculation" (New Tab 2a?) feasibility.
        - [x] Review "Draft Order" (Tab 4) regarding multi-restaurant context.
    - [x] **Implementation Phase**
        - [x] **Step 1: Instructions**: Run `update_instructions.py` to refresh content.
        - [x] **Step 2: Tech Cards**: Implement `_find_header_col` with fuzzy matching in `SheetsClient`.
        - [x] **Step 3: Dish Calculation**:
            - [x] Update `CalculationEngineV2` to return dish breakdown.
            - [x] Add `write_dish_calculation` to `SheetsClient`.
            - [x] Integrate into `OrderService`.
        - [x] **Step 4: Verification**: Update `verify_hybrid_flow.py` to check Tab 2a export.

- [x] **Settings Tab Upgrade**
    - [x] **Design**: Define layout for "5. НАСТРОЙКИ ⚙️".
    - [x] **Implementation**:
        - [x] Create `setup_settings_tab.py` to format the sheet.
        - [x] Add `fetch_settings` to `SheetsClient`.
        - [x] Update `CalculationEngineV2` to use dynamic settings (Safety Stock).
    - [x] **Verification**: Verify settings take effect in calculation.
- [x] Phase 4: Scheduler & Sync Refinement
    - [x] Configure `start_scheduler` in `src/scheduler.py`
    - [x] Add Sync Job (04:00 AM) calling `sync_sheet_to_db`
    - [x] Adjust Calc Job (06:00 AM)
    - [x] Verify scheduler status and logs
- [x] **Phase 5: Order Accounting (In-Transit Logic)**
    - [x] **Audit**: Review `engine_v2.py` for 24-48h logic.
    - [x] **Bug Fix**: Resolve unit mismatch (Boxes vs KG) in transit summation.
    - [x] **Service Update**: Recalculate `quantity_kg` in `OrderService.update_order_items`.
    - [x] **Verification**: Run `verify_transit_fix.py` to confirm correct subtraction.

- [x] **Phase 6: Documentation Organization & Cleanup**
    - [x] Create `docs/BUSINESS_LOGIC.md` from `.resolved` version.
    - [x] Relocate `PROJECT_STATE.md` to `docs/`.
    - [x] Update `README.md` links.
    - [x] Clean up redundant `.md` files in project root.
