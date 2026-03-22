import requests
from bs4 import BeautifulSoup
import time
import os

BOT_TOKEN   = os.environ["BOT_TOKEN"]
CHAT_ID     = os.environ["CHAT_ID"]
PRODUCT_URL = os.environ["PRODUCT_URL"]
CHECK_EVERY = int(os.environ.get("CHECK_EVERY", "300"))
PRICE_SELECTOR = os.environ.get("PRICE_SELECTOR", "")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}

def send_telegram(msg: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"})

def fetch_price():
    try:
        r = requests.get(PRODUCT_URL, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        if PRICE_SELECTOR:
            el = soup.select_one(PRICE_SELECTOR)
            return el.get_text(strip=True) if el else None

        for attr in [
            {"itemprop": "price"},
            {"class": lambda c: c and any("price" in x.lower() for x in c)},
        ]:
            el = soup.find(attrs=attr)
            if el:
                return el.get_text(strip=True)

        meta = soup.find("meta", property="product:price:amount")
        if meta:
            return meta.get("content")

        return None
    except Exception as e:
        print(f"Error fetching price: {e}")
        return None

def main():
    print(f"Watching: {PRODUCT_URL}")
    print(f"Interval: {CHECK_EVERY}s")
    last_price = None

    while True:
        price = fetch_price()

        if price is None:
            print("Could not extract price — check PRICE_SELECTOR env var")
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
