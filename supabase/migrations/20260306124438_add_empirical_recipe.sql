CREATE TABLE IF NOT EXISTS public.empirical_recipes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dish_name VARCHAR NOT NULL,
    ingredient_name VARCHAR NOT NULL,
    product_id UUID REFERENCES public.products(id) ON DELETE SET NULL,
    yield_rate NUMERIC(10, 4) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_empirical_recipes_dish_name ON public.empirical_recipes(dish_name);
CREATE INDEX IF NOT EXISTS ix_empirical_recipes_ingredient_name ON public.empirical_recipes(ingredient_name);
