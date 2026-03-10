-- Migration: Add analytics tables (anomalies, sales_facts, product_mix)
-- Created at: 2026-03-10 01:47:55

CREATE TABLE IF NOT EXISTS public.product_mix (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID NOT NULL REFERENCES public.restaurants(id) ON DELETE CASCADE,
    product_id UUID REFERENCES public.products(id) ON DELETE SET NULL,
    iiko_dish_id VARCHAR,
    probability NUMERIC(10, 4) NOT NULL
);

CREATE TABLE IF NOT EXISTS public.sales_facts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID NOT NULL REFERENCES public.restaurants(id) ON DELETE CASCADE,
    iiko_dish_id VARCHAR NOT NULL,
    dish_name VARCHAR NOT NULL,
    date TIMESTAMP WITH TIME ZONE NOT NULL,
    quantity NUMERIC(10, 4) NOT NULL,
    revenue_rub NUMERIC(10, 2) NOT NULL
);

CREATE TABLE IF NOT EXISTS public.anomalies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES public.orders(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES public.products(id) ON DELETE CASCADE,
    auto_qty NUMERIC(10, 4) NOT NULL,
    manual_qty NUMERIC(10, 4) NOT NULL,
    reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indices for performance
CREATE INDEX IF NOT EXISTS ix_product_mix_restaurant_id ON public.product_mix(restaurant_id);
CREATE INDEX IF NOT EXISTS ix_sales_facts_restaurant_id ON public.sales_facts(restaurant_id);
CREATE INDEX IF NOT EXISTS ix_sales_facts_date ON public.sales_facts(date);
CREATE INDEX IF NOT EXISTS ix_anomalies_order_id ON public.anomalies(order_id);
