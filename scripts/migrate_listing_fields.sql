-- Migration: add condition, seller quality, shipping, and country fields to listings
-- Run this in your Supabase SQL editor

ALTER TABLE listings
    ADD COLUMN IF NOT EXISTS condition              TEXT,
    ADD COLUMN IF NOT EXISTS seller_feedback_score  INT,
    ADD COLUMN IF NOT EXISTS seller_feedback_pct    NUMERIC(5,2),
    ADD COLUMN IF NOT EXISTS shipping_cost          NUMERIC(10,2),
    ADD COLUMN IF NOT EXISTS shipping_currency      TEXT,
    ADD COLUMN IF NOT EXISTS seller_country         TEXT;
