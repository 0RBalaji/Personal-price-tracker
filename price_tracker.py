import time
import os
import requests
from playwright.sync_api import sync_playwright

BOT_TOKEN      = os.environ["BOT_TOKEN"]
CHAT_ID        = os.environ["CHAT_ID"]
PRODUCT_URL    = os.environ["PRODUCT_URL"]
CHECK_EVERY    = int(os.environ.get("CHECK_EVERY", "300"))
PRICE_SELECTOR = os.environ.get("PRICE_SELECTOR", "")

def send_telegram(msg: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"})

def fetch_price():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox"]
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                locale="en-IN",
                viewport={"width": 1280, "height": 800},
            )
            page = context.new_page()
            page.goto(PRODUCT_URL, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3000)

            selectors = [
                ".a-price-whole",
                "#priceblock_ourprice",
                "#priceblock_dealprice",
                "#priceblock_saleprice",
                ".a-offscreen",
                "span.a-color-price",
            ]

            if PRICE_SELECTOR:
                selectors = [PRICE_SELECTOR] + selectors

            for sel in selectors:
                el = page.query_selector(sel)
                if el:
                    price = el.inner_text().strip().split("\n")[0].strip()
                    if price:
                        print(f"Found price via '{sel}': {price}")
                        browser.close()
                        return price

            text = page.inner_text("body")
            print("--- PAGE SNIPPET ---")
            print(text[:2000])
            print("--- END ---")
            browser.close()
            return None

    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    print(f"Watching: {PRODUCT_URL}")
    print(f"Interval: {CHECK_EVERY}s")
    last_price = None

    while True:
        price = fetch_price()

        if price is None:
            print("Could not extract price — will retry")
        elif price != last_price:
            if last_price is None:
                msg = (
                    f"🤖 <b>Price Tracker Started</b>\n"
                    f"📦 {PRODUCT_URL}\n"
                    f"💰 Current price: <b>{price}</b>"
                )
                print(f"Initial price: {price}")
            else:
                msg = (
                    f"🔔 <b>Price Changed!</b>\n"
                    f"📦 {PRODUCT_URL}\n"
                    f"  Old: {last_price}\n"
                    f"  New: <b>{price}</b>"
                )
                print(f"Price changed: {last_price} → {price}")

            send_telegram(msg)
            last_price = price
        else:
            print(f"No change — {price}")

        time.sleep(CHECK_EVERY)

if __name__ == "__main__":
    main()
