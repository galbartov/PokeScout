"""Send deal alert notifications via Telegram (with image)."""
from __future__ import annotations

import logging

import httpx
from telegram import Bot
from telegram.constants import ParseMode

from pokefinder.config import settings

logger = logging.getLogger(__name__)
_bot: Bot | None = None


def _get_bot() -> Bot:
    global _bot
    if _bot is None:
        _bot = Bot(token=settings.telegram_bot_token)
    return _bot


async def send_deal(
    telegram_id: int,
    message_text: str,
    image_url: str | None = None,
) -> int | None:
    """Send a deal notification. Returns message_id if successful, None on failure."""
    bot = _get_bot()
    try:
        if image_url:
            # Try passing URL directly first (faster, works for public images)
            try:
                msg = await bot.send_photo(
                    chat_id=telegram_id,
                    photo=image_url,
                    caption=message_text,
                    parse_mode=ParseMode.MARKDOWN,
                )
                return msg.message_id
            except Exception:
                pass

            # Fallback: download and upload bytes (works for CDN-protected images)
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    img_resp = await client.get(image_url, follow_redirects=True)
                    img_resp.raise_for_status()
                    image_bytes = img_resp.content

                try:
                    msg = await bot.send_photo(
                        chat_id=telegram_id,
                        photo=image_bytes,
                        caption=message_text,
                        parse_mode=ParseMode.MARKDOWN,
                    )
                except Exception:
                    msg = await bot.send_photo(
                        chat_id=telegram_id,
                        photo=image_bytes,
                        caption=message_text,
                        parse_mode=None,
                    )
                return msg.message_id
            except Exception as img_err:
                logger.debug("Image send failed, falling back to text: %s", img_err)

        # Text-only — try Markdown first, fall back to plain text if parse fails
        try:
            msg = await bot.send_message(
                chat_id=telegram_id,
                text=message_text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=False,
            )
            return msg.message_id
        except Exception:
            msg = await bot.send_message(
                chat_id=telegram_id,
                text=message_text,
                parse_mode=None,
                disable_web_page_preview=False,
            )
            return msg.message_id

    except Exception as e:
        logger.error("Failed to send Telegram notification to %s: %s", telegram_id, e)
        return None


async def edit_deal(
    telegram_id: int,
    message_id: int,
    new_text: str,
) -> bool:
    """Edit an existing message. Returns True if successful."""
    bot = _get_bot()
    try:
        await bot.edit_message_caption(
            chat_id=telegram_id,
            message_id=message_id,
            caption=new_text,
            parse_mode=ParseMode.MARKDOWN,
        )
        return True
    except Exception:
        try:
            await bot.edit_message_text(
                chat_id=telegram_id,
                message_id=message_id,
                text=new_text,
                parse_mode=ParseMode.MARKDOWN,
            )
            return True
        except Exception as e:
            logger.debug("Failed to edit Telegram message %s: %s", message_id, e)
            return False
