import requests
from bs4 import BeautifulSoup
import time
import os

BOT_TOKEN      = os.environ["BOT_TOKEN"]
CHAT_ID        = os.environ["CHAT_ID"]
PRODUCT_URL    = os.environ["PRODUCT_URL"]
CHECK_EVERY    = int(os.environ.get("CHECK_EVERY", "300"))
PRICE_SELECTOR = os.environ.get("PRICE_SELECTOR", "")
SCRAPER_KEY    = os.environ["SCRAPER_KEY"]

def scraper_url(url):
    return f"http://api.scraperapi.com?api_key={SCRAPER_KEY}&url={url}&country_code=in"

def send_telegram(msg: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"})

def fetch_price():
    try:
        r = requests.get(scraper_url(PRODUCT_URL), timeout=60)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        selectors = [".a-price-whole","#priceblock_ourprice","#priceblock_dealprice",".a-offscreen","span.a-color-price"]
        if PRICE_SELECTOR:
            selectors = [PRICE_SELECTOR] + selectors
        for sel in selectors:
            el = soup.select_one(sel)
            if el:
                price = el.get_text(strip=True).split("\n")[0].strip()
                if price:
                    print(f"Found via '{sel}': {price}")
                    return price
        print("Could not find price in page")
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
            print("Retrying next interval...")
        elif price != last_price:
            if last_price is None:
                msg = f"🤖 <b>Price Tracker Started</b>\n📦 {PRODUCT_URL}\n💰 Current price: <b>{price}</b>"
                print(f"Initial price: {price}")
            else:
                msg = f"🔔 <b>Price Changed!</b>\n📦 {PRODUCT_URL}\n  Old: {last_price}\n  New: <b>{price}</b>"
                print(f"Price changed: {last_price} → {price}")
            send_telegram(msg)
            last_price = price
        else:
            print(f"No change — {price}")
        time.sleep(CHECK_EVERY)

if __name__ == "__main__":
    main()
