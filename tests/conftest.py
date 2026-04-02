import os

# Set required env vars before any imports
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "123:test")
os.environ.setdefault("ADMIN_TELEGRAM_ID", "12345")
