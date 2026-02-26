import os
import sqlite3
import feedparser
import yfinance as yf
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("TELEGRAM_TOKEN")

# ---------- DATABASE SETUP ----------
conn = sqlite3.connect("stocks.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS stocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT UNIQUE
)
""")
conn.commit()

# ---------- COMMANDS ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📈 Stock News Bot\n\n"
        "/add STOCK\n"
        "/remove STOCK\n"
        "/list\n"
        "/news STOCK"
    )

# Add stock
async def add_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /add TCS")
        return
    
    symbol = context.args[0].upper()

    try:
        cursor.execute("INSERT INTO stocks (symbol) VALUES (?)", (symbol,))
        conn.commit()
        await update.message.reply_text(f"✅ {symbol} added.")
    except:
        await update.message.reply_text("⚠️ Stock already exists.")

# Remove stock
async def remove_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /remove TCS")
        return
    
    symbol = context.args[0].upper()
    cursor.execute("DELETE FROM stocks WHERE symbol=?", (symbol,))
    conn.commit()
    await update.message.reply_text(f"❌ {symbol} removed.")

# List stocks
async def list_stocks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT symbol FROM stocks")
    rows = cursor.fetchall()

    if not rows:
        await update.message.reply_text("No stocks saved.")
        return
    
    stocks = "\n".join([row[0] for row in rows])
    await update.message.reply_text(f"📌 Saved Stocks:\n{stocks}")

# News + sentiment
async def stock_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /news TCS")
        return
    
    symbol = context.args[0].upper()

    feed_url = f"https://news.google.com/rss/search?q={symbol}+stock"
    feed = feedparser.parse(feed_url)

    if not feed.entries:
        await update.message.reply_text("No news found.")
        return

    news_list = []
    sentiment_score = 0

    for entry in feed.entries[:5]:
        title = entry.title
        news_list.append(f"• {title}")

        # Simple sentiment logic
        if any(word in title.lower() for word in ["gain", "rise", "up", "profit", "growth"]):
            sentiment_score += 1
        if any(word in title.lower() for word in ["fall", "down", "loss", "decline", "drop"]):
            sentiment_score -= 1

    sentiment = "Bullish 📈" if sentiment_score > 0 else "Bearish 📉" if sentiment_score < 0 else "Neutral ⚖️"

    summary = "\n".join(news_list)

    await update.message.reply_text(
        f"📰 Latest News for {symbol}\n\n"
        f"{summary}\n\n"
        f"Weekly Sentiment: {sentiment}"
    )

# ---------- MAIN ----------

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_stock))
    app.add_handler(CommandHandler("remove", remove_stock))
    app.add_handler(CommandHandler("list", list_stocks))
    app.add_handler(CommandHandler("news", stock_news))

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import os

class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")

def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))  # Render provides PORT
    server = HTTPServer(("0.0.0.0", port), DummyHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()
