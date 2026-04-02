"""
Claude Haiku vision OCR for Pokemon TCG listing images.

When a scraped post has no price or no card name detectable from text,
we send the image(s) to Claude Haiku to extract:
  - Card name(s) + Pokemon name(s)
  - Price(s)  (ignoring delivery fees like "משלוח 30₪")
  - Grade + grading company (PSA/BGS/CGC/SGC) if a graded slab is visible
  - Category hint (single / pack / booster-box / etb / etc.)

For posts with multiple products in one image (or across images),
we return multiple OcrItem entries — one per distinct product found.
"""
from __future__ import annotations

import base64
import logging
import re
from dataclasses import dataclass, field

import httpx

from pokefinder.config import settings

logger = logging.getLogger(__name__)

# Delivery-fee pattern — lines like "משלוח 30₪" or "delivery: ₪25"
_DELIVERY_RE = re.compile(
    r"(משלוח|delivery|shipping|הוצ[''״]?\s*משלוח)[^\n]*",
    re.IGNORECASE,
)

# Same price regex used in facebook.py
_PRICE_RE = re.compile(
    r"(?:₪|nis|ils|שח|ש\"ח|ש'ח|שקל)\s*(\d[\d,.]*)"
    r"|(\d[\d,.]*)\s*(?:₪|nis|ils|שח|ש\"ח|ש'ח|שקל)",
    re.IGNORECASE,
)


@dataclass
class OcrItem:
    """One product detected in an image."""
    card_name: str | None = None          # e.g. "Charizard" / "שריזארד"
    pokemon_name: str | None = None       # normalised to English if possible
    price: float | None = None
    currency: str = "ILS"
    grade_value: float | None = None
    grading_company: str | None = None    # PSA / BGS / CGC / SGC
    category_hint: str | None = None      # single / pack / etb / booster-box
    raw_text: str = ""                    # full Claude response for this item


def _should_enrich(
    title: str,
    description: str | None,
    price: float | None,
    image_urls: list[str],
) -> bool:
    """Return True if the listing needs OCR enrichment.
    Only enrich when we have images but no price — extracting the price
    is the only signal worth the API cost.
    """
    if not image_urls:
        return False
    if not settings.anthropic_api_key:
        return False

    combined = (title + " " + (description or "")).lower()
    has_price = price is not None or bool(_PRICE_RE.search(combined))
    return not has_price


async def _fetch_image_b64(url: str) -> str | None:
    """Download image and return base64-encoded bytes, or None on failure."""
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return base64.standard_b64encode(resp.content).decode()
    except Exception as e:
        logger.debug("OCR image fetch failed for %s: %s", url, e)
        return None


_SYSTEM_PROMPT = """\
You are an expert Pokemon TCG card identifier.
You will be given one or more photos of Pokemon cards, booster packs, ETBs, or graded slabs.
For EACH distinct product visible, output a JSON object.
If multiple products are shown, output a JSON array.

Each object must have these fields (use null if not detectable):
- "card_name": the card's full name as printed (e.g. "Charizard VMAX", "Pikachu ex")
- "pokemon_name": the Pokemon's base name in English (e.g. "Charizard", "Pikachu")
- "price": numeric price in ILS (Israeli Shekel).
  IMPORTANT — numbers to IGNORE:
  * Delivery/shipping fees (משלוח, delivery, shipping)
  * Dates written on sticky notes or paper (e.g. "23.3", "15/4", "2.4.25") — Israeli Facebook
    groups require sellers to include today's date in their photo; these are NOT prices.
    A date looks like DD.MM, DD/MM, or DD.MM.YY/YYYY. Prices are typically 10–5000 ₪.
  Only include the product's own sale price.
- "grading_company": one of "PSA", "BGS", "CGC", "SGC", or null
- "grade_value": numeric grade (e.g. 9, 9.5, 10), or null
- "category": one of "single", "pack", "etb", "booster-box", "collection-box", "promo", "other"

Be precise. If you cannot determine a value, use null. Do not guess prices.
Return ONLY valid JSON — no markdown fences, no explanation.
"""


async def enrich_listing(
    title: str,
    description: str | None,
    price: float | None,
    image_urls: list[str],
) -> list[OcrItem]:
    """
    Run Claude Haiku vision on listing images.
    Returns a list of OcrItem (one per detected product).
    Returns empty list if enrichment not needed or fails.
    """
    if not _should_enrich(title, description, price, image_urls):
        return []

    # Fetch only the first image — price is almost always visible in it
    images_b64: list[tuple[str, str]] = []  # (b64_data, media_type)
    for url in image_urls[:1]:
        b64 = await _fetch_image_b64(url)
        if b64:
            # Detect media type from URL extension
            ext = url.split("?")[0].rsplit(".", 1)[-1].lower()
            media_type = {
                "jpg": "image/jpeg", "jpeg": "image/jpeg",
                "png": "image/png", "webp": "image/webp", "gif": "image/gif",
            }.get(ext, "image/jpeg")
            images_b64.append((b64, media_type))

    if not images_b64:
        return []

    # Build message content — all images + question
    content: list[dict] = []
    for b64, media_type in images_b64:
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": b64,
            },
        })
    content.append({
        "type": "text",
        "text": (
            f"Post text (for context):\n{(title + ' ' + (description or ''))[:500]}\n\n"
            "Identify all Pokemon TCG products in these images and return JSON as instructed."
        ),
    })

    try:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        response = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": content}],
        )
        raw_text = response.content[0].text.strip()
    except Exception as e:
        logger.warning("Claude OCR API error: %s", e)
        return []

    return _parse_ocr_response(raw_text)


def _parse_price(val) -> float | None:
    if val is None:
        return None
    try:
        return float(str(val).replace(",", ""))
    except (ValueError, TypeError):
        return None


def _parse_grade(val) -> float | None:
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _parse_ocr_response(raw_text: str) -> list[OcrItem]:
    """Parse Claude's JSON response into OcrItem list."""
    import json

    # Strip possible markdown fences
    text = raw_text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
        text = text.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        logger.warning("OCR JSON parse error: %s — raw: %s", e, raw_text[:200])
        return []

    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        return []

    items: list[OcrItem] = []
    for obj in data:
        if not isinstance(obj, dict):
            continue
        item = OcrItem(
            card_name=obj.get("card_name"),
            pokemon_name=obj.get("pokemon_name"),
            price=_parse_price(obj.get("price")),
            grading_company=obj.get("grading_company"),
            grade_value=_parse_grade(obj.get("grade_value")),
            category_hint=obj.get("category"),
            raw_text=raw_text,
        )
        items.append(item)

    return items
