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

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('TELEGRAM_TOKEN')
DB_PATH = 'stocks.db'

POSITIVE_WORDS = {'bullish', 'gain', 'rise', 'surge', 'rally', 'strong', 'beat', 'upgrade', 'buy', 'positive'}
NEGATIVE_WORDS = {'bearish', 'fall', 'drop', 'plunge', 'crash', 'weak', 'miss', 'downgrade', 'sell', 'negative'}

RSS_FEEDS = [
    'https://feeds.marketwatch.com/marketwatch/topstories/',
    'https://feeds.reuters.com/reuters/businessNews'
]

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('CREATE TABLE IF NOT EXISTS user_stocks (user_id INTEGER, symbol TEXT, added_date TEXT, PRIMARY KEY (user_id, symbol))')
    conn.commit()
    conn.close()

def get_sentiment_score(title):
    words = re.findall(r'\b\w+\b', title.lower())
    pos = sum(1 for w in words if w in POSITIVE_WORDS)
    neg = sum(1 for w in words if w in NEGATIVE_WORDS)
    return pos - neg

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Stock Tracker Bot. /add AAPL - /remove AAPL - /list - /news AAPL - /sentiment")

async def add_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Usage: /add SYMBOL")
        return
    
    symbol = context.args[0].upper()
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        if not info.get('symbol'):
            await update.message.reply_text("Invalid symbol")
            return
    except:
        await update.message.reply_text("Invalid symbol")
        return
    
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT OR IGNORE INTO user_stocks VALUES (?, ?, ?)", (user_id, symbol, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    
    await update.message.reply_text("Added " + symbol)

async def remove_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Usage: /remove SYMBOL")
        return
    
    symbol = context.args[0].upper()
    conn = sqlite3.connect(DB_PATH)
    result = conn.execute("DELETE FROM user_stocks WHERE user_id=? AND symbol=?", (user_id, symbol)).rowcount
    conn.commit()
    conn.close()
    
    if result:
        await update.message.reply_text("Removed " + symbol)
    else:
        await update.message.reply_text(symbol + " not found")

async def list_stocks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect(DB_PATH)
    stocks = conn.execute("SELECT symbol FROM user_stocks WHERE user_id=?", (user_id,)).fetchall()
    conn.close()
    
    if not stocks:
        await update.message.reply_text("No stocks. Use /add SYMBOL")
        return
    
    msg = "Your stocks:\n"
    for s in stocks:
        msg += "- " + s[0] + "\n"
    await update.message.reply_text(msg)

async def stock_news(symbol):
    news = []
    symbol_lower = symbol.lower()
    
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:5]:
                if symbol_lower in entry.title.lower():
                    score = get_sentiment_score(entry.title)
                    news.append({'title': entry.title, 'link': entry.link, 'score': score})
        except:
            continue
    
    return news[:3]

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /news SYMBOL")
        return
    
    symbol = context.args[0].upper()
    await update.message.reply_text("Fetching news for " + symbol)
    
    news_items = await stock_news(symbol)
    if not news_items:
        await update.message.reply_text("No news found")
        return
    
    msg = symbol + " News:\n\n"
    for i, item in enumerate(news_items, 1):
        if item['score'] > 0:
            msg += str(i) + ". Bullish: " + item['title'][:100] + "\n"
        elif item['score'] < 0:
            msg += str(i) + ". Bearish: " + item['title'][:100] + "\n"
        else:
            msg += str(i) + ". Neutral: " + item['title'][:100] + "\n"
    
    await update.message.reply_text(msg)

async def weekly_sentiment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect(DB_PATH)
    stocks = [row[0] for row in conn.execute("SELECT symbol FROM user_stocks WHERE user_id=?", (user_id,))]
    conn.close()
    
    if not stocks:
        await update.message.reply_text("No stocks")
        return
    
    sentiment_summary = defaultdict(int)
    total_articles = 0
    
    for symbol in stocks:
        news_items = await stock_news(symbol)
        for item in news_items:
            sentiment_summary[symbol] += item['score']
            total_articles += 1
    
    if total_articles == 0:
        await update.message.reply_text("No news found")
        return
    
    msg = "Weekly Sentiment:\n"
    for symbol, score in sentiment_summary.items():
        if score > 0:
            msg += symbol + ": Bullish (" + str(score) + ")\n"
        elif score < 0:
            msg += symbol + ": Bearish (" + str(score) + ")\n"
        else:
            msg += symbol + ": Neutral (" + str(score) + ")\n"
    
        msg += "\nAnalyzed " + str(total_articles) + " articles\n"
await update.message.reply_text(msg)
async def main():
    init_db()
    logger.info("Stock Tracker Bot starting...")
    
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
    
    logger.info("Bot running!")
    try:
        await asyncio.Event().wait()
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()

if __name__ == '__main__':
    if TOKEN:
        asyncio.run(main())
    else:
        print("TELEGRAM_TOKEN not set!")
