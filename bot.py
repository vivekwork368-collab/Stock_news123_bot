import os
import sqlite3
import feedparser
import yfinance as yf
from openai import OpenAI
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# =========================
# ENV VARIABLES
# =========================
TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN is missing!")

client = OpenAI(api_key=OPENAI_API_KEY)

# =========================
# DATABASE SETUP
# =========================
conn = sqlite3.connect("stocks.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS stocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT UNIQUE
)
""")
conn.commit()

# =========================
# COMMANDS
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📈 Stock Intelligence Bot is running!")

# ADD STOCK
async def add_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /add AAPL")
        return

    symbol = context.args[0].upper()

    try:
        cursor.execute("INSERT INTO stocks (symbol) VALUES (?)", (symbol,))
        conn.commit()
        await update.message.reply_text(f"✅ {symbol} added.")
    except:
        await update.message.reply_text("⚠️ Stock already exists.")

# REMOVE STOCK
async def remove_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /remove AAPL")
        return

    symbol = context.args[0].upper()
    cursor.execute("DELETE FROM stocks WHERE symbol=?", (symbol,))
    conn.commit()
    await update.message.reply_text(f"❌ {symbol} removed.")

# LIST STOCKS
async def list_stocks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT symbol FROM stocks")
    rows = cursor.fetchall()

    if not rows:
        await update.message.reply_text("No stocks saved.")
        return

    text = "📌 Saved Stocks:\n"
    for row in rows:
        text += f"- {row[0]}\n"

    await update.message.reply_text(text)

# NEWS COMMAND
async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /news AAPL")
        return

    symbol = context.args[0].upper()
    feed = feedparser.parse(f"https://news.google.com/rss/search?q={symbol}+stock")

    headlines = []
    for entry in feed.entries[:5]:
        headlines.append(entry.title)

    if not headlines:
        await update.message.reply_text("No news found.")
        return

    text = f"📰 Latest News for {symbol}:\n\n"
    for h in headlines:
        text += f"- {h}\n"

    await update.message.reply_text(text)

# ANALYZE COMMAND
async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /analyze AAPL")
        return

    symbol = context.args[0].upper()

    # 1️⃣ Get Weekly Price
    try:
        data = yf.download(symbol, period="7d", interval="1d")
        open_price = data["Open"][0]
        close_price = data["Close"][-1]

        if close_price > open_price:
            bias = "Bullish"
        elif close_price < open_price:
            bias = "Bearish"
        else:
            bias = "Neutral"
    except:
        bias = "Unknown"

    # 2️⃣ Get News Headlines
    feed = feedparser.parse(f"https://news.google.com/rss/search?q={symbol}+stock")
    headlines = [entry.title for entry in feed.entries[:5]]

    # 3️⃣ AI Summary
    summary_text = "No AI summary available."
    if OPENAI_API_KEY and headlines:
        try:
            prompt = f"""
            These are recent headlines about {symbol}:
            {headlines}

            Summarize briefly and suggest if next week looks bullish or bearish.
            """

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )

            summary_text = response.choices[0].message.content
        except:
            summary_text = "AI summary failed."

    final_text = f"""
📊 Weekly Technical Bias: {bias}

🧠 AI Market Summary:
{summary_text}
"""

    await update.message.reply_text(final_text)

# =========================
# MAIN
# =========================
import asyncio
import os

PORT = int(os.environ.get("PORT", 10000))
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("add", add_stock))
app.add_handler(CommandHandler("remove", remove_stock))
app.add_handler(CommandHandler("list", list_stocks))
app.add_handler(CommandHandler("news", news))
app.add_handler(CommandHandler("analyze", analyze))

async def main():
    await app.initialize()
    
    # Set webhook URL
    webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
    await app.bot.set_webhook(webhook_url)

    # Start webhook server
    await app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=webhook_url,
        url_path="webhook"
    )

asyncio.run(main())

import threading
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run_web():
    app.run(host="0.0.0.0", port=10000)

threading.Thread(target=run_web).start()
