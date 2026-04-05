from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str

    # Telegram
    telegram_bot_token: str
    admin_telegram_id: int  # your personal Telegram user ID (admin)

    # Twilio / WhatsApp
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_from: str = "whatsapp:+14155238886"

    # eBay
    ebay_app_id: str = ""
    ebay_client_secret: str = ""

    # pokemontcg.io
    pokemontcg_api_key: str = ""

    # Anthropic (Claude vision OCR)
    anthropic_api_key: str = ""

    # Discord
    discord_bot_token: str = ""

    # Stripe (legacy — kept for migration period)
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_id: str = ""

    # PayPal (legacy)
    paypal_client_id: str = ""
    paypal_secret: str = ""
    paypal_plan_id: str = ""
    paypal_webhook_id: str = ""

    # Paddle
    paddle_client_token: str = ""
    paddle_price_id: str = ""
    paddle_webhook_secret: str = ""

    # App
    app_env: str = "development"
    base_url: str = "http://localhost:8000"
    secret_key: str = "change-me"

    # Scraping
    scrape_interval_minutes: int = 7
    free_deals_limit: int = 10

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


settings = Settings()
