import nest_asyncio
import logging
import os
import sqlite3
import re
from datetime import datetime
from collections import defaultdict
import feedparser
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

nest_asyncio.apply()

# ------------------ Logging ------------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ------------------ Config ------------------
TOKEN = os.getenv("TELEGRAM_TOKEN")
FINNHUB_KEY = os.getenv("FINNHUB_KEY")
DB_PATH = "stocks.db"

# ------------------ Database ------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_stocks (
            user_id INTEGER,
            symbol TEXT,
            added_date TEXT,
            PRIMARY KEY (user_id, symbol)
        )
    """)
    conn.commit()
    conn.close()

# ------------------ Finnhub Backup ------------------
def get_price_finnhub(symbol):
    if not FINNHUB_KEY:
        return None

    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_KEY}"
        r = requests.get(url, timeout=5)
        data = r.json()
        price = data.get("c")

        if price and price > 0:
            return price

        return None
    except:
        return None


# ------------------ Smart Symbol Resolver ------------------
def resolve_symbol(user_input):
    user_input = user_input.upper().strip()

    # If already NSE format
    if user_input.endswith(".NS"):
        return user_input

    # If Finnhub key not set
    if not FINNHUB_KEY:
        return None

    try:
        url = f"https://finnhub.io/api/v1/search?q={user_input}&token={FINNHUB_KEY}"
        r = requests.get(url, timeout=10)
        data = r.json()

        results = data.get("result", [])

        for result in results:
            symbol = result.get("symbol", "")
            exchange = result.get("exchange", "")

            # Prefer NSE stocks
            if exchange == "NSE":
                return symbol

        # If NSE not found, return first match
        if results:
            return results[0].get("symbol")

    except Exception as e:
        print("Symbol resolve error:", e)

    return None
#------------------ Safe Price Fetch ------------------
#def get_price(symbol):
    if not FINNHUB_KEY:
        print("❌ FINNHUB_KEY missing")
        return None

    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_KEY}"
        r = requests.get(url, timeout=10)
        
        if r.status_code != 200:
            print("HTTP Error:", r.status_code)
            return None

        data = r.json()
        print("Finnhub response:", data)

        price = data.get("c")

        if price is not None and price > 0:
            return float(price)

        return None

    except Exception as e:
        print("Price fetch error:", e)
        return None 
        
# ------------------ Sentiment ------------------
POSITIVE_WORDS = {"bullish","gain","rise","surge","rally","strong","profit","growth"}
NEGATIVE_WORDS = {"bearish","drop","fall","crash","loss","decline","weak"}

def get_sentiment_score(title):
    words = re.findall(r"\b\w+\b", title.lower())
    pos = sum(1 for w in words if w in POSITIVE_WORDS)
    neg = sum(1 for w in words if w in NEGATIVE_WORDS)
    return pos - neg

# ------------------ RSS Feeds ------------------
RSS_FEEDS = [
    "https://feeds.reuters.com/reuters/businessNews",
    "https://feeds.bloomberg.com/markets/news.rss",
    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "https://www.moneycontrol.com/rss/latestnews.xml"
]

# ------------------ Commands ------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📈 Stock Tracker Bot\n\n"
        "/add SYMBOL\n"
        "/remove SYMBOL\n"
        "/list\n"
        "/price SYMBOL\n"
        "/news SYMBOL\n"
        "/sentiment"
    )
# ---------- ADD STOCK (Smart Detection) ----------
async def add_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /add SYMBOL or COMPANY NAME")
        return

    user_id = update.effective_user.id
    user_input = " ".join(context.args)

    await update.message.reply_text("🔍 Searching stock...")

    symbol = resolve_symbol(user_input)

    if not symbol:
        await update.message.reply_text("❌ Could not find stock")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR IGNORE INTO user_stocks VALUES (?, ?, ?)",
        (user_id, symbol, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

    await update.message.reply_text(f"✅ Added {symbol} to watchlist")

# ---------- REMOVE ----------
async def remove_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /remove SYMBOL")
        return

    user_id = update.effective_user.id
    symbol = context.args[0].upper()

    conn = sqlite3.connect(DB_PATH)
    result = conn.execute(
        "DELETE FROM user_stocks WHERE user_id=? AND symbol=?",
        (user_id, symbol)
    ).rowcount
    conn.commit()
    conn.close()

    if result:
        await update.message.reply_text(f"🗑 Removed {symbol}")
    else:
        await update.message.reply_text("Symbol not found")

# ---------- LIST ----------
async def list_stocks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    conn = sqlite3.connect(DB_PATH)
    stocks = [row[0] for row in conn.execute(
        "SELECT symbol FROM user_stocks WHERE user_id=?",
        (user_id,)
    ).fetchall()]
    conn.close()

    if not stocks:
        await update.message.reply_text("📭 Watchlist empty")
        return

    msg = "📈 Your Watchlist:\n\n"
    for s in stocks:
        msg += f"• {s}\n"

    await update.message.reply_text(msg)

# ---------- PRICE ----------
async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /price SYMBOL")
        return

    user_input = " ".join(context.args)
    symbol = resolve_symbol(user_input)

    if not symbol:
        await update.message.reply_text("❌ Could not find stock")
        return

    await update.message.reply_text(f"Fetching price for {symbol}...")

    price_value = get_price(symbol)

    if price_value is not None:
        await update.message.reply_text(f"💰 {symbol}: {price_value}")
    else:
        await update.message.reply_text("❌ Unable to fetch price")

# ---------- NEWS ----------
async def stock_news(symbol):
    news = []
    symbol_clean = symbol.lower().replace(".ns","")

    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:15]:

                title = entry.title.lower()

                if (
                    symbol_clean in title
                    or symbol_clean.replace(".", "") in title
                ):
                    score = get_sentiment_score(entry.title)
                    news.append((entry.title[:120], score))

        except:
            continue

    return news[:5]

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /news SYMBOL")
        return

    symbol = context.args[0].upper()
    items = await stock_news(symbol)

    if not items:
        await update.message.reply_text("No news found")
        return

    msg = f"📰 {symbol} News:\n\n"
    for title, score in items:
        sentiment = "📈 Bullish" if score > 0 else "📉 Bearish" if score < 0 else "➡ Neutral"
        msg += f"{sentiment}: {title}\n\n"

    await update.message.reply_text(msg)

# ---------- SENTIMENT ----------
async def weekly_sentiment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    conn = sqlite3.connect(DB_PATH)
    stocks = [row[0] for row in conn.execute(
        "SELECT symbol FROM user_stocks WHERE user_id=?",
        (user_id,)
    ).fetchall()]
    conn.close()

    if not stocks:
        await update.message.reply_text("No stocks in watchlist")
        return

    summary = defaultdict(int)

    for symbol in stocks:
        news_items = await stock_news(symbol)
        for _, score in news_items:
            summary[symbol] += score

    msg = "📊 Weekly Sentiment:\n\n"
    for symbol, score in summary.items():
        if score > 0:
            msg += f"📈 {symbol}: Bullish ({score})\n"
        elif score < 0:
            msg += f"📉 {symbol}: Bearish ({score})\n"
        else:
            msg += f"➡ {symbol}: Neutral\n"

    await update.message.reply_text(msg)

# ------------------ Run ------------------
def run_bot():
    print("🚀 Bot Live")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_stock))
    app.add_handler(CommandHandler("remove", remove_stock))
    app.add_handler(CommandHandler("list", list_stocks))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("news", news))
    app.add_handler(CommandHandler("sentiment", weekly_sentiment))

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    init_db()
    if TOKEN:
        run_bot()
    else:
        print("TELEGRAM_TOKEN missing")
