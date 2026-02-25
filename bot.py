import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
import yfinance as yf
import nltk
nltk.download('punkt')
from nltk.tokenize import sent_tokenize
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ---------------- CONFIG ----------------
TELEGRAM_BOT_TOKEN = "8601899020:AAF6xdQ9Uc2vUqE2J3g_B_iynLoVa83bfGQ"  # <-- Replace with your bot token
PORTFOLIO_FILE = "portfolio.txt"
MAX_MSG_LEN = 4000  # Telegram max message length

# ---------------- UTILITIES ----------------
if not os.path.exists(PORTFOLIO_FILE):
    with open(PORTFOLIO_FILE, "w") as f:
        f.write("")

def load_portfolio():
    with open(PORTFOLIO_FILE, "r") as f:
        return [line.strip().upper() for line in f if line.strip()]

def save_portfolio(stocks):
    with open(PORTFOLIO_FILE, "w") as f:
        f.write("\n".join(stocks))

def add_stock(stock):
    stocks = load_portfolio()
    stock = stock.upper()
    if stock not in stocks:
        stocks.append(stock)
        save_portfolio(stocks)
        return True
    return False

def remove_stock(stock):
    stocks = load_portfolio()
    stock = stock.upper()
    if stock in stocks:
        stocks.remove(stock)
        save_portfolio(stocks)
        return True
    return False

# ---------------- COMMANDS ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📊 Personal Portfolio Bot\n\n"
        "Commands:\n"
        "/add STOCK - Add a stock\n"
        "/remove STOCK - Remove a stock\n"
        "/mylist - Show portfolio\n"
        "/portfolio - Show stock prices\n"
        "/news - Show 2–3 line news summary"
    )

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        stock = context.args[0]
        if add_stock(stock):
            await update.message.reply_text(f"✅ Added {stock} to portfolio.")
        else:
            await update.message.reply_text(f"ℹ️ {stock} is already in portfolio.")
    else:
        await update.message.reply_text("Usage: /add STOCK")

async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        stock = context.args[0]
        if remove_stock(stock):
            await update.message.reply_text(f"❌ Removed {stock} from portfolio.")
        else:
            await update.message.reply_text(f"ℹ️ {stock} not found in portfolio.")
    else:
        await update.message.reply_text("Usage: /remove STOCK")

async def mylist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stocks = load_portfolio()
    if stocks:
        await update.message.reply_text("💼 Your portfolio:\n" + "\n".join(stocks))
    else:
        await update.message.reply_text("📂 Portfolio is empty.")

async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stocks = load_portfolio()
    if not stocks:
        await update.message.reply_text("📂 Portfolio is empty.")
        return

    messages = []
    for stock in stocks:
        try:
            data = yf.Ticker(stock).history(period="2d")
            if not data.empty:
                last_price = data["Close"][-1]
                prev_close = data["Close"][-2] if len(data) > 1 else last_price
                change = ((last_price - prev_close) / prev_close * 100) if prev_close != 0 else 0
                messages.append(f"{stock}: ₹{last_price:.2f} ({change:.2f}%)")
            else:
                messages.append(f"{stock}: Data not found")
        except Exception:
            messages.append(f"{stock}: Error fetching data")
    await update.message.reply_text("\n".join(messages))

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stocks = load_portfolio()
    if not stocks:
        await update.message.reply_text("📂 Portfolio is empty.")
        return

    messages = []
    for stock in stocks:
        try:
            # 1. Stock news
            query = stock + " stock"
            rss_url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
            response = requests.get(rss_url, timeout=5)
            soup = BeautifulSoup(response.content, "xml")
            items = soup.find_all("item")[:2]

            news_text = ""
            for item in items:
                title = item.title.text
                desc_tag = item.find("description")
                description = desc_tag.text if desc_tag else ""
                content = title + ". " + description
                sentences = sent_tokenize(content)
                summary = " ".join(sentences[:3])
                news_text += f"• {summary}\n"

            if news_text:
                messages.append(f"{stock} news:\n{news_text}")
            else:
                messages.append(f"{stock} news: No news found")

            # 2. Sector news (optional: based on first letter or using yfinance info)
            ticker = yf.Ticker(stock)
            sector = ticker.info.get("sector")
            if sector:
                sector_query = sector + " sector"
                rss_url = f"https://news.google.com/rss/search?q={sector_query}&hl=en-IN&gl=IN&ceid=IN:en"
                response = requests.get(rss_url, timeout=5)
                soup = BeautifulSoup(response.content, "xml")
                items = soup.find_all("item")[:1]  # 1 news per sector
                if items:
                    for item in items:
                        title = item.title.text
                        desc_tag = item.find("description")
                        description = desc_tag.text if desc_tag else ""
                        content = title + ". " + description
                        sentences = sent_tokenize(content)
                        summary = " ".join(sentences[:3])
                        messages.append(f"{sector} sector news:\n• {summary}\n")

        except Exception:
            messages.append(f"{stock} news: Error fetching news")

    full_message = "\n\n".join(messages)
    if len(full_message) > MAX_MSG_LEN:
        full_message = full_message[:MAX_MSG_LEN] + "\n… (truncated)"
    await update.message.reply_text(full_message)

# ---------------- MAIN ----------------
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("remove", remove))
    app.add_handler(CommandHandler("mylist", mylist))
    app.add_handler(CommandHandler("portfolio", portfolio))
    app.add_handler(CommandHandler("news", news))

    print("Bot is running...")
    app.run_polling()
