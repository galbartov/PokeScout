# PokeFinder Setup Guide

## 1. Prerequisites

- Python 3.11+
- A [Supabase](https://supabase.com) project (free tier)
- A Telegram bot token ([BotFather](https://t.me/botfather))
- Your Telegram user ID (message [@userinfobot](https://t.me/userinfobot))

Optional (add later):
- Twilio account for WhatsApp
- eBay developer account (free) for eBay scraping
- Stripe account for payments

---

## 2. Initial Setup

```bash
# Clone and install
cd PokeFinder
pip install -e ".[dev]"
playwright install chromium
```

---

## 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

At minimum, fill in:
- `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY`
- `TELEGRAM_BOT_TOKEN`
- `ADMIN_TELEGRAM_ID` (your numeric Telegram user ID)

---

## 4. Create Database Tables

1. Open your Supabase project → SQL Editor
2. Copy and paste the contents of `schema.sql`
3. Click "Run"

---

## 5. Facebook Session (Required for FB scraping)

Run this once on your local machine to save your Facebook login session:

```bash
python scripts/save_fb_session.py
```

A browser window will open. Log in to Facebook, then press Enter.
This saves `fb_session.json` — copy it to your VPS.

> ⚠️ Never commit `fb_session.json` to git (it's in `.gitignore`).
> Sessions expire periodically. The bot will alert you on Telegram when it expires.

---

## 6. Run Locally (Development)

```bash
uvicorn pokefinder.main:app --reload --port 8000
```

The Telegram bot will start in polling mode automatically.

---

## 7. Deploy to VPS (Production)

```bash
# On Hetzner VPS or similar
git clone <your-repo> /app/pokefinder
cd /app/pokefinder
cp fb_session.json .  # from step 5
cp .env .             # your production .env

docker-compose up -d
```

Set `APP_ENV=production` and `BASE_URL=https://yourdomain.com` in `.env`.

Set up a reverse proxy (nginx/caddy) to forward HTTPS to port 8000.

---

## 8. Telegram Bot Commands

User commands:
- `/start` — onboarding
- `/add` — add another preference
- `/preferences` — view/edit preferences
- `/status` — subscription status
- `/subscribe` — upgrade
- `/help` — help

Admin commands (your Telegram ID only):
- `/addgroup <url>` — add Facebook group
- `/removegroup <url>` — remove group
- `/groups` — list groups
- `/admin_stats` — stats dashboard
- `/admin_health` — scraper health

---

## 9. WhatsApp Setup (Optional, Phase 4)

1. Create a [Twilio](https://twilio.com) account
2. Enable WhatsApp Business (or use the sandbox for testing)
3. Set `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_FROM` in `.env`
4. Point your Twilio WhatsApp webhook to `https://yourdomain.com/webhooks/whatsapp`

---

## 10. Stripe Setup (Optional, Phase 4)

1. Create a [Stripe](https://stripe.com) account
2. Create a recurring product (₪20/month)
3. Copy the Price ID to `STRIPE_PRICE_ID` in `.env`
4. Add webhook endpoint in Stripe dashboard → `https://yourdomain.com/webhooks/stripe`
5. Copy the webhook secret to `STRIPE_WEBHOOK_SECRET`
