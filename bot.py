import logging
import requests
import xml.etree.ElementTree as ET
import yfinance as yf
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8601899020:AAF6xdQ9Uc2vUqE2J3g_B_iynLoVa83bfGQ"

logging.basicConfig(level=logging.INFO)

CACHE = {}
CACHE_DURATION = 300  # 5 minutes
PORTFOLIO = set()

SECTOR_MAP = {
    "TCS": "IT Services",
    "INFY": "IT Services",
    "RELIANCE": "Energy",
    "HDFCBANK": "Banking",
    "ICICIBANK": "Banking",
    "SBIN": "Banking",
    "TATAMOTORS": "Automobile",
    "MARUTI": "Automobile",
    "SUNPHARMA": "Pharma"
}

def get_cached(key):
    if key in CACHE:
        data, timestamp = CACHE[key]
        if time.time() - timestamp < CACHE_DURATION:
            return data
    return None

def set_cache(key, data):
    CACHE[key] = (data, time.time())

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📊 Personal Portfolio Bot\n\n"
        "/add TCS\n"
        "/remove TCS\n"
        "/mylist\n"
        "/portfolio\n"
        "/track TCS"
    )

# ---------------- ADD STOCK ----------------
async def add_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /add TCS")
        return

    symbol = context.args[0].upper()
    PORTFOLIO.add(symbol)
    await update.message.reply_text(f"✅ {symbol} added to portfolio.")

# ---------------- REMOVE STOCK ----------------
async def remove_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /remove TCS")
        return

    symbol = context.args[0].upper()

    if symbol in PORTFOLIO:
        PORTFOLIO.remove(symbol)
        await update.message.reply_text(f"❌ {symbol} removed.")
    else:
        await update.message.reply_text("Stock not in portfolio.")

# ---------------- SHOW LIST ----------------
async def mylist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not PORTFOLIO:
        await update.message.reply_text("Portfolio empty.")
        return

    stocks = "\n".join(PORTFOLIO)
    await update.message.reply_text(f"📋 Your Portfolio:\n\n{stocks}")

# ---------------- PORTFOLIO SUMMARY ----------------
async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not PORTFOLIO:
        await update.message.reply_text("Portfolio empty.")
        return

    message = "📊 Portfolio Summary\n\n"

    for symbol in PORTFOLIO:
        cache_key = f"price_{symbol}"
        cached = get_cached(cache_key)

        if cached:
            message += cached + "\n"
            continue

        try:
            stock = yf.Ticker(symbol + ".NS")
            data = stock.history(period="1d")

            if data.empty:
                continue

            close = data["Close"].iloc[-1]
            open_price = data["Open"].iloc[-1]
            change_percent = ((close - open_price) / open_price) * 100

            sector = SECTOR_MAP.get(symbol, "Market")

            line = f"{symbol} | ₹{round(close,2)} | {round(change_percent,2)}% | {sector}"
            set_cache(cache_key, line)

            message += line + "\n"

        except:
            message += f"{symbol} | Data unavailable\n"

    await update.message.reply_text(message)

# ---------------- TRACK SINGLE STOCK ----------------
async def track(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /track TCS")
        return

    symbol = context.args[0].upper()

    try:
        stock = yf.Ticker(symbol + ".NS")
        data = stock.history(period="1d")

        if data.empty:
            await update.message.reply_text("Stock not found.")
            return

        close = data["Close"].iloc[-1]
        open_price = data["Open"].iloc[-1]
        change_percent = ((close - open_price) / open_price) * 100

        sector = SECTOR_MAP.get(symbol, "Market")

        query = f"{symbol} OR {sector}"
        rss_url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"

        response = requests.get(rss_url, timeout=10)
        root = ET.fromstring(response.content)
        items = root.findall(".//item")[:3]

        message = f"📊 {symbol}\nSector: {sector}\nPrice: ₹{round(close,2)}\nChange: {round(change_percent,2)}%\n\n📰 News:\n\n"

        for item in items:
            title = item.find("title").text
            link = item.find("link").text
            message += f"🔹 {title}\n{link}\n\n"

        await update.message.reply_text(message)

    except:
        await update.message.reply_text("⚠ Try again later.")

# ---------------- MAIN ----------------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_stock))
    app.add_handler(CommandHandler("remove", remove_stock))
    app.add_handler(CommandHandler("mylist", mylist))
    app.add_handler(CommandHandler("portfolio", portfolio))
    app.add_handler(CommandHandler("track", track))

    print("🚀 Portfolio Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
