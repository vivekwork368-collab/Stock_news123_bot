import logging
import requests
import xml.etree.ElementTree as ET
import yfinance as yf
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8601899020:AAF6xdQ9Uc2vUqE2J3g_B_iynLoVa83bfGQ"

logging.basicConfig(level=logging.INFO)

# Simple cache
CACHE = {}
CACHE_DURATION = 300  # 5 minutes

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📊 Smart Stock Tracking Bot\n\n"
        "/track TCS - Track stock + sector news\n"
        "/price TCS - Get stock price\n"
        "/nifty - NIFTY 50\n"
        "/sensex - SENSEX"
    )

# ---------------- CACHE HELPER ----------------
def get_cached(key):
    if key in CACHE:
        data, timestamp = CACHE[key]
        if time.time() - timestamp < CACHE_DURATION:
            return data
    return None

def set_cache(key, data):
    CACHE[key] = (data, time.time())

# ---------------- TRACK ----------------
async def track(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /track TCS")
        return

    symbol_input = context.args[0].upper()
    cache_key = f"track_{symbol_input}"

    cached_data = get_cached(cache_key)
    if cached_data:
        await update.message.reply_text(cached_data)
        return

    try:
        stock = yf.Ticker(symbol_input + ".NS")
        info = stock.info

        company_name = info.get("longName", symbol_input)
        sector = info.get("sector", "Indian stock market")

        query = f"{company_name} OR {sector}"
        rss_url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"

        response = requests.get(rss_url, timeout=10)
        root = ET.fromstring(response.content)
        items = root.findall(".//item")[:5]

        if not items:
            await update.message.reply_text("No news found.")
            return

        message = f"📰 {company_name}\nSector: {sector}\n\n"

        for item in items:
            title = item.find("title").text
            link = item.find("link").text
            message += f"🔹 {title}\n{link}\n\n"

        set_cache(cache_key, message)

        for i in range(0, len(message), 4000):
            await update.message.reply_text(message[i:i+4000])

    except Exception:
        await update.message.reply_text("⚠ Rate limited. Please try again after 1-2 minutes.")

# ---------------- PRICE ----------------
async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /price TCS")
        return

    symbol_input = context.args[0].upper()
    cache_key = f"price_{symbol_input}"

    cached_data = get_cached(cache_key)
    if cached_data:
        await update.message.reply_text(cached_data)
        return

    try:
        stock = yf.Ticker(symbol_input + ".NS")
        data = stock.history(period="1d")

        if data.empty:
            await update.message.reply_text("Stock not found.")
            return

        price_value = round(data["Close"].iloc[-1], 2)
        message = f"📊 {symbol_input} Current Price: ₹{price_value}"

        set_cache(cache_key, message)
        await update.message.reply_text(message)

    except Exception:
        await update.message.reply_text("⚠ Rate limited. Try again shortly.")

# ---------------- NIFTY ----------------
async def nifty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cache_key = "nifty"
    cached_data = get_cached(cache_key)
    if cached_data:
        await update.message.reply_text(cached_data)
        return

    try:
        index = yf.Ticker("^NSEI")
        data = index.history(period="1d")
        price = round(data["Close"].iloc[-1], 2)

        message = f"📈 NIFTY 50: {price}"
        set_cache(cache_key, message)

        await update.message.reply_text(message)

    except Exception:
        await update.message.reply_text("⚠ Rate limited. Try again later.")

# ---------------- SENSEX ----------------
async def sensex(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cache_key = "sensex"
    cached_data = get_cached(cache_key)
    if cached_data:
        await update.message.reply_text(cached_data)
        return

    try:
        index = yf.Ticker("^BSESN")
        data = index.history(period="1d")
        price = round(data["Close"].iloc[-1], 2)

        message = f"📈 SENSEX: {price}"
        set_cache(cache_key, message)

        await update.message.reply_text(message)

    except Exception:
        await update.message.reply_text("⚠ Rate limited. Try again later.")

# ---------------- MAIN ----------------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("track", track))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("nifty", nifty))
    app.add_handler(CommandHandler("sensex", sensex))

    print("🚀 Stable Smart Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
