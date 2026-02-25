# bot.py

import os
import yfinance as yf
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# -------- CONFIGURATION --------
TOKEN = 8601899020:AAF6xdQ9Uc2vUqE2J3g_B_iynLoVa83bfGQ  # Your Telegram Bot Token
NEWS_API_KEY = os.environ.get("c5fb0e2299814a2aa8b79cbf26cbab74")  # Your News API Key
PORTFOLIO_FILE = "portfolio.txt"

# -------- HELPER FUNCTIONS --------
def load_portfolio():
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE, "r") as f:
            return set(f.read().splitlines())
    return set()

def save_portfolio(portfolio):
    with open(PORTFOLIO_FILE, "w") as f:
        f.write("\n".join(portfolio))

def get_stock_info(stock):
    try:
        ticker = yf.Ticker(stock)
        info = ticker.info
        price = info.get('regularMarketPrice', 'N/A')
        change = info.get('regularMarketChangePercent', 0)
        sector = info.get('sector', 'Unknown')
        return price, change, sector
    except:
        return 'N/A', 0, 'Unknown'

def get_stock_news(stock):
    try:
        url = f"https://newsapi.org/v2/everything?q={stock}&apiKey={NEWS_API_KEY}&pageSize=1&sortBy=publishedAt"
        data = requests.get(url).json()
        articles = data.get('articles')
        if articles:
            headline = articles[0]['title']
            return headline if len(headline) <= 120 else headline[:117] + "..."
        return "No recent news."
    except:
        return "Error fetching news."

# -------- BOT COMMANDS --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "💼 Personal Portfolio Bot\n\n"
        "/add STOCK - Add stock to portfolio\n"
        "/remove STOCK - Remove stock\n"
        "/mylist - Show your portfolio\n"
        "/portfolio - Show stock prices & sector\n"
        "/news - Latest news summary\n"
    )
    await update.message.reply_text(msg)

async def add_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    portfolio = load_portfolio()
    if context.args:
        stock = context.args[0].upper()
        portfolio.add(stock)
        save_portfolio(portfolio)
        await update.message.reply_text(f"{stock} added to your portfolio ✅")
    else:
        await update.message.reply_text("Usage: /add STOCK")

async def remove_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    portfolio = load_portfolio()
    if context.args:
        stock = context.args[0].upper()
        if stock in portfolio:
            portfolio.remove(stock)
            save_portfolio(portfolio)
            await update.message.reply_text(f"{stock} removed from your portfolio ✅")
        else:
            await update.message.reply_text(f"{stock} not in portfolio ❌")
    else:
        await update.message.reply_text("Usage: /remove STOCK")

async def mylist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    portfolio = load_portfolio()
    if portfolio:
        msg = "📈 Your Portfolio:\n" + "\n".join(portfolio)
    else:
        msg = "Your portfolio is empty. Add stocks using /add STOCK"
    await update.message.reply_text(msg)

async def portfolio_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    portfolio = load_portfolio()
    if not portfolio:
        await update.message.reply_text("Your portfolio is empty. Use /add STOCK")
        return

    msg = "💹 Portfolio Summary:\n"
    for stock in portfolio:
        price, change, sector = get_stock_info(stock)
        msg += f"{stock} | ₹{price} | {change:.2f}% | {sector}\n"
    await update.message.reply_text(msg)

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    portfolio = load_portfolio()
    if not portfolio:
        await update.message.reply_text("Your portfolio is empty. Use /add STOCK")
        return

    msg = "📰 Latest News:\n"
    for stock in portfolio:
        price, change, sector = get_stock_info(stock)
        summary = get_stock_news(stock)
        msg += f"{stock} | ₹{price} | {change:.2f}% | {sector}\nNews: {summary}\n\n"
    await update.message.reply_text(msg)

# -------- MAIN FUNCTION --------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_stock))
    app.add_handler(CommandHandler("remove", remove_stock))
    app.add_handler(CommandHandler("mylist", mylist))
    app.add_handler(CommandHandler("portfolio", portfolio_summary))
    app.add_handler(CommandHandler("news", news))

    print("🚀 Portfolio Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
