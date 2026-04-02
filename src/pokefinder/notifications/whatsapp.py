"""Send deal alert notifications via Twilio WhatsApp."""
from __future__ import annotations

import logging
from typing import Any

from pokefinder.config import settings

logger = logging.getLogger(__name__)


async def send_deal(
    phone: str,
    message_text: str,
    image_url: str | None = None,
) -> bool:
    """Send a deal notification to a WhatsApp number. Returns True if successful."""
    if not settings.twilio_account_sid or not settings.twilio_auth_token:
        logger.warning("Twilio not configured — skipping WhatsApp message to %s", phone)
        return False

    try:
        from twilio.rest import Client
        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)

        kwargs: dict[str, Any] = {
            "from_": settings.twilio_whatsapp_from,
            "to": f"whatsapp:{phone}",
            "body": message_text,
        }
        if image_url:
            kwargs["media_url"] = [image_url]

        client.messages.create(**kwargs)
        return True

    except Exception as e:
        logger.error("Failed to send WhatsApp notification to %s: %s", phone, e)
        return False
