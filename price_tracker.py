import requests
from bs4 import BeautifulSoup
import time
import os

BOT_TOKEN      = os.environ["BOT_TOKEN"]
CHAT_ID        = os.environ["CHAT_ID"]
PRODUCT_URL    = os.environ["PRODUCT_URL"]
CHECK_EVERY    = int(os.environ.get("CHECK_EVERY", "300"))
PRICE_SELECTOR = os.environ.get("PRICE_SELECTOR", "")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "max-age=0",
    "TE": "Trailers",
}

def send_telegram(msg: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"})

def fetch_price():
    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        r = session.get(PRODUCT_URL, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # Amazon-specific selectors in order of priority
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
            el = soup.select_one(sel)
            if el:
                price = el.get_text(strip=True)
                # Clean up — remove duplicate digits Amazon sometimes injects
                price = price.split("\n")[0].strip()
                if price:
                    print(f"Found price via '{sel}': {price}")
                    return price

        # Debug: print partial HTML to logs so we can see what Amazon returned
        print("--- PAGE SNIPPET (first 2000 chars) ---")
        print(soup.get_text()[:2000])
        print("--- END SNIPPET ---")
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
            print("Could not extract price — will retry next interval")
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
