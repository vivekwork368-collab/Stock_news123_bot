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

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('TELEGRAM_TOKEN')
DB_PATH = 'stocks.db'

# Sentiment lexicon
POSITIVE_WORDS = {'bullish', 'gain', 'rise', 'surge', 'rally', 'strong', 'beat', 'upgrade', 'buy', 'positive'}
NEGATIVE_WORDS = {'bearish', 'fall', 'drop', 'plunge', 'crash', 'weak', 'miss', 'downgrade', 'sell', 'negative'}

# RSS feeds
RSS_FEEDS = [
    'https://feeds.marketwatch.com/marketwatch/topstories/',
    'https://feeds.reuters.com/reuters/businessNews'
]

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

def get_sentiment_score(title: str) -> int:
    words = re.findall(r'\bw+\b', title.lower())
    pos = sum(1 for w in words if w in POSITIVE_WORDS)
    neg = sum(1 for w in words if w in NEGATIVE_WORDS)
    return pos - neg

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📈 **Stock Tracker Bot**

"
        "/add AAPL - Add stock
"
        "/remove AAPL - Remove stock
"
        "/list - View your stocks
"
        "/news AAPL - Latest news
"
        "/sentiment - Weekly sentiment

"
        "✅ SQLite • RSS • yFinance • Rule-based analysis"
    )

async def add_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Usage: /add <symbol> (e.g., /add AAPL)")
        return
    
    symbol = context.args[0].upper()
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        if not info.get('symbol'):
            await update.message.reply_text(f"❌ Invalid symbol: {symbol}")
            return
    except:
        await update.message.reply_text(f"❌ Invalid symbol: {symbol}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT OR IGNORE INTO user_stocks VALUES (?, ?, ?)", 
                (user_id, symbol, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"✅ Added {symbol} ({info.get('longName', 'N/A')})")

async def remove_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Usage: /remove <symbol>")
        return
    
    symbol = context.args[0].upper()
    conn = sqlite3.connect(DB_PATH)
    result = conn.execute("DELETE FROM user_stocks WHERE user_id=? AND symbol=?", 
                         (user_id, symbol)).rowcount
    conn.commit()
    conn.close()
    
    if result:
        await update.message.reply_text(f"🗑️ Removed {symbol}")
    else:
        await update.message.reply_text(f"❌ {symbol} not in your list")

async def list_stocks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect(DB_PATH)
    stocks = conn.execute("SELECT symbol FROM user_stocks WHERE user_id=?", (user_id,)).fetchall()
    conn.close()
    
    if not stocks:
        await update.message.reply_text("📭 No stocks saved. Add some with /add AAPL")
        return
    
    stock_list = "📊 **Your Stocks:**
" + "
".join([f"• {s[0]}" for s in stocks])
    await update.message.reply_text(stock_list)

async def stock_news(symbol: str) -> list:
    news = []
    symbol_lower = symbol.lower()
    
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:5]:
                if symbol_lower in entry.title.lower() or symbol_lower in entry.get('summary', '').lower():
                    score = get_sentiment_score(entry.title)
                    news.append({
                        'title': entry.title,
                        'link': entry.link,
                        'score': score
                    })
        except:
            continue
    
    return news[:3]

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /news AAPL")
        return
    
    symbol = context.args[0].upper()
    await update.message.reply_text(f"📰 Fetching news for {symbol}...")
    
    news_items = await stock_news(symbol)
    if not news_items:
        await update.message.reply_text(f"No recent news found for {symbol}")
        return
    
    message = f"📰 **{symbol} News:**

"
    for i, item in enumerate(news_items, 1):
        sentiment = "🟢" if item['score'] > 0 else "🔴" if item['score'] < 0 else "🟡"
        message += f"{i}. {sentiment} {item['title']}
{item['link'][:60]}...

"
    
    await update.message.reply_text(message, disable_web_page_preview=True)

async def weekly_sentiment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect(DB_PATH)
    stocks = [row[0] for row in conn.execute("SELECT symbol FROM user_stocks WHERE user_id=?", (user_id,))]
    conn.close()
    
    if not stocks:
        await update.message.reply_text("📭 No stocks. Add some first!")
        return
    
    sentiment_summary = defaultdict(int)
    total_articles = 0
    
    for symbol in stocks:
        news_items = await stock_news(symbol)
        for item in news_items:
            sentiment_summary[symbol] += item['score']
            total_articles += 1
    
    if total_articles == 0:
        await update.message.reply_text("No recent news found for your stocks.")
        return
    
    message = "📊 **Weekly Sentiment:**

"
    for symbol, score in sentiment_summary.items():
        trend = "🟢 Bullish" if score > 0 else "🔴 Bearish" if score < 0 else "🟡 Neutral"
        message += f"• {symbol}: {trend} (score: {score})
"
    
    message += f"
📈 Analyzed {total_articles} articles"
    await update.message.reply_text(message)

async def main():
    init_db()
    logger.info("🚀 Stock Tracker Bot starting...")
    
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_stock))
    app.add_handler(CommandHandler("remove", remove_stock))
    app.add_handler(CommandHandler("list", list_stocks))
    app.add_handler(CommandHandler("news", news))
    app.add_handler(CommandHandler("sentiment", weekly_sentiment))
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    
    logger.info("✅ Bot running!")
    try:
        await asyncio.Event().wait()
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()

if __name__ == '__main__':
    if not TOKEN:
        logger.error("TELEGRAM_TOKEN not set!")
    else:
        asyncio.run(main())
