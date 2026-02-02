
# Tasks

- [x] **Audit & Analysis**
  - [x] Create Audit Report (`audit_report.md`)
  - [x] Create Implementation Plan (`implementation_plan.md`)
  - [x] Analyze `SalesPlanParser` failure

- [x] **Math Logic Update (Calculation Engine)**
  - [x] Add `SAFETY_STOCK_RATIO` to config
  - [x] Implement "Money-to-Ingredients" logic correctly
  - [x] Add "Goods in Transit" logic (subtract verified orders from need)
  - [x] Add Packaging Rounding logic (round up to boxes)
  - [x] Verify with Unit Tests (`src/tests/test_math_logic.py`)

- [x] **Google Sheets Integration**
  - [x] Analyze new Google Sheet structure
  - [x] Rewrite `SalesPlanParser` to support Monthly Summary format
  - [x] Verify with real data loading (`src/scripts/load_real_data.py`)

- [x] **Frontend Integration**
  - [x] Dockerize Frontend (Vue.js + Vite)
  - [x] Add Frontend service to `docker-compose.yml`
  - [ ] Configure Nginx/Proxy if needed

- [x] **Testing & Quality Assurance**
  - [x] Fix existing tests in `test_calculation_engine.py`
  - [x] Add integration tests for API (Anomaly Flow)
  - [x] Test End-to-End flow (Plan -> Calc -> Order)

- [ ] **Documentation**
  - [ ] Update README.md
  - [ ] Create API Documentation
  - [ ] Document Deployment steps
