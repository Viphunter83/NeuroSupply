# Implementation Plan: Fix Calculation Logic

**Goal:** Align `CalculationEngineV2` with Business Spec v1.0.

## User Review Required
> [!IMPORTANT]
> **Goods in Transit Logic**: Currently, we define "Transit" as the sum of all items in orders with status `VERIFIED_BY_COOK` or `EXPORTED_TO_PROCOB` created in the **last 24 hours**.
>
> **Reasoning**: We lack a "RECEIVED" status. Assuming daily delivery, any order older than 24h should be either delivered (in StockBalance) or lost.
>
> **Action**: If this heuristic is too risky, we must add a `DELIVERED` status and a "Receive" button in the Bot. For v2.0, we stick to the 24h heuristic.

## Proposed Changes

### 1. Configuration (`src/core/config.py`)
- Add `SAFETY_STOCK_RATIO: float = 1.1` (10% buffer).

### 2. Calculation Engine (`src/services/calculation/engine_v2.py`)
- **Query Transit**: Fetch `VERIFIED` and `EXPORTED` orders for the restaurant from the last 24h.
- **Calculate Transit**: Sum quantities per `product_id`.
- **Apply Formula**:
    ```python
    predicted_usage = (plan_rub / 1000) * mix_prob * gross_amount
    needed_with_safety = predicted_usage * settings.SAFETY_STOCK_RATIO
    to_order_kg = max(0, needed_with_safety - current_stock - transit_qty)
    ```
- **Apply Packaging**:
    ```python
    if product.package_size and product.package_size > 0:
        packs = math.ceil(to_order_kg / product.package_size)
    else:
        # Fallback to kg if no package info
        packs = to_order_kg
    ```

### 3. API & Response
- Update the returned dictionary to include `transit_qty`, `safety_stock_qty`, and `packs_count`.

## Verification Plan

### Automated Tests
- Create a unit test `tests/test_math_logic.py`:
    - Mock DB with:
        - 1 Product (Beef, package=10kg)
        - 1 StockBalance (10kg)
        - 1 Transit Order (verified 2h ago, 5kg)
        - Sales Plan (100k, implies 45kg usage)
    - Expect:
        - Usage: 45kg
        - With Safety (1.1): 49.5kg
        - Net Need: 49.5 - 10 (Stock) - 5 (Transit) = 34.5kg
        - Packs: ceil(34.5 / 10) = 4 packs (40kg)
        - Check logic output equals 4 packs.
