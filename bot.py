import logging
import os
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# 🔐 Telegram Bot Token
TOKEN = "8601899020:AAF6xdQ9Uc2vUqE2J3g_B_iynLoVa83bfGQ"

logging.basicConfig(level=logging.INFO)

# ✅ Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Stock News Bot is running on cloud!")

# 📰 News Command
async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api_key = os.getenv("c5fb0e2299814a2aa8b79cbf26cbab74")

    if not api_key:
        await update.message.reply_text("❌ NEWS_API_KEY not found in environment variables.")
        return

    url = "https://newsapi.org/v2/everything"

    params = {
        "q": "Indian stock market OR NIFTY OR SENSEX",
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 5,
        "apiKey": api_key
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        if data.get("status") != "ok":
            await update.message.reply_text(f"⚠ API Error:\n{data}")
            return

        articles = data.get("articles", [])

        if not articles:
            await update.message.reply_text("⚠ No news found. Try again later.")
            return

        message = "📰 Latest Indian Stock Market News:\n\n"

        for article in articles[:5]:
            title = article.get("title", "No Title")
            link = article.get("url", "")
            message += f"🔹 {title}\n{link}\n\n"

        await update.message.reply_text(message)

    except Exception as e:
        await update.message.reply_text(f"Error occurred:\n{str(e)}")

# 💬 Echo (optional)
async def reply_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await update.message.reply_text(f"You said: {user_text}")

# 🚀 Main App
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("news", news))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_message))

    print("Bot Running on Cloud...")
    app.run_polling()

if __name__ == "__main__":
    main()
