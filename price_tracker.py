import requests
from bs4 import BeautifulSoup
import time
import os
import json
import threading

BOT_TOKEN   = os.environ["BOT_TOKEN"]
CHAT_ID     = os.environ["CHAT_ID"]
SCRAPER_KEY = os.environ["SCRAPER_KEY"]
CHECK_EVERY = int(os.environ.get("CHECK_EVERY", "300"))
DATA_FILE   = "tracked.json"

def load():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f)
    return {}

def save(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def send(msg: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")

def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {"timeout": 30}
    if offset:
        params["offset"] = offset
    try:
        r = requests.get(url, params=params, timeout=35)
        return r.json().get("result", [])
    except:
        return []

def scraper_url(url):
    return f"http://api.scraperapi.com?api_key={SCRAPER_KEY}&url={url}&country_code=in"

def fetch_price(product_url):
    try:
        r = requests.get(scraper_url(product_url), timeout=60)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        selectors = [
            ".a-price-whole",
            "#priceblock_ourprice",
            "#priceblock_dealprice",
            ".a-offscreen",
            "span.a-color-price",
            "[itemprop='price']",
            ".price",
        ]
        for sel in selectors:
            el = soup.select_one(sel)
            if el:
                price = el.get_text(strip=True).split("\n")[0].strip()
                if price:
                    return price
        return None
    except Exception as e:
        print(f"Fetch error for {product_url}: {e}")
        return None

def handle_message(text: str):
    text = text.strip()
    tracked = load()

    if text.startswith("http://") or text.startswith("https://"):
        url = text
        if url in tracked:
            send(f"Already tracking this URL.")
            return
        send(f"Fetching current price, please wait...")
        price = fetch_price(url)
        if price:
            tracked[url] = price
            save(tracked)
            send(f"✅ <b>Now tracking!</b>\n📦 {url}\n💰 Current price: <b>{price}</b>")
        else:
            send(f"❌ Could not fetch price. Make sure it's a valid product URL.")

    elif text == "/list":
        if not tracked:
            send("📋 Not tracking anything yet. Send a product URL to start.")
        else:
            msg = f"📋 <b>Tracking {len(tracked)} product(s):</b>\n\n"
            for i, (url, price) in enumerate(tracked.items(), 1):
                msg += f"{i}. {url}\n   💰 Last seen: <b>{price or 'unknown'}</b>\n\n"
            send(msg)

    elif text.startswith("/remove"):
        parts = text.split(" ", 1)
        if len(parts) < 2:
            send("Usage: /remove <url>")
            return
        url = parts[1].strip()
        if url in tracked:
            del tracked[url]
            save(tracked)
            send(f"🗑 Removed from tracking.")
        else:
            send(f"URL not found in tracking list.")

    elif text == "/clear":
        save({})
        send("🗑 Cleared all tracked products.")

    elif text in ("/help", "/start"):
        send(
            "👋 <b>Price Tracker Bot</b>\n\n"
            "Send any product URL to start tracking it.\n\n"
            "<b>Commands:</b>\n"
            "/list — show all tracked products\n"
            "/remove &lt;url&gt; — stop tracking a URL\n"
            "/clear — remove all\n"
            "/help — show this message"
        )
    else:
        send("Send a product URL to track it, or /help for commands.")

def price_check_loop():
    while True:
        tracked = load()
        if tracked:
            print(f"Checking {len(tracked)} product(s)...")
            updated = dict(tracked)
            for url, last_price in tracked.items():
                price = fetch_price(url)
                if price is None:
                    print(f"  Could not fetch: {url}")
                    continue
                if price != last_price:
                    msg = (
                        f"🔔 <b>Price Changed!</b>\n"
                        f"📦 {url}\n"
                        f"  Old: {last_price}\n"
                        f"  New: <b>{price}</b>"
                    )
                    send(msg)
                    print(f"  Changed: {last_price} -> {price}")
                    updated[url] = price
                else:
                    print(f"  No change — {price}")
            save(updated)
        else:
            print("No products tracked. Send a URL to the bot.")
        time.sleep(CHECK_EVERY)

def main():
    print(f"Bot started. Interval: {CHECK_EVERY}s")
    send("🤖 <b>Price Tracker Bot is online!</b>\nSend a product URL to start tracking, or /help for commands.")

    t = threading.Thread(target=price_check_loop, daemon=True)
    t.start()

    offset = None
    while True:
        updates = get_updates(offset)
        for update in updates:
            offset = update["update_id"] + 1
            msg = update.get("message", {})
            text = msg.get("text", "")
            chat_id = str(msg.get("chat", {}).get("id", ""))
            if text and chat_id == str(CHAT_ID):
                print(f"Received: {text}")
                handle_message(text)

if __name__ == "__main__":
    main()
