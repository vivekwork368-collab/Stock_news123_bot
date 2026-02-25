import logging
import requests
import xml.etree.ElementTree as ET
import yfinance as yf
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8601899020:AAF6xdQ9Uc2vUqE2J3g_B_iynLoVa83bfGQ"

logging.basicConfig(level=logging.INFO)

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📊 Smart Stock Tracking Bot\n\n"
        "Commands:\n"
        "/track TCS - Track stock + sector news\n"
        "/price TCS - Get stock price\n"
        "/nifty - NIFTY 50 value\n"
        "/sensex - SENSEX value"
    )

# ---------------- TRACK STOCK + SECTOR NEWS ----------------
async def track(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /track TCS")
        return

    symbol_input = context.args[0].upper()
    symbol = symbol_input + ".NS"

    try:
        stock = yf.Ticker(symbol)
        info = stock.info

        company_name = info.get("longName", symbol_input)
        sector = info.get("sector", "Indian stock market")

        # Build RSS query for both stock + sector
        query = f"{company_name} OR {sector}"
        rss_url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"

        response = requests.get(rss_url, timeout=10)
        root = ET.fromstring(response.content)

        items = root.findall(".//item")[:6]

        if not items:
            await update.message.reply_text("No related news found.")
            return

        message = f"📰 News for {company_name}\nSector: {sector}\n\n"

        for item in items:
            title = item.find("title").text
            link = item.find("link").text
            message += f"🔹 {title}\n{link}\n\n"

        for i in range(0, len(message), 4000):
            await update.message.reply_text(message[i:i+4000])

    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

# ---------------- STOCK PRICE ----------------
async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /price TCS")
        return

    symbol = context.args[0].upper() + ".NS"

    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period="1d")

        if data.empty:
            await update.message.reply_text("Stock not found.")
            return

        price = round(data["Close"].iloc[-1], 2)
        await update.message.reply_text(f"📊 Current Price: ₹{price}")

    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

# ---------------- NIFTY ----------------
async def nifty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        index = yf.Ticker("^NSEI")
        data = index.history(period="1d")
        price = round(data["Close"].iloc[-1], 2)

        await update.message.reply_text(f"📈 NIFTY 50: {price}")

    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

# ---------------- SENSEX ----------------
async def sensex(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        index = yf.Ticker("^BSESN")
        data = index.history(period="1d")
        price = round(data["Close"].iloc[-1], 2)

        await update.message.reply_text(f"📈 SENSEX: {price}")

    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

# ---------------- MAIN ----------------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("track", track))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("nifty", nifty))
    app.add_handler(CommandHandler("sensex", sensex))

    print("🚀 Smart Stock Tracking Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
