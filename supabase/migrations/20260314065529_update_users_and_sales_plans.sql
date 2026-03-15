-- Migration: Update users and sales_plans for Unified Web Platform
-- Created at: 2026-03-14 06:55:29

-- 1. Update Users Table
-- Add primary key ID if not exists, and make telegram_id nullable/unique
DO $$ 
BEGIN
    -- Add UUID id column as primary key candidate
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='id') THEN
        ALTER TABLE public.users ADD COLUMN id UUID DEFAULT gen_random_uuid();
        
        -- Move PK from telegram_id to id
        ALTER TABLE public.users DROP CONSTRAINT users_pkey;
        ALTER TABLE public.users ADD PRIMARY KEY (id);
        
        -- Make telegram_id unique
        ALTER TABLE public.users ADD CONSTRAINT uq_users_telegram_id UNIQUE (telegram_id);
    END IF;

    -- Add supabase_user_id
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='supabase_user_id') THEN
        ALTER TABLE public.users ADD COLUMN supabase_user_id UUID UNIQUE;
    END IF;
END $$;

-- 2. Update Sales Plans Table
-- Add timestamps if not exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='sales_plans' AND column_name='created_at') THEN
        ALTER TABLE public.sales_plans ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
        ALTER TABLE public.sales_plans ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
    END IF;
END $$;

-- 3. Add unique constraint to sales_plans (one plan per restaurant per day)
-- This might fail if there's duplicate data, so we use a safe approach
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_sales_plans_restaurant_date') THEN
        ALTER TABLE public.sales_plans ADD CONSTRAINT uq_sales_plans_restaurant_date UNIQUE (restaurant_id, date);
    END IF;
END $$;
