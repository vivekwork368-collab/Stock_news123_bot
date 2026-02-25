import os
import json
import asyncio
import feedparser
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
STOCK_FILE = "stocks.json"

# ================= DATABASE =================

def load_stocks():
    if not os.path.exists(STOCK_FILE):
        return []
    with open(STOCK_FILE, "r") as f:
        return json.load(f)

def save_stocks(stocks):
    with open(STOCK_FILE, "w") as f:
        json.dump(stocks, f)

# ================= COMMANDS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📈 Stock Bot Running!\n\n"
        "/add <symbol>\n"
        "/remove <symbol>\n"
        "/list\n"
        "/news <symbol>"
    )

async def add_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /add AAPL")
        return

    symbol = context.args[0].upper()
    stocks = load_stocks()

    if symbol in stocks:
        await update.message.reply_text("Already added.")
        return

    stocks.append(symbol)
    save_stocks(stocks)

    await update.message.reply_text(f"✅ Added {symbol}")

async def remove_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /remove AAPL")
        return

    symbol = context.args[0].upper()
    stocks = load_stocks()

    if symbol not in stocks:
        await update.message.reply_text("Not in list.")
        return

    stocks.remove(symbol)
    save_stocks(stocks)

    await update.message.reply_text(f"❌ Removed {symbol}")

async def list_stocks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stocks = load_stocks()

    if not stocks:
        await update.message.reply_text("No stocks added.")
        return

    await update.message.reply_text("📌 Your Stocks:\n" + "\n".join(stocks))

async def stock_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /news AAPL")
        return

    symbol = context.args[0].upper()

    feed = feedparser.parse(
        f"https://news.google.com/rss/search?q={symbol}+stock"
    )

    if not feed.entries:
        await update.message.reply_text("No news found.")
        return

    news_list = []
    for entry in feed.entries[:5]:
        news_list.append(f"📰 {entry.title}\n{entry.link}\n")

    await update.message.reply_text("\n".join(news_list))

# ================= FLASK (PORT OPENER) =================

flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)

# ================= MAIN =================

async def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_stock))
    app.add_handler(CommandHandler("remove", remove_stock))
    app.add_handler(CommandHandler("list", list_stocks))
    app.add_handler(CommandHandler("news", stock_news))

    await app.run_polling()

if __name__ == "__main__":
    # Start Flask in background thread
    Thread(target=run_flask).start()

    # Run Telegram bot in main event loop
    asyncio.run(main())
