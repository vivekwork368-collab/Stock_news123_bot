  import os
import requests
import yfinance as yf
import openai
import time
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ---------------- CONFIG ----------------
TOKEN = os.getenv("8601899020:AAF6xdQ9Uc2vUqE2J3g_B_iynLoVa83bfGQ")
NEWS_API_KEY = os.getenv("c5fb0e2299814a2aa8b79cbf26cbab74")
OPENAI_API_KEY = os.getenv("sk-proj-D_3aVBvNn4C4UxPiBCuGZVadH2u58DcfGyn3OLAw-Id-6ZFmLfqC12ZspA4Ku3gzjgmDvYHv9ET3BlbkFJ7_qjNrVL74PidFlWEM-fqHozI-HzqXcd9")
PORTFOLIO_FILE = "portfolio.txt"
NEWS_PER_STOCK = 5  # fetch 5 recent news
CACHE_DURATION = 1800  # 30 minutes

openai.api_key = OPENAI_API_KEY
news_cache = {}

# ---------------- HELPERS ----------------
def load_portfolio():
    if not os.path.exists(PORTFOLIO_FILE):
        return []
    with open(PORTFOLIO_FILE, "r") as f:
        return [line.strip() for line in f.readlines() if line.strip()]

def save_portfolio(stocks):
    with open(PORTFOLIO_FILE, "w") as f:
        for s in stocks:
            f.write(s + "\n")

def fetch_stock_sector(stock_symbol):
    try:
        stock = yf.Ticker(stock_symbol)
        info = stock.info
        return info.get("sector", "General")
    except:
        return "General"

def fetch_news(query, max_articles=5):
    now = time.time()
    if query in news_cache and now - news_cache[query]["time"] < CACHE_DURATION:
        return news_cache[query]["summary"]

    from_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    url = f"https://newsapi.org/v2/everything?q={query}&from={from_date}&sortBy=publishedAt&language=en&pageSize={max_articles}&apiKey={NEWS_API_KEY}"
    try:
        res = requests.get(url)
        data = res.json()
        if data.get("status") != "ok" or not data.get("articles"):
            return []
        news_list = [article.get("title","") + ". " + article.get("description","") for article in data["articles"]]
        news_cache[query] = {"time": now, "summary": news_list}
        return news_list
    except:
        return []

def summarize_news_ai(news_text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": f"Summarize this news in 2–3 lines:\n{news_text}"}],
            temperature=0.5,
            max_tokens=120
        )
        return response.choices[0].message.content.strip()
    except:
        return news_text[:300]

def analyze_sentiment_ai(news_summaries):
    combined_text = "\n".join(news_summaries)
    prompt = f"Analyze the overall market sentiment from this news for the next month: Bullish, Bearish, or Neutral. Give only one word:\n{combined_text}"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=10
        )
        return response.choices[0].message.content.strip()
    except:
        return "Neutral"

# ---------------- COMMAND HANDLERS ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Personal Portfolio Bot Started!\n"
        "Use /add STOCK to add, /remove STOCK to remove, /mylist to view portfolio, /news to get stock news and sentiment."
    )

async def mylist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stocks = load_portfolio()
    if not stocks:
        await update.message.reply_text("📂 Your portfolio is empty. Add stocks with /add STOCK")
    else:
        await update.message.reply_text("📂 Your portfolio:\n" + "\n".join(stocks))

async def add_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /add STOCK_SYMBOL")
        return
    stock = context.args[0].upper()
    stocks = load_portfolio()
    if stock in stocks:
        await update.message.reply_text(f"⚠️ {stock} is already in your portfolio.")
        return
    stocks.append(stock)
    save_portfolio(stocks)
    await update.message.reply_text(f"✅ Added {stock} to your portfolio.")

async def remove_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /remove STOCK_SYMBOL")
        return
    stock = context.args[0].upper()
    stocks = load_portfolio()
    if stock not in stocks:
        await update.message.reply_text(f"⚠️ {stock} is not in your portfolio.")
        return
    stocks.remove(stock)
    save_portfolio(stocks)
    await update.message.reply_text(f"❌ Removed {stock} from your portfolio.")

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stocks = load_portfolio()
    if not stocks:
        await update.message.reply_text("📂 Your portfolio is empty. Add stocks with /add STOCK")
        return

    messages = []
    for stock in stocks:
        sector = fetch_stock_sector(stock)
        stock_news = fetch_news(stock, NEWS_PER_STOCK)
        sector_news = fetch_news(sector, 2)

        if stock_news:
            messages.append(f"📰 {stock} news summary:")
            summarized_stock_news = [summarize_news_ai(n) for n in stock_news]
            for s in summarized_stock_news:
                messages.append(f"• {s}")
            sentiment = analyze_sentiment_ai(summarized_stock_news)
            messages.append(f"📊 Monthly Sentiment: {sentiment}")

        if sector_news:
            messages.append(f"💼 {sector} sector news summary:")
            summarized_sector_news = [summarize_news_ai(n) for n in sector_news]
            for s in summarized_sector_news:
                messages.append(f"• {s}")
            sentiment_sector = analyze_sentiment_ai(summarized_sector_news)
            messages.append(f"📊 Sector Monthly Sentiment: {sentiment_sector}")

    CHUNK_SIZE = 4000
    text = "\n".join(messages)
    for i in range(0, len(text), CHUNK_SIZE):
        await update.message.reply_text(text[i:i+CHUNK_SIZE])

# ---------------- MAIN ----------------
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("mylist", mylist))
    app.add_handler(CommandHandler("add", add_stock))
    app.add_handler(CommandHandler("remove", remove_stock))
    app.add_handler(CommandHandler("news", news))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()      
