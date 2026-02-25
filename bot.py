import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# File to store user portfolio
PORTFOLIO_FILE = "portfolio.txt"

# Ensure portfolio file exists
if not os.path.exists(PORTFOLIO_FILE):
    with open(PORTFOLIO_FILE, "w") as f:
        f.write("")  # empty portfolio

# Load stocks from portfolio file
def load_portfolio():
    with open(PORTFOLIO_FILE, "r") as f:
        stocks = [line.strip() for line in f if line.strip()]
    return stocks

# Save stock to portfolio
def add_stock(stock):
    stocks = load_portfolio()
    stock = stock.upper()
    if stock not in stocks:
        stocks.append(stock)
        with open(PORTFOLIO_FILE, "w") as f:
            f.write("\n".join(stocks))
        return True
    return False

# Remove stock
def remove_stock(stock):
    stocks = load_portfolio()
    stock = stock.upper()
    if stock in stocks:
        stocks.remove(stock)
        with open(PORTFOLIO_FILE, "w") as f:
            f.write("\n".join(stocks))
        return True
    return False

# Command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📊 Personal Portfolio Bot\n\n"
        "Commands:\n"
        "/add STOCK - Add a stock\n"
        "/remove STOCK - Remove a stock\n"
        "/mylist - Show portfolio\n"
        "/portfolio - Show prices\n"
        "/news - Show 2-3 line news summary"
    )

# Command: /add
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        stock = context.args[0]
        if add_stock(stock):
            await update.message.reply_text(f"✅ Added {stock} to portfolio.")
        else:
            await update.message.reply_text(f"ℹ️ {stock} is already in portfolio.")
    else:
        await update.message.reply_text("Usage: /add STOCK")

# Command: /remove
async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        stock = context.args[0]
        if remove_stock(stock):
            await update.message.reply_text(f"❌ Removed {stock} from portfolio.")
        else:
            await update.message.reply_text(f"ℹ️ {stock} not found in portfolio.")
    else:
        await update.message.reply_text("Usage: /remove STOCK")

# Command: /mylist
async def mylist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stocks = load_portfolio()
    if stocks:
        await update.message.reply_text("💼 Your portfolio:\n" + "\n".join(stocks))
    else:
        await update.message.reply_text("📂 Portfolio is empty.")

# Command: /portfolio - show price and % change
async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stocks = load_portfolio()
    if not stocks:
        await update.message.reply_text("📂 Portfolio is empty.")
        return

    messages = []
    for stock in stocks:
        try:
            data = pd.DataFrame(yfinance.Ticker(stock).history(period="1d"))
            if not data.empty:
                last_price = data["Close"][-1]
                prev_close = data["Close"][-2] if len(data) > 1 else last_price
                change = ((last_price - prev_close) / prev_close * 100) if prev_close != 0 else 0
                messages.append(f"{stock}: ₹{last_price:.2f} ({change:.2f}%)")
            else:
                messages.append(f"{stock}: Data not found")
        except Exception as e:
            messages.append(f"{stock}: Error fetching data")
    await update.message.reply_text("\n".join(messages))

# Command: /news - 2-3 line summary
async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stocks = load_portfolio()
    if not stocks:
        await update.message.reply_text("📂 Portfolio is empty.")
        return

    messages = []
    for stock in stocks:
        try:
            # Google RSS feed for stock
            query = stock + " stock"
            rss_url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
            response = requests.get(rss_url, timeout=5)
            soup = BeautifulSoup(response.content, "xml")
            items = soup.find_all("item")[:2]  # latest 2 news items
            news_text = ""
            for item in items:
                title = item.title.text
                link = item.link.text
                news_text += f"• {title}\n{link}\n"
            if news_text:
                messages.append(f"{stock} news:\n{news_text}")
            else:
                messages.append(f"{stock} news: No news found")
        except Exception as e:
            messages.append(f"{stock} news: Error fetching news")
    await update.message.reply_text("\n".join(messages))

# --- Main ---
if __name__ == "__main__":
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN not set in environment")
        exit(1)

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("remove", remove))
    app.add_handler(CommandHandler("mylist", mylist))
    app.add_handler(CommandHandler("portfolio", portfolio))
    app.add_handler(CommandHandler("news", news))

    print("Bot is running...")
    app.run_polling()
