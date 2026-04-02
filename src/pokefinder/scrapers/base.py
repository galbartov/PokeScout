"""Abstract base class for all scrapers."""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class RawListing:
    platform: str
    external_id: str | None
    url: str
    title: str
    description: str | None = None
    price: float | None = None
    currency: str = "USD"
    image_urls: list[str] = field(default_factory=list)
    seller_name: str | None = None
    seller_contact: str | None = None  # profile URL, phone, username
    location_text: str | None = None
    buying_format: str | None = None       # 'AUCTION' or 'FIXED_PRICE'
    auction_end_time: str | None = None    # ISO 8601, nullable
    condition: str | None = None           # e.g. 'New', 'Used', 'Very Good'
    seller_feedback_score: int | None = None
    seller_feedback_pct: float | None = None  # 0–100
    shipping_cost: float | None = None     # None = unknown, 0.0 = free
    shipping_currency: str | None = None
    seller_country: str | None = None
    raw_data: dict | None = None


class BaseScraper(ABC):
    platform: str

    @abstractmethod
    async def scrape(self) -> list[RawListing]:
        """Scrape listings from the source and return raw results."""
        ...

    async def run(self) -> tuple[list[RawListing], str | None]:
        """
        Execute the scrape and return (listings, error_message).
        Callers handle DB persistence.
        """
        try:
            listings = await self.scrape()
            return listings, None
        except Exception as e:
            return [], str(e)
