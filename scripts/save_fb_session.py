"""
Run this script ONCE on your local machine (or VPS) to log in to Facebook
and save your session cookies to fb_session.json.

Usage:
    python scripts/save_fb_session.py

The browser will open. Log in manually, then press Enter to save cookies.
"""
import asyncio
import json


async def main() -> None:
    from playwright.async_api import async_playwright

    print("Starting browser. Log in to Facebook manually, then press Enter here.")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto("https://www.facebook.com/login")

        input("\nLog in to Facebook in the browser, then press Enter here to save cookies...")

        cookies = await context.cookies()
        with open("fb_session.json", "w") as f:
            json.dump(cookies, f)

        print(f"✅ Saved {len(cookies)} cookies to fb_session.json")
        print("Copy this file to your VPS project root and restart the app.")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
