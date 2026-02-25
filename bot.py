import os
import json
import requests
import feedparser
import yfinance as yf
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# ==============================
# CONFIG
# ==============================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

STOCK_FILE = "stocks.json"

# ==============================
# SIMPLE DATABASE (JSON FILE)
# ==============================

def load_stocks():
    if not os.path.exists(STOCK_FILE):
        return []
    with open(STOCK_FILE, "r") as f:
        return json.load(f)

def save_stocks(stocks):
    with open(STOCK_FILE, "w") as f:
        json.dump(stocks, f)

# ==============================
# TELEGRAM COMMANDS
# ==============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📈 Stock Bot Running!\n\n"
        "Commands:\n"
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

# ==============================
# TELEGRAM BOT RUNNER
# ==============================

def run_bot():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_stock))
    app.add_handler(CommandHandler("remove", remove_stock))
    app.add_handler(CommandHandler("list", list_stocks))
    app.add_handler(CommandHandler("news", stock_news))

    app.run_polling()

# ==============================
# FLASK APP (FOR RENDER PORT)
# ==============================

flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "Stock Telegram Bot is running!"

# ==============================
# MAIN
# ==============================

if __name__ == "__main__":
    # Run Telegram bot in background thread
    bot_thread = Thread(target=run_bot)
    bot_thread.start()

    # Run Flask server (required for Render Web Service)
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)
