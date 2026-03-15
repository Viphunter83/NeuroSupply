-- Add performance indices for commercial operation
-- 20260315114220_add_performance_indices.sql

-- Sales Fact indices
CREATE INDEX IF NOT EXISTS idx_sales_facts_restaurant_date ON sales_facts (restaurant_id, date);
CREATE INDEX IF NOT EXISTS idx_sales_facts_dish_id ON sales_facts (iiko_dish_id);

-- Sales Plan indices
CREATE INDEX IF NOT EXISTS idx_sales_plans_restaurant_date ON sales_plans (restaurant_id, date);

-- Order indices for faster transit calculation
CREATE INDEX IF NOT EXISTS idx_orders_restaurant_status_created ON orders (restaurant_id, status, created_at);

-- Product Mix indices
CREATE INDEX IF NOT EXISTS idx_product_mix_restaurant ON product_mix (restaurant_id);
