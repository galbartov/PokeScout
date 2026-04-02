"""
Test script: inject a fake auction listing ending in ~3h and run match_and_notify.
Sends a real Telegram notification to the admin if a matching preference exists.
"""
import asyncio
import sys
import os
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from pokefinder.db import get_client
from pokefinder.matching.engine import match_and_notify


async def main():
    db = await get_client()

    # Auction ends in 3 hours
    auction_end = (datetime.now(timezone.utc) + timedelta(hours=3)).isoformat()

    # Insert a fake auction listing
    record = {
        "platform": "ebay",
        "external_id": f"TEST-AUCTION-{int(datetime.now().timestamp())}",
        "url": "https://www.ebay.com/itm/999999999999",
        "title": "Pikachu Illustration Rare 173/165 Scarlet Violet 151 Pokemon Card",
        "title_normalized": "pikachu illustration rare 173/165 scarlet violet 151 pokemon card",
        "price": 55.00,
        "currency": "USD",
        "category": "singles",
        "buying_format": "AUCTION",
        "auction_end_time": auction_end,
        "image_urls": ["https://images.pokemontcg.io/sv3pt5/199_hires.png"],
        "seller_name": "test_seller",
        "raw_data": {"test": True},
    }

    print(f"Inserting test auction listing ending at {auction_end}...")
    res = await db.table("listings").insert(record).execute()
    listing_id = res.data[0]["id"]
    print(f"Inserted listing ID: {listing_id}")

    print("Running match_and_notify...")
    sent = await match_and_notify([listing_id])
    print(f"Notifications sent: {sent}")

    # Clean up
    await db.table("listings").delete().eq("id", listing_id).execute()
    print("Cleaned up test listing.")

asyncio.run(main())
