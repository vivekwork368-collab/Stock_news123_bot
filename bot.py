import os
import sqlite3
import feedparser
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN is not set!")

# SQLite setup
conn = sqlite3.connect("stocks.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS stocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT UNIQUE
)
""")
conn.commit()

# Commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📈 Stock News Bot\n\n"
        "/add STOCK\n"
        "/remove STOCK\n"
        "/list\n"
        "/news STOCK"
    )

async def add_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /add TCS")
        return
    symbol = context.args[0].upper()
    try:
        cursor.execute("INSERT INTO stocks (symbol) VALUES (?)", (symbol,))
        conn.commit()
        await update.message.reply_text(f"✅ {symbol} added.")
    except sqlite3.IntegrityError:
        await update.message.reply_text("⚠️ Stock already exists.")

async def list_stocks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT symbol FROM stocks")
    rows = cursor.fetchall()
    if not rows:
        await update.message.reply_text("No stocks saved.")
        return
    await update.message.reply_text("📌 Saved Stocks:\n" + "\n".join(r[0] for r in rows))

async def stock_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /news TCS")
        return
    symbol = context.args[0].upper()
    feed = feedparser.parse(f"https://news.google.com/rss/search?q={symbol}+stock")
    if not feed.entries:
        await update.message.reply_text("No news found.")
        return

    news_list = []
    sentiment_score = 0
    for entry in feed.entries[:5]:
        title = entry.title
        news_list.append(f"• {title}")
        if any(word in title.lower() for word in ["gain", "rise", "up", "profit", "growth"]):
            sentiment_score += 1
        if any(word in title.lower() for word in ["fall", "down", "loss", "decline", "drop"]):
            sentiment_score -= 1

    sentiment = "Bullish 📈" if sentiment_score > 0 else "Bearish 📉" if sentiment_score < 0 else "Neutral ⚖️"
    await update.message.reply_text(f"📰 Latest News for {symbol}\n\n" + "\n".join(news_list) + f"\n\nWeekly Sentiment: {sentiment}")

# Run bot
async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_stock))
    app.add_handler(CommandHandler("list", list_stocks))
    app.add_handler(CommandHandler("news", stock_news))

    print("Bot running...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
