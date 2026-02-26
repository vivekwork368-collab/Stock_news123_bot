import asyncio
import logging
import os
import sqlite3
import re
from datetime import datetime
from collections import defaultdict
import yfinance as yf
import feedparser
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ------------------ Logging Setup ------------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ------------------ Config ------------------
TOKEN = os.getenv('TELEGRAM_TOKEN')
DB_PATH = 'stocks.db'

POSITIVE_WORDS = {
    'bullish','gain','rise','surge','rally','strong','beat','upgrade','buy',
    'positive','growth','profit'
}
NEGATIVE_WORDS = {
    'bearish','fall','drop','plunge','crash','weak','miss','downgrade','sell',
    'negative','loss','decline'
}

RSS_FEEDS = [
    # Global Business News
    'https://feeds.marketwatch.com/marketwatch/topstories/',
    'https://feeds.reuters.com/reuters/businessNews',
    'https://rss.cnn.com/rss/money_latest.rss',
    'https://feeds.bloomberg.com/markets/news.rss',

    # Tech/Stock Specific
    'https://feeds.aap.com.au/feeds/market.rss',
    'https://feeds.forbes.com/forbes/headlines',

    # Indian Markets (.NS stocks)
    'https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms',
    'https://www.moneycontrol.com/rss/latestnews.xml',

    # Finance Focused
    'https://www.investing.com/rss/news.rss',
    'https://feeds.benzinga.com/benzinga-feeds',
    'https://finance.yahoo.com/news/rssindex'
]

# ------------------ Database ------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS user_stocks (
            user_id INTEGER, 
            symbol TEXT, 
            added_date TEXT, 
            PRIMARY KEY (user_id, symbol)
        )
    ''')
    conn.commit()
    conn.close()

# ------------------ Sentiment Analysis ------------------
def get_sentiment_score(title):
    words = re.findall(r'\b\w+\b', title.lower())  # fixed regex
    pos = sum(1 for w in words if w in POSITIVE_WORDS)
    neg = sum(1 for w in words if w in NEGATIVE_WORDS)
    return pos - neg

# ------------------ Bot Commands ------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📈 *Stock Tracker Bot*\n\n"
        "Commands:\n"
        "/add AAPL - Add stock\n"
        "/add TCS.NS - Add Indian stock\n"
        "/remove AAPL - Remove stock\n"
        "/list - Your watchlist\n"
        "/news AAPL - Latest news\n"
        "/sentiment - Portfolio analysis"
    )

async def add_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text(
            "Usage: /add SYMBOL\n\n"
            "Examples:\n"
            "/add AAPL\n"
            "/add TCS.NS\n"
            "/add RELIANCE.NS"
        )
        return

    symbol = context.args[0].upper()
    # Optional: Check if valid ticker
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        if not info.get('symbol'):
            await update.message.reply_text("❌ Invalid symbol")
            return
    except:
        await update.message.reply_text("❌ Invalid symbol")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR IGNORE INTO user_stocks VALUES (?, ?, ?)",
        (user_id, symbol, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

    await update.message.reply_text(f"✅ Added *{symbol}* to watchlist!")

async def remove_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Usage: /remove SYMBOL")
        return

    symbol = context.args[0].upper()
    conn = sqlite3.connect(DB_PATH)
    result = conn.execute(
        "DELETE FROM user_stocks WHERE user_id=? AND symbol=?", 
        (user_id, symbol)
    ).rowcount
    conn.commit()
    conn.close()

    if result:
        await update.message.reply_text(f"🗑️ Removed {symbol}")
    else:
        await update.message.reply_text(f"{symbol} not found in watchlist")

async def list_stocks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect(DB_PATH)
    stocks = [row[0] for row in conn.execute(
        "SELECT symbol FROM user_stocks WHERE user_id=?", (user_id,)
    ).fetchall()]
    conn.close()

    if not stocks:
        await update.message.reply_text("📭 No stocks. Use /add SYMBOL")
        return

    msg = "📈 *Your Watchlist:*\n\n"
    for s in stocks:
        msg += f"• {s}\n"
    await update.message.reply_text(msg)

# ------------------ News ------------------
async def stock_news(symbol):
    news = []
    symbol_lower = symbol.lower().replace('.ns', '').replace('.bo', '').replace('.l', '')

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:10]:
                title_lower = entry.title.lower()
                if (symbol_lower in title_lower or 
                    symbol.lower() in title_lower or
                    symbol.replace('.NS','').lower() in title_lower or
                    symbol.replace('.BO','').lower() in title_lower):
                    score = get_sentiment_score(entry.title)
                    news.append({
                        'title': entry.title[:120],
                        'link': entry.link,
                        'score': score,
                        'source': feed.feed.get('title','News')
                    })
        except:
            continue
    return news[:5]

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /news SYMBOL")
        return

    symbol = context.args[0].upper()
    await update.message.reply_text(f"🔍 Fetching news for {symbol}...")

    news_items = await stock_news(symbol)
    if not news_items:
        await update.message.reply_text(f"❌ No news found for {symbol}")
        return

    msg = f"📰 *{symbol} News* (from 10+ sources):\n\n"
    for i, item in enumerate(news_items, 1):
        if item['score'] > 0:
            msg += f"{i}. 📈 *Bullish*: {item['title']}\n"
        elif item['score'] < 0:
            msg += f"{i}. 📉 *Bearish*: {item['title']}\n"
        else:
            msg += f"{i}. ➡️ *Neutral*: {item['title']}\n"
        msg += f"   {item['source']}\n\n"

    await update.message.reply_text(msg)

# ------------------ Weekly Sentiment ------------------
async def weekly_sentiment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect(DB_PATH)
    stocks = [row[0] for row in conn.execute(
        "SELECT symbol FROM user_stocks WHERE user_id=?", (user_id,)
    ).fetchall()]
    conn.close()

    if not stocks:
        await update.message.reply_text("📭 No stocks in watchlist")
        return

    sentiment_summary = defaultdict(int)
    total_articles = 0

    await update.message.reply_text(f"🔄 Analyzing {len(stocks)} stocks...")

    for symbol in stocks:
        news_items = await stock_news(symbol)
        for item in news_items:
            sentiment_summary[symbol] += item['score']
            total_articles += 1

    if total_articles == 0:
        await update.message.reply_text("❌ No news found for your stocks")
        return

    msg = "📊 *Weekly Sentiment Analysis*\n\n"
    for symbol, score in sentiment_summary.items():
        if score > 0:
            msg += f"📈 {symbol}: *Bullish* ({score})\n"
        elif score < 0:
            msg += f"📉 {symbol}: *Bearish* ({score})\n"
        else:
            msg += f"➡️ {symbol}: *Neutral* ({score})\n"

    msg += f"\n📈 Analyzed {total_articles} articles from 10+ sources"
    await update.message.reply_text(msg)

# ------------------ Main ------------------
async def main():
    init_db()
    logger.info("Stock Tracker Bot starting...")

    app = Application.builder().token(TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_stock))
    app.add_handler(CommandHandler("remove", remove_stock))
    app.add_handler(CommandHandler("list", list_stocks))
    app.add_handler(CommandHandler("news", news))
    app.add_handler(CommandHandler("sentiment", weekly_sentiment))

    # Run bot
    await app.run_polling()

# ------------------ Entry ------------------
if __name__ == '__main__':
    if TOKEN:
        asyncio.run(main())
    else:
        print("❌ TELEGRAM_TOKEN not set!")
