"""
FastAPI application entrypoint.
Starts the Telegram bot (webhook mode in prod / polling in dev),
WhatsApp webhook, Stripe webhook, and the APScheduler.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from telegram.ext import Application

from pokefinder.bots.telegram_bot import build_onboarding_handler, register_handlers
from pokefinder.bots.telegram_bot.browser import build_browser_handler
from pokefinder.bots.telegram_bot.sealed import build_sealed_handler
from pokefinder.bots.whatsapp_bot import whatsapp_router
from pokefinder.config import settings
from pokefinder.db import get_client
from pokefinder.db import queries
from pokefinder.api.setup import router as setup_router
from pokefinder.payments import stripe_router, paddle_router
from pokefinder.scheduler import build_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

_tg_app: Application | None = None
_scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _tg_app, _scheduler

    # ── Telegram bot ──────────────────────────────────────────────────────
    _tg_app = Application.builder().token(settings.telegram_bot_token).build()
    _tg_app.add_handler(build_onboarding_handler())
    _tg_app.add_handler(build_browser_handler())
    _tg_app.add_handler(build_sealed_handler())
    register_handlers(_tg_app)

    await _tg_app.initialize()
    await _tg_app.start()

    if settings.is_production:
        # Webhook mode: Telegram sends updates to our server
        await _tg_app.bot.set_webhook(
            url=f"{settings.base_url}/webhooks/telegram",
            allowed_updates=["message", "callback_query"],
        )
        logger.info("Telegram webhook set at %s/webhooks/telegram", settings.base_url)
    else:
        # Long polling for local development
        await _tg_app.updater.start_polling(drop_pending_updates=True)
        logger.info("Telegram bot started in polling mode")

    # ── Scheduler ─────────────────────────────────────────────────────────
    _scheduler = build_scheduler()
    _scheduler.start()
    logger.info("Scheduler started (every %d min)", settings.scrape_interval_minutes)

    yield

    # ── Shutdown ──────────────────────────────────────────────────────────
    if _scheduler:
        _scheduler.shutdown()

    if _tg_app:
        if not settings.is_production:
            await _tg_app.updater.stop()
        await _tg_app.stop()
        await _tg_app.shutdown()


app = FastAPI(title="PokeFinder", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", settings.base_url],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# ── Webhook routes ────────────────────────────────────────────────────────────
app.include_router(whatsapp_router)
app.include_router(stripe_router)
app.include_router(paddle_router)
app.include_router(setup_router)


@app.post("/webhooks/telegram")
async def telegram_webhook(request: Request) -> dict:
    """Receive Telegram webhook updates (production mode only)."""
    from telegram import Update
    data = await request.json()
    update = Update.de_json(data, _tg_app.bot)
    await _tg_app.process_update(update)
    return {"ok": True}



@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "env": settings.app_env}
