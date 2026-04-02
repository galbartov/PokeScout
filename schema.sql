-- PokeFinder — Supabase Schema
-- Run this in your Supabase SQL editor

-- ── USERS ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_id             BIGINT UNIQUE,
    telegram_username       TEXT,
    whatsapp_phone          TEXT UNIQUE,          -- E.164 e.g. "+972501234567"
    display_name            TEXT,
    locale                  TEXT DEFAULT 'en',
    location_lat            DOUBLE PRECISION,
    location_lon            DOUBLE PRECISION,
    location_name           TEXT,
    is_active               BOOLEAN DEFAULT TRUE,
    free_deals_used         INT DEFAULT 0,
    is_subscribed           BOOLEAN DEFAULT FALSE,
    stripe_customer_id      TEXT,
    subscription_expires_at TIMESTAMPTZ,
    notification_channels   JSONB DEFAULT '["telegram"]',  -- ["telegram","whatsapp"]
    created_at              TIMESTAMPTZ DEFAULT now(),
    updated_at              TIMESTAMPTZ DEFAULT now()
);

-- ── PREFERENCES ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS preferences (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name              TEXT NOT NULL,
    categories        JSONB DEFAULT '[]',     -- ["sealed","singles","graded","bulk"]
    keywords          JSONB DEFAULT '[]',     -- ["charizard","etb"]
    sets              JSONB DEFAULT '[]',     -- ["151","Obsidian Flames"]
    price_min         NUMERIC(10,2),
    price_max         NUMERIC(10,2),
    currency          TEXT DEFAULT 'ILS',
    radius_km         INT,
    grading_companies JSONB DEFAULT '[]',     -- ["PSA","BGS","CGC"]
    min_grade         NUMERIC(3,1),
    tcg_product_id    TEXT,                   -- pokemontcg.io card ID or sealed slug
    tcg_product_name  TEXT,                   -- confirmed display name
    is_active         BOOLEAN DEFAULT TRUE,
    created_at        TIMESTAMPTZ DEFAULT now(),
    updated_at        TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_pref_user ON preferences(user_id);

-- ── TCG PRODUCTS CACHE ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS tcg_products_cache (
    id           TEXT PRIMARY KEY,           -- pokemontcg.io ID or sealed slug
    product_type TEXT NOT NULL,              -- 'card' | 'sealed'
    name_en      TEXT NOT NULL,

    set_name     TEXT,
    aliases      JSONB DEFAULT '[]',
    raw_data     JSONB,
    cached_at    TIMESTAMPTZ DEFAULT now()
);

-- ── LISTINGS ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS listings (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform         TEXT NOT NULL,           -- 'ebay'
    external_id      TEXT,
    url              TEXT NOT NULL,
    title            TEXT NOT NULL,
    title_normalized TEXT,
    description      TEXT,
    price            NUMERIC(10,2),
    currency         TEXT DEFAULT 'ILS',
    image_urls       JSONB DEFAULT '[]',
    image_hash       TEXT,
    seller_name      TEXT,
    seller_contact   TEXT,
    location_text    TEXT,
    category         TEXT,                    -- 'sealed'|'singles'|'graded'|'bulk'
    detected_grade   TEXT,
    grading_company  TEXT,
    grade_value      NUMERIC(3,1),
    tcg_product_id   TEXT,                    -- matched product if found
    buying_format    TEXT,                    -- 'AUCTION' | 'FIXED_PRICE'
    auction_end_time TIMESTAMPTZ,             -- null for fixed-price listings
    raw_data         JSONB,
    dedup_cluster    UUID,
    scraped_at       TIMESTAMPTZ DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_listing_external ON listings(platform, external_id)
    WHERE external_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_listing_hash    ON listings(image_hash);
CREATE INDEX IF NOT EXISTS idx_listing_scraped ON listings(scraped_at);

-- ── NOTIFICATIONS ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS notifications (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    listing_id    UUID NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    preference_id UUID REFERENCES preferences(id),
    channel       TEXT NOT NULL DEFAULT 'telegram',  -- 'telegram' | 'whatsapp'
    status        TEXT DEFAULT 'sent',
    sent_at       TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, listing_id)
);
CREATE INDEX IF NOT EXISTS idx_notif_user ON notifications(user_id, sent_at);

-- ── SCRAPE RUNS ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS scrape_runs (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform       TEXT NOT NULL,
    status         TEXT DEFAULT 'running',   -- 'running'|'completed'|'failed'
    listings_found INT DEFAULT 0,
    new_listings   INT DEFAULT 0,
    duration_ms    INT,
    error_message  TEXT,
    started_at     TIMESTAMPTZ DEFAULT now(),
    completed_at   TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_scrape_platform ON scrape_runs(platform, started_at);

-- ── SETUP TOKENS ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS setup_tokens (
    token       TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at  TIMESTAMPTZ NOT NULL,
    used        BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_setup_tokens_user ON setup_tokens(user_id);
