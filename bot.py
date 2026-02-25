import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# =========================
# ENV VARIABLES (Render)
# =========================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN not found in environment variables!")

# =========================
# COMMAND: /start
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 Hello! Your AI Investment Bot is live.\n\n"
        "Use:\n"
        "/news - Get latest stock news\n"
        "/portfolio - Sample portfolio suggestion"
    )

# =========================
# COMMAND: /news
# =========================
async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not NEWS_API_KEY:
        await update.message.reply_text("News API key not configured.")
        return

    url = f"https://newsapi.org/v2/top-headlines?category=business&country=in&apiKey={NEWS_API_KEY}"
    
    try:
        response = requests.get(url)
        data = response.json()

        articles = data.get("articles", [])[:5]

        if not articles:
            await update.message.reply_text("No news found.")
            return

        message = "📰 Top Business News:\n\n"
        for article in articles:
            message += f"• {article['title']}\n{article['url']}\n\n"

        await update.message.reply_text(message)

    except Exception as e:
        await update.message.reply_text(f"Error fetching news: {str(e)}")

# =========================
# COMMAND: /portfolio
# =========================
async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        "📊 Sample Growth Portfolio (Long Term 10-15 yrs)\n\n"
        "40% – Nifty 50 Index Fund\n"
        "20% – Banking Sector Fund\n"
        "20% – IT Sector Fund\n"
        "10% – Defence Stock Basket\n"
        "10% – Gold ETF\n\n"
        "⚠️ For educational purposes only."
    )
    await update.message.reply_text(message)

# =========================
# MAIN
# =========================
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("news", news))
    app.add_handler(CommandHandler("portfolio", portfolio))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# =========================
# ENV VARIABLES (Render)
# =========================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN not found in environment variables!")

# =========================
# COMMAND: /start
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 Hello! Your AI Investment Bot is live.\n\n"
        "Use:\n"
        "/news - Get latest stock news\n"
        "/portfolio - Sample portfolio suggestion"
    )

# =========================
# COMMAND: /news
# =========================
async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not NEWS_API_KEY:
        await update.message.reply_text("News API key not configured.")
        return

    url = f"https://newsapi.org/v2/top-headlines?category=business&country=in&apiKey={NEWS_API_KEY}"
    
    try:
        response = requests.get(url)
        data = response.json()

        articles = data.get("articles", [])[:5]

        if not articles:
            await update.message.reply_text("No news found.")
            return

        message = "📰 Top Business News:\n\n"
        for article in articles:
            message += f"• {article['title']}\n{article['url']}\n\n"

        await update.message.reply_text(message)

    except Exception as e:
        await update.message.reply_text(f"Error fetching news: {str(e)}")

# =========================
# COMMAND: /portfolio
# =========================
async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        "📊 Sample Growth Portfolio (Long Term 10-15 yrs)\n\n"
        "40% – Nifty 50 Index Fund\n"
        "20% – Banking Sector Fund\n"
        "20% – IT Sector Fund\n"
        "10% – Defence Stock Basket\n"
        "10% – Gold ETF\n\n"
        "⚠️ For educational purposes only."
    )
    await update.message.reply_text(message)

# =========================
# MAIN
# =========================
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("news", news))
    app.add_handler(CommandHandler("portfolio", portfolio))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
